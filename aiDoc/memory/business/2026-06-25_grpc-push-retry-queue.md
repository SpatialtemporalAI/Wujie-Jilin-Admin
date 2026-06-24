# gRPC 推送失败持久化重试队列 + 前端"绿色 success + 备注"

**日期**: 2026-06-25
**提出者**: 用户

## 需求描述

上一阶段（2026-06-24）搭好了 gRPC client 骨架，但失败处理是「静默吞掉」——后端记 WARNING 日志，前端看到普通"保存成功"，设备掉线时配置永远无法同步过去。

本次升级为「DB 优先 + 失败持久化 + 自动重试 + 前端备注」：

1. **DB 更新优先**：当前已是「先 commit 再推送」，继续保持
2. **gRPC 失败入重试表**：失败时把任务（service/method/payload）持久化到新表 `grpc_retry_task`
3. **调度任务自动重试**：每分钟扫描到期任务，调用对应 gRPC，成功则置 completed，仍失败则按指数退避延后
4. **前端"绿色 success + 备注"**：后端返回 `code=0 + data.grpc_status + msg`，前端统一用 `message.success`，文案根据 `grpc_status` 区分

## 状态

已完成

## 用户决策

| 决策点 | 选择 |
|---|---|
| 提示方式 | 绿色 success + 备注文案（不用黄色 warning） |
| 重试策略 | 指数退避 60s/120s/240s + 最多 3 次，超过标记 dead |
| 测试按钮 | 失败直接 fail，**不入重试队列**（实时语义） |
| 扫描频率 | 每分钟（cron `* * * * *`，与现有 task-schedule-scan 一致） |

## 涉及范围

### 后端新建（5 个）

- `backend/database/models/business/grpc_retry_task.py` — ORM 模型，继承 `Base`
  - 字段：service_name / method_name / payload(JSON) / robot_id / status(pending/completed/dead) / retry_count / max_retries(默认3) / next_retry_at / last_error / completed_at
  - 复合索引 `(status, next_retry_at)` 用于扫描
- `backend/database/alembic/versions/0029_grpc_retry_task_table.py` — Alembic 迁移
- `backend/modules/grpc/retry_service.py` — `GrpcRetryService`
  - `save_pending(db, service_name, method_name, payload, robot_id, ...)` — 业务层失败时调用
  - `run_pending_once(db, limit=50)` — 扫描到期任务并重试，返回 stats
  - `_retry_one` / `_advance_fields` — 单任务重试 + 推进 retry_count 或置 dead
  - `_ROUTING` 字典：把 `(service_name, method_name)` 映射到 `config_client.py` 的对应 Client 方法（必要的"动态调度"层）
- `backend/modules/grpc/tasks/__init__.py` — 空包触发
- `backend/modules/grpc/tasks/retry_failed_pushes.py` — `@scheduled_task` 调度任务（cron `* * * * *`）

### 后端修改（4 个）

- `backend/main.py` — 加一行 `import modules.grpc.tasks.retry_failed_pushes  # noqa: F401`
- `backend/modules/robot/services/robot_config_service.py` — 5 个保存方法改造
  - 新增 `_push_with_retry(db, rpc_call, service_name, method_name, payload, robot_id)` 通用入口
  - 新增 `_aggregate_status(statuses)` 聚合多次 RPC 状态
  - 5 个保存方法（save_voice_config / create_face / update_face / delete_face / update_speed_level / update_battery_threshold）返回 `(orm_obj, grpc_status)`
- `backend/modules/robot/endpoints/robot_config.py` — 5 个保存 endpoint 改造
  - 读取 grpc_status，按 `_GRPC_MSG_MAP` 拼接 msg
  - speed/battery/delete_face 响应改为 `ResponseModel[ConfigUpdateResponse]`
  - test_wake_word / test_tts 失败时直接 `response_base.fail`，**不入队**
- `backend/modules/robot/schemas/robot_config.py`
  - `RobotVoiceConfigResponse` / `RobotFaceRecognitionResponse` 加 `grpc_status: Optional[str]`
  - 新增 `ConfigUpdateResponse`（speed/battery/delete 通用响应）

### 前端修改（6 个）

- `frontend/src/typings/api/robot-config.d.ts`
  - 新增 `GrpcStatus` 类型（'synced' | 'pending_retry' | 'disabled'）
  - `VoiceConfig` / `FaceRecognition` 加 `grpc_status?: GrpcStatus`
  - 新增 `ConfigUpdateResponse` 接口
- `frontend/src/service/api/robot-config.ts` — speed/battery fetch 函数返回类型改为 `ConfigUpdateResponse`
- `frontend/src/views/settings/modules/voice-synthesis-tab.vue` — `handleSaveVoice` 读取 `data.grpc_status`，pending_retry 时显示「保存成功（设备同步待重试）」
- `frontend/src/views/settings/modules/face-recognition-tab.vue` — `handleSave`（增/改）+ `handleDelete` 三处入口同样改造
- `frontend/src/views/settings/modules/walking-speed-tab.vue` — `handleSave` 同样改造
- `frontend/src/views/settings/modules/battery-threshold-tab.vue` — `handleSave` 同样改造

## 关键设计决策

### 1. payload 用 JSON 存储而非引用 DB 记录
DB 记录可能被后续修改，重试时拿到的会是新值而非当时的快照。JSON 存当时的请求 payload，语义清晰，符合「任务执行快照独立」的偏好（参考 [feedback-dual-table-migration](../../../C:/Users/drenc/.claude/projects/d--project-SpatialtemporalAi-Wujie-Jilin-Admin/memory/feedback-dual-table-migration.md)）。

### 2. 测试按钮不入队的理由
voice 的 TestWakeWord / TestTTSConfig 是「实时测试」语义——用户点击后等机器人的即时响应。如果失败入队后重试成功，机器人过几分钟突然发声反而会惊吓用户。所以失败直接 fail，让用户知道「现在测试不了」。

### 3. 指数退避只 3 次
60s/120s/240s 共 3 次，覆盖大约 7 分钟窗口。如果设备 7 分钟还没上线，大概率长时间离线，标记 dead 留给运维处理（避免无限堆积）。dead 状态记录保留在表中，后续可加查询页面。

### 4. 响应契约不变（code=0）
保持 `code === "0"` 为成功语义，前端无需改 axios 拦截器。`grpc_status` 仅作为附加信息，前端用它选文案。

### 5. 复用现有调度框架
不引入 Celery/RQ 等新依赖。完全用项目已有的 `@scheduled_task` + APScheduler，注册流程、并发策略、sys_scheduled_task 表都已有支撑。

### 6. _ROUTING 字典实现"动态调度"
`payload` 是 JSON，运行时取出后按方法签名展开为 kwargs 传给 client。`(service_name, method_name)` → `(client_method_ref, required_payload_keys)` 的映射，复用 `config_client.py` 的 4 个业务 Client（每个方法已带异常吞掉逻辑）。

## 相关文件

- backend/database/models/business/grpc_retry_task.py
- backend/database/alembic/versions/0029_grpc_retry_task_table.py
- backend/modules/grpc/retry_service.py
- backend/modules/grpc/tasks/retry_failed_pushes.py
- backend/main.py
- backend/modules/robot/services/robot_config_service.py
- backend/modules/robot/endpoints/robot_config.py
- backend/modules/robot/schemas/robot_config.py
- frontend/src/typings/api/robot-config.d.ts
- frontend/src/service/api/robot-config.ts
- frontend/src/views/settings/modules/{voice-synthesis,face-recognition,walking-speed,battery-threshold}-tab.vue

## 验证方案

### 档 1：GRPC_ENABLED=false
- 点全部 5 类保存按钮 → DB 正常写入，前端绿色 success「保存成功」，`grpc_retry_task` 表无新增

### 档 2：GRPC_ENABLED=true（无服务端）
- 点全部 5 类保存按钮 → DB 正常写入，前端绿色 success「保存成功（设备同步待重试）」
- `grpc_retry_task` 表新增记录（status=pending, next_retry_at=now()+60s）
- 1 分钟后调度任务触发，重试失败 → retry_count=1, next_retry_at=now()+120s
- 3 次重试后 → status=dead
- `sys_scheduled_task` 表存在 `task_key=grpc.retry_failed_pushes` 记录

### 档 3：测试按钮
- voice 测试唤醒词 / 测试 TTS 失败时 → 前端 message.error（红色失败），`grpc_retry_task` 表无新增

### 前端验证
- `pnpm typecheck` 通过

### 后端验证
- `python -c "from modules.grpc.retry_service import GrpcRetryService; from modules.grpc.tasks.retry_failed_pushes import retry_failed_pushes"` 导入检查
- 启动 FastAPI，确认调度任务注册到 `sys_scheduled_task` 表

## 记录日期

2026-06-25
