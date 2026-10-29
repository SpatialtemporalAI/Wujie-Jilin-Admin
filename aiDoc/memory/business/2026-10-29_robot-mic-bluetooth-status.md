# 机器人列表新增麦克风蓝牙状态与重连

## 需求描述

机器人列表卡片新增「麦克风蓝牙状态」行（样式对齐「服务器自启状态」行）：状态标签（已连接/未连接/未知）+ 重连按钮。用户确认：指机器人的麦克风蓝牙，由后端直连机器人对接。

## 技术方案

- 链路：后端 gRPC 直连机器人 **agent 端**（不走控制面板 HTTP，与 slot-status 不同）
- proto：`backend/grpc`（子模块）新增 `protos/config/mic_bluetooth.proto`，`MicBluetoothService` 两个 RPC：
  - `GetMicBluetoothStatus(robot_id)` → `{ connected, message }`
  - `ReconnectMicBluetooth(robot_id)` → `{ success, connected, message }`
- 客户端：`modules/grpc/config_client.py` 新增 `MicBluetoothClient`（stub 按 addr 缓存、超时、异常兜底）；与推送类 RPC 不同，查询/动作类**失败返回 None**（区分「机器人应答但未连接」与「机器人不可达」），不返回哨兵响应
- Service：`robot_mic_bluetooth_service.py`，状态文案 已连接/未连接/未知；重连不可达或失败抛 ServerError
- 端点（挂 `/robot/manage`）：
  - `GET /robot/manage/{id}/mic-bluetooth/status`（权限 `robot:manage:list`）→ `MicBluetoothStatusData{status}`
  - `POST /robot/manage/{id}/mic-bluetooth/reconnect`（权限 `robot:manage:restart`，复用重启权限点）→ 同上，返回重连后状态
- `MicBluetoothStatusData` 不能用 `BaseRespEntity`（其 status 序列化器会把 truthy 转 "1"），用纯 BaseModel

## 前端

- `views/robots/index.vue`：卡片在「服务器自启状态」行下新增「麦克风蓝牙状态」行（同一 `robot-card-slot` 样式，权限 `robot:manage:restart`）；列表加载后并行逐台拉取状态，单台失败置「未知」；重连后刷新该台状态；已连接 success 色、未连接 error 色、未知 default 色
- `service/api/robot.ts` + `typings/api/robot.d.ts`：`fetchGetRobotMicBluetoothStatus` / `fetchReconnectRobotMicBluetooth` / `MicBluetoothStatus(Data)`

## 约束与备注

- **agent 端需实现 `MicBluetoothService` 两个 RPC**（proto 见子模块 `backend/grpc` 提交 80e2e67）；未实现/机器人离线时状态显示「未知」，重连提示「机器人当前不可达」
- gRPC 地址解析沿用 `robot.grpc_config.agent`；`GRPC.ENABLED=false` 时一律返回「未知」
- 蓝牙状态为实时查询，不落库（与会议模式 meeting_mode 上报落库的模式不同）

## 相关文件

- 子模块 `backend/grpc`：`protos/config/mic_bluetooth.proto`、`generated/config/mic_bluetooth_pb2{,_grpc}.py`（提交 80e2e67）
- 后端：`modules/grpc/config_client.py`、`modules/robot/services/robot_mic_bluetooth_service.py`、`modules/robot/endpoints/robot.py`、`modules/robot/schemas/robot.py`
- 前端：`views/robots/index.vue`、`service/api/robot.ts`、`typings/api/robot.d.ts`

## 记录日期

2026-10-29
