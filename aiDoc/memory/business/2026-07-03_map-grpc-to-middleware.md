# 地图同步 gRPC 改走机器人 middleware 地址

## 需求描述

「点击地图同步」（地图编辑器保存触发 `NotifyMapSaved`）和「切换地图绑定」（改 robot.map_id 触发 `SwitchMap`）原本都发往全局 `settings.GRPC.MAP_SERVICE_ADDR` 单通道，与每台机器人在 `robot.grpc_config.middleware` 配置的地址脱节。导览/middleware 服务按机器人分布时，地图变更无法触达正确的机器人。

需求：把这两条 gRPC 改为按 `robot.grpc_config.middleware` 地址下发，复用 ConfigService 既有的「按地址解析 + 按 addr 缓存 channel」机制。行走速度 / 语音 / 电量等参数配置 gRPC 本次**不动**（速度已是 middleware，语音 TTS/测试与电量保持 agent）。

## 状态

已完成

## 路由规则（改动后）

| RPC | 触发场景 | 改动前 | 改动后 |
|---|---|---|---|
| `MapServiceClient.notify_map_saved` | 地图编辑器保存 | 全局 `MAP_SERVICE_ADDR` 单通道 | 按 `Robot.map_id == 地图` 反查绑定机器人，**广播**到各自 middleware 地址 |
| `MapServiceClient.switch_map` | 改 robot.map_id 绑定 | 全局 `MAP_SERVICE_ADDR` 单通道 | 按 robot_id 取其 middleware 地址**单发** |
| `MapServiceClient.search_maps` | 定时版本同步任务 | 全局 `MAP_SERVICE_ADDR` | **不变**（无 robot 上下文） |

参数配置类（voice/speed/battery/face）target 对照**未变**，见 [[2026-06-25_param-config-grpc-from-robot]] + [[2026-06-30_param-config-grpc-target-tweak]]。

## 涉及范围

### 后端

- `backend/modules/grpc/addr_provider.py`
  - `RobotConfigAddrProvider` 新增 `find_addrs_by_target_and_map(target, map_id)`：镜像 `find_addrs_by_target`，加 `Robot.map_id == map_id` 过滤，返回 `[(robot_id, host:port), ...]`
- `backend/modules/grpc/client.py`（`MapServiceClient`）
  - 新增 `_stubs_by_addr: dict[addr, MapServiceStub]` + `_get_stub_for_addr(addr)`，复用 `get_config_channel_by_addr`（与 ConfigService 共享 channel 池）
  - `notify_map_saved(map_info, targets)`：改为广播（参考 `FaceRecognitionClient.notify_changed`），任一成功即 `status="OK"`；无 target 返回 `SKIPPED`；全失败 `ERROR`
  - `switch_map(map_id, version, addr)`：新增 `addr` 入参，按该 addr 单发；addr 空返回 `DISABLED`
  - `search_maps` 不变，仍走全局单例 `_stub_()` / `get_channel()`
- `backend/modules/grpc/channel.py`
  - `close_channel()` 末尾追加 `MapServiceClient._stubs_by_addr.clear()`（channel 关闭后清失效 stub 引用）
  - `set_map_service_addr` 不动（只影响 search_maps 全局通道）
- `backend/modules/scene/services/scene_map_nav_image_service.py`
  - `_notify_map_saved`：构建 map_info 后调 `find_addrs_by_target_and_map("middleware", map_id)` 取 targets，再 `notify_map_saved(map_info, targets)`；日志含 targets 数量
- `backend/modules/robot/services/robot_service.py`
  - `update_map_binding` 调用处透传 `robot_id`：`_switch_map_via_grpc(map_id, version, robot_id)`
  - `_switch_map_via_grpc(map_id, version, robot_id)`：先 `get_addr(robot_id, "middleware")`，空则 `switch_map skipped` 记日志返回；否则 `switch_map(map_id, version, addr)`
- `backend/scripts/dump_notify_map_saved.py`
  - `send_via_grpc(payload, map_id, grpc_addr)`：按 map_id 解析 targets 广播；`--grpc-addr` 改为「手动指定单目标地址，跳过 DB 反查」（调试用），不再 `set_map_service_addr`

### 前端

- **无改动**：纯后端地址路由变更

## 关键决策

- **地图按 map_id 广播而非单 robot**：`SceneMap` 无 `robot_id`，但 `Robot.map_id → SceneMap.id`（多对一），故保存地图时反查所有绑定该地图的机器人逐个推送，任一成功即 OK
- **SwitchMap 走 robot_id 单发**：调用方 `update_map_binding` 已持有 robot_id，天然按该 robot 的 middleware 下发
- **复用 ConfigService channel 池**：同 addr 一个 TCP channel，MapService stub 与 voice/speed/battery stub 共享，不重复建连
- **SearchMaps 维持全局**：定时任务无 robot 上下文，`MAP_SERVICE_ADDR` 仍为其专属地址
- **不回退 settings**：与参数配置 gRPC 一致的强契约——机器人未配/未启用 middleware 就跳过并记日志

## 约束与备注

- 仅后端改动，未做 UI 测试
- `MAP_SERVICE_ADDR` 不再被 notify/switch 使用，仅 search_maps 在用，.env 配置保留
- 地图 proto 的 `SwitchMapRequest` 只含 id+version（无 robot_id 字段），路由完全在 channel/addr 层，**未改 proto**
- 关联 [[2026-06-25_param-config-grpc-from-robot]]（参数配置按 robot.grpc_config 取地址的原始路由表）、[[2026-06-18_notify-map-saved-image-url-internal-token]]（NotifyMapSaved 报文构造）

## 相关文件

后端：
- `backend/modules/grpc/addr_provider.py`
- `backend/modules/grpc/client.py`
- `backend/modules/grpc/channel.py`
- `backend/modules/scene/services/scene_map_nav_image_service.py`
- `backend/modules/robot/services/robot_service.py`
- `backend/scripts/dump_notify_map_saved.py`

## 记录日期

2026-07-03
