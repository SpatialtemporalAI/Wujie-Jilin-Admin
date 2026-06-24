# 语音合成语速参数改为 0.5-2 浮点 + slider 样式优化

**日期**: 2026-06-24
**提出者**: 用户

## 需求描述

调整语音合成界面的滑动条样式，并将语速从 0-100 整数改为 0.5-2.0 浮点（步长 0.1），跨栈同步。

## 状态

已完成

## 涉及范围

### 前端

- `frontend/src/views/settings/modules/voice-synthesis-tab.vue`
  - model 默认值 `tts_speed: 50` → `1.0`
  - 语速 slider：min=0.5, max=2, step=0.1, marks={0.5,1,1.5,2}，tooltip 关闭，下方文字显示「当前语速：X.X 倍」
  - 音量 slider：补 marks={0,50,100}，tooltip 关闭，下方文字显示「当前音量：X」（顺手统一）
  - slider 与说明文字用 `flex-col gap-8px w-full` 容器，纵向布局

### 后端

- `backend/database/models/business/robot_voice_config.py`：`tts_speed: Mapped[int | None]` → `Mapped[float | None]`，类型 `Integer` → `Float`，注释改为「语速（0.5-2.0，步长 0.1）」
- `backend/modules/robot/schemas/robot_config.py`：
  - `RobotVoiceConfigSchema.tts_speed: int` → `float`，加 `ge=0.5, le=2.0`
  - `RobotVoiceConfigResponse.tts_speed: Optional[int]` → `Optional[float]`
  - `TestTTSRequest.speed: int` → `float`，加 `ge=0.5, le=2.0`
- `backend/modules/robot/services/robot_config_service.py`：默认值 `tts_speed=50` → `1.0`

### 数据库迁移

- `backend/database/alembic/versions/0028_tts_speed_to_float.py`
  - upgrade：先把存量 0-100 归一化（`ROUND(speed/50, 1)` clamp 到 [0.5, 2.0]），再 alter column Integer→Float
  - downgrade：alter 回 Integer，并把 0.5-2.0 还原成 0-100（`ROUND(speed*50)`）
  - 同时给出 PostgreSQL `USING` 子句保证类型转换稳定

### gRPC proto

- `backend/grpc/protos/config/voice.proto`：`int32 tts_speed = 3;` → `float tts_speed = 3;`，注释从「语速 0-100」改为「语速 0.5-2.0，步长 0.1」
- `backend/grpc/generated/config/voice_pb2.py`：手改 FileDescriptorProto 序列化字节，把 tts_speed 字段的 type byte 从 `0x05`(TYPE_INT32) 改为 `0x02`(TYPE_FLOAT)
  - 字节长度不变，文件偏移无需调整
  - tts_volume 仍为 INT32，未受影响
  - 已用 `google.protobuf.descriptor.FieldDescriptor.TYPE_FLOAT` 校验通过

## 约束与备注

- 全栈同步改（用户明确确认）
- gRPC NotifyTTSConfigChanged 当前是空壳端点（service 层未实际调用），所以 proto 字段类型变更不影响运行时业务路径，但 message 描述必须与 proto 一致以免 runtime 校验失败
- 项目无 `grpc_tools`，无法 `protoc` 重新生成，因此采用「手改二进制 + 字段偏移不变」的方案
- 默认值 1.0 对应「正常语速」（与 TTS 行业惯例一致：Azure/阿里/AWS 均 0.5-2.0，1.0 为默认）

## 相关文件

- [frontend/src/views/settings/modules/voice-synthesis-tab.vue](frontend/src/views/settings/modules/voice-synthesis-tab.vue)
- [backend/database/models/business/robot_voice_config.py](backend/database/models/business/robot_voice_config.py)
- [backend/modules/robot/schemas/robot_config.py](backend/modules/robot/schemas/robot_config.py)
- [backend/modules/robot/services/robot_config_service.py](backend/modules/robot/services/robot_config_service.py)
- [backend/database/alembic/versions/0028_tts_speed_to_float.py](backend/database/alembic/versions/0028_tts_speed_to_float.py)
- [backend/grpc/protos/config/voice.proto](backend/grpc/protos/config/voice.proto)
- [backend/grpc/generated/config/voice_pb2.py](backend/grpc/generated/config/voice_pb2.py)

## 关键设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 改动范围 | 全栈同步 | 用户明确选择，避免前后端类型不一致 |
| proto 字段类型 | float（非 double） | 0.5-2.0 步长 0.1 的精度需求 float 足够；行业惯例 |
| pb2.py 重生成方式 | 手改二进制 | 项目无 grpc_tools，字节长度不变所以安全可行 |
| 存量数据迁移 | ROUND(speed/50, 1) clamp [0.5,2.0] | 50 → 1.0 自然映射 |
| 默认值 | 1.0 | 对应「正常语速」，与 TTS 行业惯例一致 |
| 音量字段 | 不改 | 用户只要求改语速，音量保留 0-100 |
