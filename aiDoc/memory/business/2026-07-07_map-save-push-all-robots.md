# 保存地图时默认推送所有机器人（不再按 map_id 过滤）

## 需求描述

保存地图（`NotifyMapSaved`）此前按 `Robot.map_id == map_id` 反查**绑定该地图**的机器人再广播（见 [[2026-07-07_map-grpc-agent-push]]、[[2026-07-03_map-grpc-to-middleware]]）。业务上希望任何地图被保存后，**所有**已启用对应 target 的机器人都能收到最新 MapInfo（刷新本地地图缓存），不再要求机器人先绑定该地图。

需求：保存地图时**去掉 `Robot.map_id` 过滤**，对 middleware / agent 两个 target 各自广播给**全部**启用该 target 的机器人；切换地图（`SwitchMap`）仍按 robot_id 单发，不在本次改动范围。

## 状态

已完成

## 核心决策

- **仅改保存地图（广播）路径，不改切换地图（单发）路径**：`SwitchMap` 本就是「切到某 robot 的当前地图」，天然按 robot_id 单发，与「推送给所有机器人」语义无关，保持不动。
- **`addr_provider.py` 已存在 `find_addrs_by_target(target)`**：返回所有启用该 target 的机器人地址（无 map_id 过滤），正好满足「推全部」语义，直接复用，零新增方法。
- **`find_addrs_by_target_and_map(target, map_id)` 方法保留**：仍是通用工具，仅本次业务路径不再调用它（调试脚本 `scripts/dump_notify_map_saved.py` 仍按 map 反查，保持不变，因为它是针对指定 map 的手动调试工具）。
- **`MapServiceClient` / proto / 前端零改动**：纯调用方把 `find_addrs_by_target_and_map` 换成 `find_addrs_by_target`，广播语义、双推结构、独立 try/except 全部沿用 [[2026-07-07_map-grpc-agent-push]] 的实现。

## 涉及范围

### 后端

- `backend/modules/scene/services/scene_map_nav_image_service.py`（`_notify_map_saved`）
  - `find_addrs_by_target_and_map(target, fresh.id)` → `find_addrs_by_target(target)`；map_info 构造一次、middleware/agent 双推、独立 try/except 结构不变；docstring 与行内注释同步更新为「遍历所有启用对应 target 的机器人（不再判断 robot 是否绑定该地图）」。

### 前端

- 无改动（纯后端地址路由调整）。

## 约束与备注

- 仅后端改动，未做界面测试（参考长期偏好：前端变更才需 typecheck）。
- 语义变化：保存任一地图会向**全部**已启用 middleware/agent 的机器人下发该地图的 MapInfo；未启用对应 target 的机器人仍被跳过（沿用「未配即跳过+记日志」强契约）。
- 广播内部仍按每端「任一成功即 OK / 无 target 返回 SKIPPED」，middleware 与 agent 两端结果互不混合。
- 切换地图（`SwitchMap`，`robot_service._switch_map_via_grpc`）保持按 robot_id + target 单发，不受本次改动影响。

## 相关文件

后端：
- `backend/modules/scene/services/scene_map_nav_image_service.py`（改动）

复用未改：
- `backend/modules/grpc/addr_provider.py`（`find_addrs_by_target`）
- `backend/modules/grpc/client.py`（`MapServiceClient.notify_map_saved`）
- `backend/modules/robot/services/robot_service.py`（`_switch_map_via_grpc`，未动）
- `backend/scripts/dump_notify_map_saved.py`（手动调试脚本，仍按 map 反查，未动）

## 相关历史记忆

- [[2026-07-07_map-grpc-agent-push]]（middleware + agent 双推的原始实现，本需求在其基础上放宽广播范围）
- [[2026-07-03_map-grpc-to-middleware]]（地图 gRPC 改走 robot.middleware / 按 map_id 反查的原始路由表）
- [[2026-06-18_notify-map-saved-image-url-internal-token]]（NotifyMapSaved 报文构造）

## 记录日期

2026-07-07
