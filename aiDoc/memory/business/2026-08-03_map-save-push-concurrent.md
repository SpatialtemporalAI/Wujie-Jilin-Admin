# 保存地图 gRPC 推送由串行改为有界并发

## 需求描述

`NotifyMapSaved`（保存地图触发）原本按 `("middleware","agent")` × 机器人**串行**逐个下发（嵌套 for + 每个 await RPC），机器人一多总耗时 ≈ (N+M) × 单次 RPC（30s 封顶），设备收到地图延迟大。要求改成并发。

## 状态

已完成

## 方案

`SceneMapNavImageService._notify_map_saved`（modules/scene/services/scene_map_nav_image_service.py）：

- **关键约束**：`AsyncSession` 不可跨任务并发共享（底层一条连接，并发 await 会抛 `InvalidRequestError`/状态错乱）。**不能**直接把原循环体塞进 `asyncio.gather`。
- 抽出 `_push_map_to_one(map_info, map_id, version, target, robot_id, addr)`：每个机器人各自 `async with async_db_manager.get_session_cr() as push_db` 开独立 session，做 cancel_superseded → 在线判断 →（离线）save_pending →（在线）RPC；RPC 不碰 db 放 session 外，失败再开新 session save_pending。整体 try/except，单机失败仅日志不抛。
- `_notify_map_saved` 先收集 `push_list = [(target, robot_id, addr), ...]`，再用 `asyncio.Semaphore(_MAX_CONCURRENT_MAP_PUSH=16)` 限流 + `asyncio.gather` 并发调用 `_push_map_to_one`。
- 删除 `_notify_map_saved` 内因重构而不再使用的局部 import（`MapServiceClient`/`GrpcRetryService`，已下沉到 `_push_map_to_one`）。
- `map_info`（proto）只读共享安全；`MapServiceClient.notify_map_saved_one` stub 按 addr 缓存、纯 RPC，并发安全。

## 收益与边界

- 耗时从 ⌈(N+M)⌉ × RPC 降到 ⌈(N+M)/16⌉ 批。
- 地图保存本就是后台 `asyncio.create_task`（即发即忘），HTTP 早已返回；并发只影响设备收到地图的延迟，不影响保存接口响应。
- 仍是「广播给全部启用 middleware/agent 的机器人」（未按 map_id 过滤），且同一机器人若同时配 middleware+agent 仍会收到两次（发往两个不同服务地址，设计内）。

## 涉及范围

### 后端

- 改 `backend/modules/scene/services/scene_map_nav_image_service.py`：
  - 新增模块常量 `_MAX_CONCURRENT_MAP_PUSH = 16`
  - `_notify_map_saved` 推送段改为 gather 并发
  - 新增 `_push_map_to_one` 静态方法

### 前端

无改动。

## 相关文件

- `backend/modules/scene/services/scene_map_nav_image_service.py`
- `backend/modules/grpc/client.py`（`notify_map_saved_one`，并发安全，参考）
- `backend/modules/grpc/addr_provider.py`（`find_addrs_by_target`，广播地址来源，参考）

## 记录日期

2026-08-03
