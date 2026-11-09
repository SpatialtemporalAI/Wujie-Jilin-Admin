# 机器人麦克风蓝牙按钮放开为「连接/断开」并新增单连接二次确认

## 需求描述

1. 之前被隐藏（`f5f7646`）的麦克风蓝牙操作按钮重新放开，按状态显示「连接」（未连接）或「断开」（已连接）。
2. 麦克风同一时间最多只能连接一台机器人：连接其他机器人时，若已有机器人处于已连接状态，需二次确认并提示「会先断开已连接的机器人」。
3. 需要把后台实际调用的 agent 端方法与传参同步给 agent 同事。

## 技术方案

- proto（子模块 `backend/grpc`）：`protos/config/mic_bluetooth.proto` 新增 `DisconnectMicBluetooth`：
  - `DisconnectMicBluetooth(DisconnectMicBluetoothRequest{int64 robot_id})` → `DisconnectMicBluetoothResponse{bool success, bool connected, string message}`
  - 「连接」仍复用已有 `ReconnectMicBluetooth(robot_id)`（语义为断开当前连接后重新搜索/连接）
  - 重新生成 `generated/config/mic_bluetooth_pb2{,_grpc}.py`
- 客户端：`modules/grpc/config_client.py` 的 `MicBluetoothClient` 新增 `disconnect(robot_id)`（不可达返回 None）
- Service：`robot_mic_bluetooth_service.py` 新增 `disconnect(robot)`；不可达/失败抛 ServerError
- 端点：`POST /robot/manage/{id}/mic-bluetooth/disconnect`（权限 `robot:manage:restart`，`log_operation action=disconnect`）→ `MicBluetoothStatusData{status}`
- 单连接约束由 agent 端硬件/agent 逻辑保证（连接新机器人时自动断开旧机器人），后台只在连接前做前端二次确认

## 前端

- `views/robots/index.vue`：
  - 状态行按钮随 `micBtStatusMap[robot.id]` 切换：「未连接」显示「连接」（`icon-mdi-bluetooth-connect`，调 reconnect）；「已连接」显示「断开」（`icon-mdi-bluetooth-off`，NPopconfirm 二次确认，调 disconnect）
  - `handleConnectMicBt`：若列表中其他机器人已连接，`useDialog().warning` 二次确认（提示会先断开已连接的机器人），确认后再执行连接
  - `micBtReconnectingMap` 重命名为 `micBtActionMap`，连接/断开共用 loading
- `service/api/robot.ts` 新增 `fetchDisconnectRobotMicBluetooth(id)`；`typings` 复用 `MicBluetoothStatusData`
- `typings/components.d.ts` 增加 `IconMdiBluetoothOff`

## agent 端同步信息

- 查询状态：`MicBluetoothService/GetMicBluetoothStatus`，请求 `{ robot_id: int64 }`
- 连接：`MicBluetoothService/ReconnectMicBluetooth`，请求 `{ robot_id: int64 }`
- 断开：`MicBluetoothService/DisconnectMicBluetooth`，请求 `{ robot_id: int64 }`（**新增，需 agent 端实现**）
- 响应均含 `success`、`connected`、`message`（查询响应无 `success`）

## 约束与备注

- 断开后 `connected` 正常应为 `false`，前端按返回值刷新状态
- 状态仍为实时查询不落库；列表 10s 轮询聚合 `mic_bluetooth_status`
- 二次确认仅基于前端已加载的列表状态（最长可能有约 10s 延迟），最终单连接以 agent 端为准

## 相关文件

- 子模块 `backend/grpc`：`protos/config/mic_bluetooth.proto`、`generated/config/mic_bluetooth_pb2{,_grpc}.py`
- 后端：`modules/grpc/config_client.py`、`modules/robot/services/robot_mic_bluetooth_service.py`、`modules/robot/endpoints/robot.py`
- 前端：`views/robots/index.vue`、`service/api/robot.ts`、`typings/components.d.ts`

## 记录日期

2026-11-09
