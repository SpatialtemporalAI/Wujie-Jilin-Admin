# 2026-11-25 会议管理（声纹注册 / 会议纪要 / 蓝牙设备连接）

## 需求描述

3.0 分支新增左侧一级菜单「会议管理」，包含三个子项：

1. **声纹注册**：选择机器人，浏览器麦克风采集发言人语音，上传平台存储后由后端下发 agent 完成 ASR + 声纹建模；支持查看注册记录、删除声纹、开关机器人会议模式。
2. **会议纪要**：机器人 agent 会后主动上报会议（逐字稿、发言人、总结、音频），平台负责存储、列表/详情展示、人工改派发言人、回收站与导出。
3. **蓝牙设备连接**：设备尚未到位，本期只保留菜单与占位页，不做功能。

三个功能均需权限管理，菜单初期不向所有角色开放，需在角色管理中按权限码分配。

## 状态

已完成（蓝牙设备连接为占位，待设备到位后开发）

## 涉及范围

### 后端

- 新模块 `backend/modules/meeting/`
  - `schemas/`：`voiceprint.py`、`minutes.py`、`agent.py`
  - `services/`：`voiceprint_service.py`、`minute_service.py`
  - `endpoints/`：`voiceprint.py`、`minutes.py`、`agent.py`
  - `router.py`：后台路由挂 `/admin/meeting`，agent 开放路由挂 `/openapi/v1/meeting`
- 新表（迁移 `0021_add_meeting_tables.py`）：`meeting_voiceprint`、`meeting_minute`、`meeting_minute_speaker`、`meeting_minute_segment`
- 菜单与权限（迁移 `0022_seed_meeting_menu.py`）：一级目录 `meeting` + 三个菜单 + 按钮权限
  - `meeting:voiceprint:list/add/delete/meeting_mode`
  - `meeting:minutes:list/detail/edit/delete/export`
  - `meeting:bluetooth:list`
- gRPC（平台 → agent）
  - `backend/grpc/protos/config/voiceprint.proto`：`VoiceprintService.RegisterVoiceprint` / `DeleteVoiceprint`
  - `meeting_mode.proto` 复用 `MeetingModeService.SetMeetingMode`
  - `modules/grpc/config_client.py` 新增 `VoiceprintClient`、`MeetingModeClient`，均走 `robot.grpc_config.agent`
- agent 开放接口（agent → 平台）
  - `POST /openapi/v1/meeting/files`：multipart `file`，返回 `file_id`
  - `POST /openapi/v1/meeting/minutes/report`：按 `meeting_no` 幂等 upsert，覆盖时先清空旧发言人/逐字稿
  - 鉴权：请求头 `X-Agent-Token` 对齐 `MEETING__AGENT_TOKEN`，为空不校验
- 后台接口（Web 端）
  - 声纹：`GET /voiceprint/robots`、`GET /voiceprint/overview`、`GET /voiceprint/list`、`POST /voiceprint/register`、`DELETE /voiceprint/{id}`、`PUT /voiceprint/meeting-mode`
  - 纪要：`GET /minutes/list`、`GET /minutes/trash`、`DELETE /minutes/trash/clear`、`GET /minutes/{id}`、`PUT /minutes/segments/{segment_id}/speaker`、`GET /minutes/{id}/export`、`DELETE /minutes/{id}`、`POST /minutes/{id}/restore`、`DELETE /minutes/{id}/purge`

### 前端

- 路由：`frontend/src/router/elegant/{imports.ts,transform.ts}` + `typings/elegant-router.d.ts` 增加 `meeting`、`meeting_voiceprint`、`meeting_minutes`、`meeting_bluetooth`
- i18n：`locales/langs/{zh-cn,en-us}.ts` 增加 `route.meeting*` 与按钮权限文案
- API：`frontend/src/service/api/meeting.ts`、`frontend/src/typings/api/meeting.d.ts`
- 页面：
  - `frontend/src/views/meeting/voiceprint/index.vue`：NSteps 录音流程（MediaRecorder、60s 自动停止、试听/重录）、声纹记录表格、会议模式开关
  - `frontend/src/views/meeting/minutes/index.vue`：纪要列表/回收站、详情抽屉（音频、总结、结论、风险、发言人、逐字稿改派）、导出
  - `frontend/src/views/meeting/bluetooth/index.vue`：占位页

### 文档

- `aiDoc/frontend-backend/meeting-agent-api.md`：agent 端 gRPC + HTTP 完整对接说明

## 约束与备注

- 声纹采集固定为浏览器麦克风整段录音（`method=record`），后端统一下发 `audio` bytes 给 agent。
- 会议模式开启前必须先成功注册至少 1 条声纹（前端限制 `registered_count > 0`）。
- 声纹注册失败也会保留记录（`status=failed` + `error_msg`），便于排查与重试。
- agent 上报以 `meeting_no` 为全局幂等键；重复上报是**全量覆盖**，必须每次传完整 `speakers` 与 `segments`。
- agent 上报的会议若已被软删除，同 `meeting_no` 再上报会自动恢复。
- 时间字段兼容 ISO8601 与 `YYYY-MM-DD HH:MM:SS`，无时区按 `Asia/Shanghai`。
- gRPC 未启用或机器人不可达时后端降级：声纹记录落库为 failed 并提示；会议模式切换直接报错。
- 权限码需在角色管理中分配后菜单才可见，默认不对所有角色开放。

## 相关文件

- `backend/modules/meeting/router.py`
- `backend/modules/meeting/endpoints/{voiceprint,minutes,agent}.py`
- `backend/modules/meeting/services/{voiceprint_service,minute_service}.py`
- `backend/modules/meeting/schemas/{voiceprint,minutes,agent}.py`
- `backend/database/models/business/meeting_voiceprint.py`
- `backend/database/models/business/meeting_minute.py`
- `backend/database/models/business/meeting_minute_speaker.py`
- `backend/database/models/business/meeting_minute_segment.py`
- `backend/database/alembic/versions/0021_add_meeting_tables.py`
- `backend/database/alembic/versions/0022_seed_meeting_menu.py`
- `backend/grpc/protos/config/voiceprint.proto`
- `backend/grpc/protos/config/meeting_mode.proto`
- `backend/modules/grpc/config_client.py`
- `backend/modules/robot/services/robot_meeting_mode_service.py`
- `frontend/src/service/api/meeting.ts`
- `frontend/src/typings/api/meeting.d.ts`
- `frontend/src/views/meeting/voiceprint/index.vue`
- `frontend/src/views/meeting/minutes/index.vue`
- `frontend/src/views/meeting/bluetooth/index.vue`
- `aiDoc/frontend-backend/meeting-agent-api.md`

## 记录日期

2026-11-25
