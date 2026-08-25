# 机器人打招呼模式（greeting_mode）

## 需求描述

`robot_voice_config` 表增加 `greeting_mode` 字段（枚举：`wave` 招手模式 / `no_wave` 无招手模式），参数配置页新增「打招呼模式」tab（机器人下拉 + 动作模式单选 + 保存），保存后通过 gRPC 推送，**只发 agent 端**。

## 状态

已完成

## 涉及范围

### 后端

- 迁移 `0005_add_greeting_mode_to_robot_voice_config.py`：`greeting_mode` String(20) NOT NULL server_default `wave`
- 模型 `RobotVoiceConfig` 新增 `greeting_mode` 列 + `DEFAULT_GREETING_MODE = "wave"` 常量
- `GET /admin/robot/config/voice` 响应（`RobotVoiceConfigResponse`）新增 `greeting_mode` 字段
- 新增 `PUT /admin/robot/config/greeting-mode/{robot_id}`（权限 `robot:config:edit`），upsert 语义（无语音配置行则按默认值建行），返回 `ConfigUpdateResponse`
- gRPC：`voice.proto` 的 `VoiceConfigService` 新增 `NotifyGreetingModeChanged` RPC；`VoiceConfigClient.notify_greeting_mode` 走 `_dispatch_with_target(target="agent")`，仅推 agent 端；失败入 `grpc_retry_task` 重试队列（service_name=voice）

### 前端

- 参数配置页新增「打招呼模式」tab（`greeting-mode-tab.vue`），位于「人脸识别TTS」与「行走速度设置」之间
- 选中机器人后经 `fetchGetVoiceConfig` 读取当前 `greeting_mode`（默认 `wave`），保存调 `fetchUpdateGreetingMode`
- `Api.RobotConfig.VoiceConfig` 类型新增 `greeting_mode?: 'wave' | 'no_wave'`

## 约束与备注

- 语音合成 tab 的保存（`RobotVoiceConfigSchema`）不包含 `greeting_mode`，两个 tab 互不覆盖
- 说明文案：招手模式下机器人检测到访客执行打招呼动作；无招手模式下机器人唤醒后无招手动作，仅语音问候
- `backend/database` 与 `backend/grpc` 为 git 子模块，相关改动需在子模块内单独提交
- 存量行由 server_default `wave` 兜底

## 相关文件

- `backend/database/alembic/versions/0005_add_greeting_mode_to_robot_voice_config.py`
- `backend/database/models/business/robot_voice_config.py`
- `backend/modules/robot/schemas/robot_config.py`
- `backend/modules/robot/services/robot_config_service.py`
- `backend/modules/robot/services/robot_service.py`
- `backend/modules/robot/endpoints/robot_config.py`
- `backend/grpc/protos/config/voice.proto`（+ 重新生成 `generated/config/voice_pb2*.py`）
- `backend/modules/grpc/config_client.py`
- `frontend/src/views/settings/index.vue`
- `frontend/src/views/settings/modules/greeting-mode-tab.vue`
- `frontend/src/service/api/robot-config.ts`
- `frontend/src/typings/api/robot-config.d.ts`

## 记录日期

2026-08-25
