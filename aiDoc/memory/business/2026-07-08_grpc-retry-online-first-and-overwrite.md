# GRPC 同步：定时重试在线前置 + 同类消息覆盖

**日期**: 2026-07-08
**提出者**: 用户

## 需求描述

优化机器人 GRPC 配置同步的重试与覆盖语义（不改 openapi 接口）：

1. **定时重试改为在线前置**：定时任务到期重试前先检测机器人在线，在线才推送；离线则延后重扫、不消耗退避次数、不标 dead，等上线后再推。此前离线机器人会被无谓重试 3 次后判 dead，导致短暂掉线即永不下发。
2. **同机器人同类消息覆盖**（旧 GRPC 无需再推，含新推送成功也要取消旧 pending）：
   - 语音合成 / 行走速度 / 电量报警：覆盖键 = `(method, robot_id)`
   - 保存地图：覆盖键 = `(method, robot_id, map_id)`
   - 切换地图：覆盖键 = `(method, robot_id)`
3. **保存地图 / 切换地图纳入重试队列**：此前为 fire-and-forget（失败仅记日志），不进队列也无覆盖；现离线/失败入 `grpc_retry_task`，在线后定时重推。

## 状态

已完成

## 涉及范围

### 后端

- **新增 `modules/grpc/result.py`**：`RetryCallResult(success, message, cancel)`。统一重试路由返回契约（config client proto 有 `.success`、map 响应只有 `.status`，需抹平）。`cancel=True` 表示终态（地图/机器人已删）→ 任务置 cancelled。
- **`database/models/business/grpc_retry_task.py`**：新增可空列 `map_id`（仅 map 类推送用于覆盖去重）。
- **迁移 `database/alembic/versions/0042_grpc_retry_task_map_id.py`**：加法式 `op.add_column`，`down_revision = 0041_seed_open_merchant_menu`，零回填。
- **`modules/grpc/retry_service.py`**（核心改造）：
  - 取消旧任务由 `save_pending` 内部**上移到推送入口**：新增公开 `cancel_superseded(db, *, service_name, method_name, robot_id, map_id=None)`（自带 commit），无论本次推送成败都先取消同键旧 pending —— 修复「新成功后旧值被定时任务补推」的回退 bug。
  - `save_pending(..., map_id=None)` 写入新列，不再内部取消。
  - `_superseded_clause` 改为显式 `robot_id`/`map_id` 参数，NULL-safe：`map_id` 为空只覆盖 `map_id IS NULL`，非空只覆盖同 `map_id`（不同地图互不覆盖）。
  - 新增公开 `is_robot_online(db, robot_id)`（在线判定唯一真源，复用 `Robot.status == ONLINE`）与私有 `_robot_active`（未软删判定）。
  - `_retry_one` 顺序：路由/payload 校验 → 机器人软删判 `cancelled` → 离线延后 60s 返回 `waiting_online`（不推进 retry_count）→ 推送；`resp.cancel`→`cancelled`、`resp.success`→`completed`、否则退避。
  - `_ROUTING` 新增 `("map","NotifyMapSaved")` / `("map","SwitchMap")` → `MapRetryHelper`；voice/speed/battery 用薄 adapter 包成 `RetryCallResult`。
  - `_ONLINE_WAIT_SECONDS = 60`；`run_pending_once` stats 增 `waiting_online` / `cancelled`。
- **`modules/grpc/map_retry_helper.py`**（新增）：`MapRetryHelper.notify_map_saved` / `switch_map`。重试时按 `map_id` 重新查库重建 map_info（不存全量快照，规避 HMAC 签名 image_url 过期），下发到 robot 的 middleware+agent；地图已删 → `cancel=True`。
- **`modules/grpc/client.py`**：抽 `MapServiceClient.notify_map_saved_one(map_info, robot_id, addr)`（单机器人单地址，吞异常返回 status）；广播 `notify_map_saved` 改为循环委托它（聚合语义不变）。
- **`modules/robot/services/robot_config_service.py`**：`_push_with_retry` 顺序改为 GRPC.ENABLED 短路 → `cancel_superseded` → `is_robot_online`（离线直接入队）→ 推送。
- **`modules/scene/services/scene_map_nav_image_service.py`**：`_notify_map_saved` 改为 per-(target, robot) 循环，每个目标机器人 cancel → 在线判断 → `notify_map_saved_one` / 入队。保留「广播给所有启用该 target 的机器人」语义（不用 `find_addrs_by_target_and_map`）。
- **`modules/robot/services/robot_service.py`**：`_switch_map_via_grpc(map_id, version, robot_id, db)` 加 db 参数；cancel → 在线判断 → 两 target 下发，任一失败入队；整体吞异常 fire-and-forget。`update_map_binding` 调用点传 db。
- **`modules/grpc/tasks/retry_failed_pushes.py`**：日志格式增 `waiting_online` / `cancelled`。

### 前端

- 零改动。响应 `grpc_status` 取值 synced / pending_retry / disabled 不变。

## 关键决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 覆盖触发时机 | 推送入口调 RPC **之前**无条件 `cancel_superseded`（不再只在 `save_pending` 内） | 旧实现仅在新推送也失败时取消 → 新推送成功后旧 pending 仍被补推旧值，设备端数据回退 |
| 地图保存覆盖键 | `(method, robot_id, map_id)` | 同机器人不同地图互不覆盖（保存 M2 不应取消 M1 的 pending） |
| 地图重试行粒度 | 每机器人每地图一行（per-robot） | 唯一能正确支撑「按机器人在线门控重试」的模型；行数受 supersede 限制为 N_robot × N_map |
| 重试重建 map_info | 按 map_id 重新查库 | image_url 是带时效 HMAC 签名 URL，存全量快照会过期；同时自然推送最新版本 |
| 离线任务退避 | `next_retry_at += 60s`，retry_count 不变 | 离线是临时态，不应消耗退避导致误判 dead |
| schema 改动 | 单列 nullable 加法（`map_id`） | 非表结构重构，不属于「大改」，保留单表加列（用户偏好新建并存仅针对大改） |
| 统一返回契约 | `RetryCallResult` | map 响应只有 `.status`，与 config 的 `.success` 不一致；统一后 `_retry_one` 不必兼容两种形状 |
| 机器人/地图软删 | 任务置 `cancelled`（非 dead、非等待） | 终态，无意义再重试 |

## 范围外 / 影响

- 不改任何 openapi endpoint / 请求响应 schema / 前端。
- 保留 NotifyMapSaved「广播给所有启用 target 的机器人」（不收窄为只绑该地图的机器人），属既定行为。
- 并发同键保存的极少数重复 pending 行可接受（cancel+insert 非原子），下一次同键 cancel 会一并清扫，重试幂等。
- 广播全离线时会为每个机器人各入一队（受 supersede 限制为每地图每机器人一行）。

## 相关文件

- [backend/modules/grpc/retry_service.py](backend/modules/grpc/retry_service.py)
- [backend/modules/grpc/map_retry_helper.py](backend/modules/grpc/map_retry_helper.py)
- [backend/modules/grpc/result.py](backend/modules/grpc/result.py)
- [backend/modules/grpc/client.py](backend/modules/grpc/client.py)
- [backend/modules/robot/services/robot_config_service.py](backend/modules/robot/services/robot_config_service.py)
- [backend/modules/scene/services/scene_map_nav_image_service.py](backend/modules/scene/services/scene_map_nav_image_service.py)
- [backend/modules/robot/services/robot_service.py](backend/modules/robot/services/robot_service.py)
- [backend/database/alembic/versions/0042_grpc_retry_task_map_id.py](backend/database/alembic/versions/0042_grpc_retry_task_map_id.py)

## 相关历史记忆

- [2026-06-25 gRPC 推送失败重试队列](./2026-06-25_grpc-push-retry-queue.md)（本次在其基础上：在线前置 + 覆盖上移 + 地图纳入）
- [2026-07-08 实时下发接口增加在线前置校验](./2026-07-08_robot-online-check-before-dispatch.md)（同为「在线判定」主题，那个是同步 409 拦截测试/启动，本个是异步重试在线门控，共用 `Robot.status == ONLINE`）
- [2026-07-07 保存地图推送给全部机器人](./2026-07-07_map-save-push-all-robots.md)（本次保留其广播语义，在其上加 per-robot 重试）
- [2026-06-26 gRPC 重试 retry_count 不推进修复](./2026-06-26_grpc-retry-count-not-advancing.md)
