# 会议指令配置接入 gRPC 推送 + 会议模式状态迁移到 robot 表

## 需求描述

1. 参数配置的会议指令（`meeting_enter_command` / `meeting_exit_command`）保存后，与其他语音配置一样向机器人 **agent** 端推送 gRPC；不下发 `meeting_mode_enabled`
2. 删除 `robot_voice_config.meeting_mode_enabled` 字段；改在 **robot 表新增布尔字段 `meeting_mode`** 记录机器人是否进入会议模式（机器人侧上报，系统侧不控制开关）

## 状态

指令配置部分已于 2026-10-16 下线（见 [2026-10-16 移除会议指令配置](./2026-10-16_remove-meeting-command-config.md)）；robot.meeting_mode 状态字段保留

已完成（机器人 agent 端实现 `NotifyMeetingModeChanged`、`meeting_mode` 上报通道对接另行处理）

## 涉及范围

### 后端

- DB 子模块 `backend/database`：`robot` 表加 `meeting_mode` 布尔列；`robot_voice_config` 删 `meeting_mode_enabled` 列（迁移 0016，down_revision=0015）
- proto 子模块 `backend/grpc`：`voice.proto` 新增 `NotifyMeetingModeChanged`（仅 `robot_id` + 两条指令），`uv run python main.py` 重新生成（需 PYTHONUTF8=1 避免 GBK 控制台 emoji 报错）
- `VoiceConfigClient.notify_meeting_mode`：仅推 agent 端（仿 `notify_greeting_mode`）
- `save_voice_config`：`changed` 集合新增 `meeting`（新建全推；更新仅两条指令实际变化才推），落库后经 `_push_with_retry` 推送，payload 空值回退默认指令
- `retry_service._ROUTING` 注册 `("voice", "NotifyMeetingModeChanged")`
- Schema：`RobotVoiceConfigSchema`/`RobotVoiceConfigResponse` 删 `meeting_mode_enabled`；`RobotResponseData` 加 `meeting_mode`（仅出参）

### 前端

- `robot-config.d.ts` 语音配置类型删 `meeting_mode_enabled`；`robot.d.ts` Robot 类型加 `meeting_mode?: boolean`
- `voice-synthesis-tab.vue`：model 与保存逻辑移除 `meeting_mode_enabled`
- `robots/index.vue`：删除 `meetingModeMap` 逐台拉语音配置逻辑，tag 直接读 `robot.meeting_mode`

## 约束与备注

- 开关仍仅机器人端语音指令可变更，系统侧不提供开关；`robot.meeting_mode` 的置位依赖机器人侧上报通道（本期只落字段与展示）
- agent 未升级实现新 RPC 前返回 UNIMPLEMENTED → 入重试队列退避 3 次后 dead，不影响 DB 保存与接口返回（既有最终一致模型）
- 历史迁移 0014/0015 不改动；两个子模块需分别提交推送后更新父仓子模块指针

## 相关文件

- `backend/database/models/business/robot.py`、`backend/database/models/business/robot_voice_config.py`
- `backend/database/alembic/versions/0016_robot_meeting_mode_drop_voice_config_enabled.py`
- `backend/grpc/protos/config/voice.proto`（+ `generated/config/voice_pb2*.py`）
- `backend/modules/grpc/config_client.py`、`backend/modules/grpc/retry_service.py`
- `backend/modules/robot/services/robot_config_service.py`
- `backend/modules/robot/schemas/robot_config.py`、`backend/modules/robot/schemas/robot.py`
- `frontend/src/views/robots/index.vue`、`frontend/src/views/settings/modules/voice-synthesis-tab.vue`
- `frontend/src/typings/api/robot.d.ts`、`frontend/src/typings/api/robot-config.d.ts`
- `aiDoc/frontend-backend/boundary.md`（参数配置 · 会议模式契约）

## 记录日期

2026-10-15
