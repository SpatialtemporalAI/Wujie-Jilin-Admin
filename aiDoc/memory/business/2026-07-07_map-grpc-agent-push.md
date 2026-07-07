# 地图保存/切换 gRPC 增加 agent 端推送（middleware + agent 双推）

## 需求描述

保存地图（`NotifyMapSaved`）和切换地图（`SwitchMap`）此前只下发到 `robot.grpc_config.middleware`（见 [[2026-07-03_map-grpc-to-middleware]]）。agent 端同样需要感知地图保存/切换事件（刷新本地地图缓存、切换当前活动地图等），但当前对 agent 完全不可达。

需求：在现有 middleware 推送基础上，**额外**向 `robot.grpc_config.agent` 推送**同一个** `MapService.NotifyMapSaved` / `SwitchMap` RPC（双推，非替换）。两端各自独立判断启停/地址、独立记日志、互不影响；某端未配置/未启用则跳过该端（沿用「强契约：未配即跳过+记日志」，不回退、不阻塞业务）。**要求 agent 端部署实现 `MapService` 的服务。**

## 状态

已完成

## 核心决策

- **`MapServiceClient`（`backend/modules/grpc/client.py`）零改动**：它本就 target-agnostic——`notify_map_saved(map_info, targets)` 接 `[(robot_id, addr)]` 广播、`switch_map(map_id, version, addr)` 接单 addr 单发，与 target 无关；channel/stub 按 addr 缓存（`get_config_channel_by_addr`），middleware 与 agent 各自 addr 走各自 channel。
- **「向两个 target 各推一次」是业务路由决策，放在调用方**，不污染 client。这是项目内首个「同 RPC 双 target」先例（`config_client.py` 每个 RPC 只绑一个 target）。
- **`addr_provider.py` 零改动**：`find_addrs_by_target_and_map("agent", map_id)` 与 `get_addr(robot_id, "agent")` 已天然可用（target 只是 grpc_config 的 dict 子键，agent/middleware/ros 对称）。
- **重试层零改动**：`NotifyMapSaved`/`SwitchMap` 本就不进 `grpc_retry_task`（重试层只覆盖 voice/speed/battery，见 [[2026-06-25_grpc-push-retry-queue]]）。
- **无 proto 改动、无前端改动**：复用同一 `MapService` 三个 RPC，纯后端地址路由扩展。

## 涉及范围

### 后端

- `backend/modules/scene/services/scene_map_nav_image_service.py`（`_notify_map_saved`，广播）
  - 对 `("middleware", "agent")` 循环：每个 target 各 `find_addrs_by_target_and_map(target, map_id)` → `notify_map_saved(map_info, targets)` → 独立记日志（`target=` 字段区分）；`map_info` 只构造一次复用；每端独立 try/except，一端失败不影响另一端。docstring 同步更新。
- `backend/modules/robot/services/robot_service.py`（`_switch_map_via_grpc`，单发）
  - 对 `("middleware", "agent")` 循环：每个 target 各 `get_addr(robot_id, target)`，空则 skip+记日志 `continue`，非空则 `switch_map(map_id, version, addr)` + 沿用既有 `grpc.aio.AioRpcError` / `Exception` 两段 except，日志带 `target=`。调用方 `update_map_binding` 不变。docstring 同步更新。
- `backend/scripts/dump_notify_map_saved.py`（调试脚本 `send_via_grpc`）
  - DB 反查模式下合并 middleware + agent 两组 target，打印时按 `(robot_id, addr, target)` 标注来源；合并后调一次 `notify_map_saved`（调试取「任一成功即 OK」即可，无需像生产那样分两次）。`--grpc-addr` 手动模式不变；帮助文本同步。

### 前端

- 无改动（纯后端地址路由扩展）。

## 约束与备注

- 仅后端改动，未做界面测试（参考长期偏好：前端变更才需 typecheck）。
- agent 端必须部署实现 `MapService`（`NotifyMapSaved` + `SwitchMap` handler）的服务，否则推送会失败并记日志（不阻塞业务）。
- middleware 与 agent 各自的 `enabled`/`host`/`port` 独立判断；某端未配置则该端 `find_addrs_by_target_and_map` 返回空 / `get_addr` 返回 None，对应 skip 或 `SKIPPED` 响应。
- 广播语义（保存地图）：每端内部仍是「任一成功即 OK / 无 target 返回 SKIPPED」，两端结果互不混合。
- 单发语义（切换地图）：每端独立返回各自的 `SwitchMapResponse`，互不影响。

## 相关文件

后端：
- `backend/modules/scene/services/scene_map_nav_image_service.py`
- `backend/modules/robot/services/robot_service.py`
- `backend/scripts/dump_notify_map_saved.py`

复用未改：
- `backend/modules/grpc/client.py`（`MapServiceClient`）
- `backend/modules/grpc/addr_provider.py`（`find_addrs_by_target_and_map` / `get_addr`）

## 相关历史记忆

- [[2026-07-03_map-grpc-to-middleware]]（地图 gRPC 改走 robot.middleware 的原始路由表，本需求是其 agent 扩展）
- [[2026-06-30_map-switch-rpc]]（SwitchMap proto 方法契约）
- [[2026-06-18_notify-map-saved-image-url-internal-token]]（NotifyMapSaved 报文构造）

## 记录日期

2026-07-07
