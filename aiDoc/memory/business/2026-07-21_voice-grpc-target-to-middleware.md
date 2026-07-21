# 语音配置 gRPC target 统一回归 middleware

**日期**: 2026-07-21
**提出者**: 用户

## 需求描述

参数配置中语音合成与唤醒词相关的 gRPC 调用，目标 target（对应 `robot.grpc_config` 的子键）由 agent 改为 **middleware**：

1. **语音合成保存** `VoiceConfigClient.notify_tts`（RPC `NotifyTTSConfigChanged`）：agent → **middleware**
2. **语音合成测试** `VoiceConfigClient.test_tts`（RPC `TestTTSConfig`）：agent → **middleware**
3. **唤醒词测试** `VoiceConfigClient.test_wake_word`（RPC `TestWakeWord`）：agent → **middleware**

唤醒词保存（`notify_wake_word`）本就走 middleware，未动。

## 状态

已完成

## 涉及范围

仅 `backend/modules/grpc/config_client.py`：

- `notify_tts` / `test_tts` / `test_wake_word` 三个方法的 `target` 由 `"agent"` 改为 `"middleware"`
- 同步更新文件头路由说明、`VoiceConfigClient` 类 docstring，保持文档与代码一致

> 其余 target 不变：`notify_wake_word`(唤醒词保存)→middleware；`notify_speed_level`(行走速度)→middleware；`battery.notify_battery_threshold`→agent；`face_recognition.notify_changed`→agent 广播；`video.notify_video_monitoring`→middleware。

## 约束与备注

- 地址解析仍在 `_dispatch_with_target` 内按 `robot.grpc_config[target]` 取 host:port，不回退 settings；`GRPC.ENABLED=false` 仍短路。
- 测试类 RPC（TestWakeWord / TestTTSConfig）失败仍直接 `response_base.fail`，不入重试队列（实时语义不变）。
- `retry_service.py` 的重试路由按 client 方法名索引，target 由 client 内部解析，无需改动。
- OpenAPI `/openapi/v1/speak` 复用 `VoiceConfigClient.test_tts`，本次随其改走 middleware；未新增 Speak RPC。
- 无前端改动、无 DB 迁移、无 proto 变更。
- 验证：`python -m py_compile backend/modules/grpc/config_client.py` 通过。

## 调整后完整 target 对照

| 配置项 | Client 方法 | RPC | target |
|---|---|---|---|
| 唤醒词保存 | `VoiceConfigClient.notify_wake_word` | `NotifyWakeWordChanged` | middleware |
| 唤醒词测试 | `VoiceConfigClient.test_wake_word` | `TestWakeWord` | **middleware** |
| TTS 保存 | `VoiceConfigClient.notify_tts` | `NotifyTTSConfigChanged` | **middleware** |
| TTS 测试 | `VoiceConfigClient.test_tts` | `TestTTSConfig` | **middleware** |
| 行走速度保存 | `SpeedConfigClient.notify_speed_level` | `NotifySpeedLevelChanged` | middleware |
| 电量阈值保存 | `BatteryConfigClient.notify_battery_threshold` | `NotifyBatteryThresholdChanged` | agent |
| 人脸库变更 | `FaceRecognitionClient.notify_changed` | `NotifyFaceRecognitionChanged` | agent（广播） |
| 视频监控启停 | `VideoMonitoringClient.notify_video_monitoring_changed` | `NotifyVideoMonitoringChanged` | middleware |

## 相关文件

- `backend/modules/grpc/config_client.py`

## 相关历史记忆

- [[2026-06-30_param-config-grpc-target-tweak]]（曾把 test_wake_word 由 middleware 改 agent；本次 test_wake_word 回归 middleware）
- [[2026-06-25_param-config-grpc-from-robot]]（原 target 路由表）
- [[2026-07-03_openapi-nav-grpc]]（speak 复用 test_tts，target 随本次同步）

## 记录日期

2026-07-21
