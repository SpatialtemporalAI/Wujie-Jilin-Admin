# 移除参数配置·会议指令配置（含 gRPC 与数据库字段）

## 需求描述

下线参数配置的会议指令配置：前端指令输入卡片、`NotifyMeetingModeChanged` gRPC 推送链路、`robot_voice_config` 的两个指令列全部移除。

**保留** `robot.meeting_mode` 状态字段与机器人列表「监听中/未开启」tag（用户明确：机器人侧仍可能以预设指令进入会议模式，状态展示不下线）。

## 状态

已完成

## 涉及范围

### 后端

- DB 子模块：`robot_voice_config` 删 `meeting_enter_command` / `meeting_exit_command` 列与 DEFAULT 常量（迁移 0017，down_revision=0016）；`robot.meeting_mode` 保留
- proto 子模块：`voice.proto` 删 `NotifyMeetingModeChanged` RPC 与消息，重新生成
- 主仓：`RobotVoiceConfigSchema`/`Response` 删指令字段与校验；`save_voice_config` 移除 meeting 变更检测与推送；`VoiceConfigClient.notify_meeting_mode`、retry 路由条目删除

### 前端

- `voice-synthesis-tab.vue`：删「会议模式」卡片、`canSaveMeeting` 校验、model 指令字段
- `robot-config.d.ts`：`VoiceConfig` 删指令字段
- `robots/index.vue` 状态 tag、`robot.d.ts` 的 `meeting_mode`：保留不动

## 约束与备注

- 历史迁移 0014/0016 不改动，删列走新增迁移 0017
- agent 端若已部署 `NotifyMeetingModeChanged` 实现，移除后不再被调用，属无害残留
- 语音配置保存链路恢复为 wake/tts/greeting 三类推送

## 相关文件

- `backend/database/models/business/robot_voice_config.py`、`backend/database/alembic/versions/0017_drop_meeting_commands_from_voice_config.py`
- `backend/grpc/protos/config/voice.proto`（+ 生成物）
- `backend/modules/robot/{schemas/robot_config.py,services/robot_config_service.py}`、`backend/modules/grpc/{config_client.py,retry_service.py}`
- `frontend/src/views/settings/modules/voice-synthesis-tab.vue`、`frontend/src/typings/api/robot-config.d.ts`
- `aiDoc/frontend-backend/boundary.md`（参数配置 · 会议模式状态契约）

## 记录日期

2026-10-16
