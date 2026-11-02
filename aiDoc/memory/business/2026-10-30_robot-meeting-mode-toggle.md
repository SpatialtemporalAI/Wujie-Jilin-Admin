# 机器人卡片会议模式手动切换

## 需求描述

机器人列表卡片的「会议模式」由纯状态展示改为可手动控制开关，交互与「服务器自启状态」「麦克风蓝牙状态」两行一致（状态 tag + 操作按钮）。同时卡片信息区按设计稿重排版：分组之间用分隔线隔开；型号/地图为左对齐两列（label 灰、值主题蓝加粗），可操作行 label 居左、tag+按钮居右；所有 label 颜色统一。

## 技术方案

- 链路：后端 gRPC 直连机器人 **agent 端**，与麦克风蓝牙同一模式
- proto：`backend/grpc`（子模块）新增 `protos/config/meeting_mode.proto`，`MeetingModeService.SetMeetingMode(robot_id, enabled)` → `{ success, meeting_mode, message }`
- 客户端：`modules/grpc/config_client.py` 新增 `MeetingModeClient`（与 MicBluetoothClient 同约定：动作类失败返回 None）
- Service：`robot_meeting_mode_service.py`，切换成功后把最新状态落库 `robot.meeting_mode`（列表展示仍读库，无需逐台查询）；不可达/失败抛 ServerError
- 端点：`POST /robot/manage/{id}/meeting-mode`（权限 `robot:manage:restart`，复用重启权限点），请求体 `MeetingModeUpdate{enabled}` → `MeetingModeStatusData{meeting_mode}`（纯 BaseModel）

## 前端

- `views/robots/index.vue`：会议模式行改为 label 左 + tag（监听中/未开启）+ 开启/关闭按钮右（按钮需 `robot:manage:restart` 权限，带 loading，成功后就地更新 `robot.meeting_mode`）
- 卡片排版：header 下方、型号/地图组、会议模式、自启/蓝牙组之间用分隔线分组；型号/地图 label 固定 4em 宽度左对齐、值主题蓝加粗；所有 label 统一灰色；机器人名称改主题蓝色
- `service/api/robot.ts` + `typings/api/robot.d.ts`：`fetchSetRobotMeetingMode` / `MeetingModeUpdate` / `MeetingModeStatusData`

## 约束与备注

- **agent 端需实现 `MeetingModeService.SetMeetingMode` RPC**；未实现/机器人离线时切换提示「机器人当前不可达」，状态展示不受影响
- gRPC 地址解析沿用 `robot.grpc_config.agent`；`GRPC.ENABLED=false` 时切换一律提示不可达
- 与 2026-10-16 下线的「会议指令配置」不同：那次是移除语音指令配置链路，本次是新增平台侧手动开关

## 相关文件

- 子模块 `backend/grpc`：`protos/config/meeting_mode.proto`、`generated/config/meeting_mode_pb2{,_grpc}.py`
- 后端：`modules/grpc/config_client.py`、`modules/robot/services/robot_meeting_mode_service.py`、`modules/robot/endpoints/robot.py`、`modules/robot/schemas/robot.py`
- 前端：`views/robots/index.vue`、`service/api/robot.ts`、`typings/api/robot.d.ts`

## 记录日期

2026-10-30
