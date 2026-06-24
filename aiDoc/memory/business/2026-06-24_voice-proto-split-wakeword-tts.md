# voice.proto 拆分为唤醒词 + 语音合成两个 RPC

## 需求描述

将 `backend/grpc/protos/config/voice.proto` 中原本单一的 `NotifyVoiceConfigChanged` RPC 拆分为两个独立 RPC，按职责分离：

1. `NotifyWakeWordChanged` —— 仅推送唤醒词开关 + 唤醒词内容
2. `NotifyTTSConfigChanged` —— 仅推送 TTS 音色 / 语速 / 音量

每个 RPC 携带各自专属字段，不再共享一个包含 6 个字段的大 Request。

## 状态

已完成

## 涉及范围

### 后端

- proto 定义：`backend/grpc/protos/config/voice.proto`
  - service `VoiceConfigService` 拆分为两个 rpc 方法
  - 旧 message：`VoiceConfigChangedRequest` / `VoiceConfigChangedResponse` 删除
  - 新 message：
    - `WakeWordChangedRequest { robot_id, wake_word_enabled, wake_word }`
    - `WakeWordChangedResponse { success, message }`
    - `TTSConfigChangedRequest { robot_id, tts_voice, tts_speed, tts_volume }`
    - `TTSConfigChangedResponse { success, message }`
- 生成代码（重新编译产出）：`backend/grpc/generated/config/voice_pb2.py` / `voice_pb2_grpc.py`
- 服务端实现：**当前尚未实现 servicer**（拆分前也未实现），后续接入方需分别实现 `NotifyWakeWordChanged` / `NotifyTTSConfigChanged`
- 客户端调用：**当前 `save_voice_config` 仅写 DB，尚未接入 grpc**，后续接入时需根据变更字段分别调用对应 RPC

### 前端

无（前端 API 字段未变，仍是 `robot_id / wake_word_enabled / wake_word / tts_voice / tts_speed / tts_volume`）

## 约束与备注

- 字段语义与原 proto 完全一致，仅做方法拆分，不引入新字段
- `wake_word`：启用时 4-6 字，禁用时为空字符串
- `tts_voice`：male / female
- `tts_speed` / `tts_volume`：0-100
- 后续接入 servicer / client 时，应按变更类型选择对应 RPC，避免一次保存触发两次推送
- 编译命令：`cd backend/grpc && uv run python main.py`（Windows GBK 环境下需设 `PYTHONIOENCODING=utf-8 PYTHONUTF8=1`）

## 相关文件

- backend/grpc/protos/config/voice.proto
- backend/grpc/generated/config/voice_pb2.py
- backend/grpc/generated/config/voice_pb2_grpc.py

## 记录日期

2026-06-24
