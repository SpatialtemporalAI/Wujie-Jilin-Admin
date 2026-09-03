# 唤醒词配置增加「回复方式」（配置语料 / 调用大模型）

## 需求描述

参数配置 → 语音配置 → 唤醒词配置新增「回复方式」：

- 单选「配置语料」/「调用大模型」
- 选「配置语料」时可设置语料模板：「唤醒词」在呢，有什么可以帮您 / 在呢，有什么可以帮您 / 自定义回复内容（选中后支持输入）
- 非自定义模板提供只读语料预览（【唤醒词】占位符实时替换为当前唤醒词）
- 「测试回复」按钮按当前 TTS 参数播报预览语料（复用 test-tts 通道）
- 保存时随唤醒词经 gRPC NotifyWakeWordChanged 推送给 middleware + agent

## 状态

已完成

## 涉及范围

### 后端

- `robot_voice_config` 表新增 `wake_reply_mode`（corpus/llm，server_default 'corpus'）与 `wake_reply_text`（可空，最长 200）两列，迁移 `0007`
- `RobotVoiceConfigSchema` / `RobotVoiceConfigResponse` 增加两字段；corpus 且启用唤醒词时回复语料必填，null/空兜底为 corpus
- `save_voice_config` 把 reply 字段纳入 "wake" 变更组；推送前把语料中的【唤醒词】占位符渲染为实际唤醒词
- `voice.proto` 的 `WakeWordChangedRequest` 新增 `wake_reply_mode = 4`、`wake_reply_text = 5`（proto3 新增字段向后兼容），pb2 已重新生成
- `VoiceConfigClient.notify_wake_word` 增加两参数；重试路由 `_wrap_voice_wake` 同步，重试 kwargs 由按 required_keys 抽取改为 payload 整体透传（wrapper 默认值兼容旧格式 payload）

### 前端

- `Api.RobotConfig.VoiceConfig` 增加 `wake_reply_mode` / `wake_reply_text`
- `voice-synthesis-tab.vue` 唤醒词配置卡片内新增回复方式 radio、语料模板下拉、自定义输入、语料预览、测试回复按钮
- 预设模板以「模板原文（含【唤醒词】占位符）」存库，加载时按文本命中回填模板选择，未命中归入自定义
- 语料模板选择是本地 UI 状态，不单独落库

## 约束与备注

- 预设模板存模板原文而非渲染后文本，避免改唤醒词后语料过期；后端推送时才渲染占位符
- proto 位于 git 子模块 `backend/grpc`（Wujie-Jilin-Grpc），改动需在子模块仓库提交推送，并在主仓库更新子模块指针
- 生成 pb2：`cd backend/grpc && uv run python main.py`（Windows GBK 控制台需 `PYTHONUTF8=1`）
- 测试回复复用 `POST /admin/robot/config/voice/test-tts`，无新增接口

## 相关文件

- `backend/database/models/business/robot_voice_config.py`
- `backend/database/alembic/versions/0007_add_wake_reply_to_robot_voice_config.py`
- `backend/modules/robot/schemas/robot_config.py`
- `backend/modules/robot/services/robot_config_service.py`
- `backend/grpc/protos/config/voice.proto` + `backend/grpc/generated/config/voice_pb2.py`
- `backend/modules/grpc/config_client.py`、`backend/modules/grpc/retry_service.py`
- `frontend/src/typings/api/robot-config.d.ts`
- `frontend/src/views/settings/modules/voice-synthesis-tab.vue`

## 记录日期

2026-09-02
