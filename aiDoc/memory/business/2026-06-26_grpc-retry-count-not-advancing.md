# gRPC 重试任务永远 pending（retry_count 不递增）

## 需求描述

任务管理用户反馈：gRPC 推送失败入队后，`grpc_retry_task` 表中的任务一直停留在
`pending`，`retry_count` 始终为 0。期望「grpc 不通抛异常也算 1 次」，让重试按
60/120/240s 指数退避正常推进，3 次失败后置 dead。

## 现象

- 入队后任务 status 一直是 pending
- retry_count 一直是 0
- next_retry_at 没有被推进

## 根因

两层超时叠加 + CancelledError 不被 except Exception 捕获：

1. 调度任务 `retry_failed_pushes` 默认 `timeout=300s`（registry.py TaskDefinition 默认），
   `_execute_task` 用 `asyncio.wait_for(func(), timeout=300)` 强制超时
2. `_dispatch_with_target`（config_client.py）把 gRPC 异常吞成 `success=False`
   响应，理论上 `_retry_one` 的 resp.success=False 路径会调 `_advance_fields`
   推进 retry_count
3. 但 pending 任务 ≥ 20 个时（20 × 单次 rpc timeout 10s = 200s 接近 300s），
   外层 `wait_for` 触发，把整个 `retry_failed_pushes` 取消
4. 取消时正在执行的 `await rpc(...)` 抛 `asyncio.CancelledError`，
   Python 3.8+ 起它是 `BaseException` 子类，不被 `except Exception` 捕获，
   冒泡出 `_dispatch_with_target` → `_retry_one` → `run_pending_once`
5. `_advance_fields` 根本没机会跑 → retry_count 永远 0

另一层隐患：grpc.aio 在某些场景（对端 IP 不可达 / TCP 层 drop SYN）
**不一定按 `timeout=10s` 抛 DEADLINE_EXCEEDED**，单次调用可能 hang 几十秒到
上百秒，进一步加剧外层 timeout 触发。

## 状态

已完成

## 涉及范围

### 后端

- `backend/modules/grpc/retry_service.py`
  - import 增加 `asyncio`
  - 模块常量 `_CALL_TIMEOUT_SECONDS: float = 15.0`（单次重试硬超时）
  - `_retry_one` 中 client 调用从 `await client_method(**kwargs)` 改为
    `await asyncio.wait_for(client_method(**kwargs), timeout=_CALL_TIMEOUT_SECONDS)`
  - 新增 `except asyncio.TimeoutError` 分支，与原 `except Exception`、
    `resp.success=False` 三种失败路径统一调 `_advance_fields` 推进 retry_count
  - 模块 docstring 补一段说明硬超时兜底

- `backend/modules/grpc/tasks/retry_failed_pushes.py`
  - `@scheduled_task` 显式加 `timeout=800`
  - 原默认 300s 在 pending 任务 ≥ 20 个时会被外层 `wait_for` 强制 cancel，
    导致内层 `_advance_fields` 没机会跑
  - 800s = 50 task × 15s 硬超时 + 50s DB/连接开销余量

## 关键决策

### 三种失败路径统一推进 retry_count

| 路径 | 触发条件 | 处理 |
|---|---|---|
| 硬超时 | `asyncio.TimeoutError`（15s 内 client 没返回） | _advance_fields |
| 调用异常 | `Exception`（极少，client 内部已吞，这里是双保险） | _advance_fields |
| 业务失败 | `resp.success=False`（client 吞异常后构造的哨兵响应） | _advance_fields |

三种路径都通过 `_advance_fields` 推进 retry_count，按 60/120/240s 指数退避
重新计算 next_retry_at，retry_count 达 max_retries=3 置 dead。

### 内层 15s 硬超时 + 外层 800s 任务超时

- 内层 15s：兜底 grpc.aio 不按 deadline 抛错的场景（对端 IP 不可达等）
- 外层 800s：保证 50 task × 15s = 750s 不会被强制 cancel
- 加 50s 余量覆盖 DB commit / 首次 channel 创建开销

### 不调整退避策略

按用户要求保持 60/120/240s 指数退避（共 3 次），只修复「算 1 次」的问题。
3 次失败后 dead，整体行为与设计一致。

### 不放宽 resp.success=False 路径

修复前 resp.success=False 已调 _advance_fields，逻辑正确；
本次只是补充前两个路径（硬超时、调用异常），保证健壮性。

## 验证方案

### 场景 1：grpc 不通（对端 IP 不可达）

- 配置一个 robot 的 grpc_config.middleware 指向不可达 IP（如 192.168.255.255:50051）
- 触发一次 voice 保存（业务层 _push_with_retry 入队）
- 期望：
  - 入队后 status=pending, retry_count=0, next_retry_at=now+60s
  - 60s 后调度扫描，15s 内必定 timeout，retry_count=1, next_retry_at=now+120s
  - 120s 后 retry_count=2, next_retry_at=now+240s
  - 240s 后 retry_count=3, status=dead

### 场景 2：grpc 端口拒绝（连接立即失败）

- 配置一个 robot 的 grpc_config.middleware 指向可达 IP 但未监听的端口
- client 内部 catch ECONNREFUSED 返回 success=False
- 期望：同场景 1，retry_count 正常推进

### 场景 3：大量 pending 任务

- 入队 50+ 个 pending 任务（同 robot 不同 method，或不同 robot）
- 期望：单次扫描 800s 内处理完所有到期任务，retry_count 各自推进
- 不再出现「外层 timeout 取消导致 retry_count 一直 0」

### 静态检查

- `python -m py_compile modules/grpc/retry_service.py modules/grpc/tasks/retry_failed_pushes.py` 通过

## 部署注意

- `@scheduled_task` 加 `timeout=800` 后，下次启动会通过
  `seed_scheduler` → `SchedulerService.sync_registry_to_db` 自动同步到
  `sys_scheduled_task` 表（`sync_registry_to_db` 强制覆盖 timeout 字段）
- 如已在 UI 手动调整过该任务 timeout，会被覆盖回 800

## 相关文件

后端：
- `backend/modules/grpc/retry_service.py`
- `backend/modules/grpc/tasks/retry_failed_pushes.py`

## 记录日期

2026-06-26
