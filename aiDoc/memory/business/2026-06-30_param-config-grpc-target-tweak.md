# 参数配置 gRPC target 调整：唤醒词测试 + 电量阈值改走 agent

**日期**: 2026-06-30
**提出者**: 用户

## 需求描述

参数配置两条 gRPC 推送的目标 target（对应 `robot.grpc_config` 的子键）由 middleware 改为 **agent**：

1. **唤醒词测试** `VoiceConfigClient.test_wake_word`（RPC `TestWakeWord`）：middleware → **agent**
2. **电量阈值保存** `BatteryConfigClient.notify_battery_threshold`（RPC `NotifyBatteryThresholdChanged`）：middleware → **agent**

## 状态

已完成

## 涉及范围

仅 `backend/modules/grpc/config_client.py`：

- `test_wake_word` 的 `target` 由 `"middleware"` 改为 `"agent"`
- `notify_battery_threshold` 的 `target` 由 `"middleware"` 改为 `"agent"`
- 同步更新文件头路由说明、`VoiceConfigClient` / `BatteryConfigClient` 类 docstring，保持文档与代码一致

> 其余 target 不变：`notify_wake_word`(唤醒词保存)→middleware；`notify_tts`/`test_tts`→agent；`notify_speed_level`(行走速度)→middleware；`face_recognition.notify_changed`→agent 广播。

## 约束与备注

- 地址解析仍在 `_dispatch_with_target` 内按 `robot.grpc_config[target]` 取 host:port，不回退 settings；`GRPC.ENABLED=false` 仍短路。
- `retry_service.py` 的重试路由按 client 方法名索引，target 由 client 内部解析，无需改动。
- 无前端改动、无 DB 迁移、无 proto 变更。
- 验证：`python -m py_compile backend/modules/grpc/config_client.py` 通过。

## 调整后完整 target 对照

| 配置项 | Client 方法 | RPC | target |
|---|---|---|---|
| 唤醒词保存 | `VoiceConfigClient.notify_wake_word` | `NotifyWakeWordChanged` | middleware |
| 唤醒词测试 | `VoiceConfigClient.test_wake_word` | `TestWakeWord` | **agent** |
| TTS 保存 | `VoiceConfigClient.notify_tts` | `NotifyTTSConfigChanged` | agent |
| TTS 测试 | `VoiceConfigClient.test_tts` | `TestTTSConfig` | agent |
| 行走速度保存 | `SpeedConfigClient.notify_speed_level` | `NotifySpeedLevelChanged` | middleware |
| 电量阈值保存 | `BatteryConfigClient.notify_battery_threshold` | `NotifyBatteryThresholdChanged` | **agent** |
| 人脸库变更 | `FaceRecognitionClient.notify_changed` | `NotifyFaceRecognitionChanged` | agent（广播，**当前未被调用**） |

## 相关文件

- `backend/modules/grpc/config_client.py`

## 相关历史记忆

- [2026-06-25 参数配置 gRPC 调用从 robot.grpc_config 取地址](./2026-06-25_param-config-grpc-from-robot.md)（原 target 路由表，本次调整其中 2 条；另注：该记忆里「人脸走 agent 广播」的客户端已实现但至今未接线调用）

## 记录日期

2026-06-30
