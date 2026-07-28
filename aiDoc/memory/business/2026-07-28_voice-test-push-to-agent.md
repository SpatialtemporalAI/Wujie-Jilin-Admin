# 唤醒词测试 / 语音合成测试推送改走机器人 agent

**日期**: 2026-07-28
**提出者**: 用户

## 需求描述

参数配置 - 唤醒词配置 / 语音合成 中的两个**测试推送**，gRPC target（对应 `robot.grpc_config` 的子键）由 middleware 改为 **agent**：

1. **唤醒词测试** `VoiceConfigClient.test_wake_word`（RPC `TestWakeWord`）：middleware → **agent**
2. **语音合成测试** `VoiceConfigClient.test_tts`（RPC `TestTTSConfig`）：middleware → **agent**

> 用户原话：「参数配置-唤醒词配置/语音合成的两个测试推送都往机器人的 agent 发送」。

仅改两个**测试**方法。保存配置类推送不动 —— `notify_wake_word`（唤醒词保存）、`notify_tts`（语音合成保存）仍走 middleware。

## 状态

已完成

## 涉及范围

仅 `backend/modules/grpc/config_client.py`：

- `test_wake_word` 的 `target` 由 `"middleware"` 改为 `"agent"`
- `test_tts` 的 `target` 由 `"middleware"` 改为 `"agent"`
- 同步更新文件头路由说明、`VoiceConfigClient` 类 docstring，保持文档与代码一致

> 其余 target 不变：`notify_wake_word`(唤醒词保存)→middleware；`notify_tts`(语音合成保存)→middleware；`notify_speed_level`(行走速度)→middleware；`battery.notify_battery_threshold`→agent；`face_recognition.notify_changed`→agent 广播；`video.notify_video_monitoring`→middleware。

## 约束与备注

- 地址解析仍在 `_dispatch_with_target` 内按 `robot.grpc_config[target]` 取 host:port，不回退 settings；`GRPC.ENABLED=false` 仍短路。若机器人未配置 agent 地址（`grpc_config.agent` 缺失 / enabled=false / 无 host:port），返回 success=False 哨兵，前端提示「测试失败，请确保机器人在线」。
- 测试类 RPC（TestWakeWord / TestTTSConfig）失败仍直接 `response_base.fail`，不入重试队列（实时语义不变）。
- `retry_service.py` 的重试路由按 client 方法名索引，target 由 client 内部解析，无需改动。
- **OpenAPI `/openapi/v1/speak` 复用 `VoiceConfigClient.test_tts`**，本次随其改走 agent；未新增 Speak RPC。（与 07-21 回归 middleware 时同源连带，`aiDoc/frontend-backend/boundary.md` 仅记「复用 test_tts」未写死 target，无需同步。）
- **前提**：机器人 agent 侧需已实现 `VoiceConfigService` 的 `TestWakeWord` / `TestTTSConfig` 两个 RPC，否则调用会失败并走上述 fail 文案。
- 无前端改动、无 DB 迁移、无 proto 变更。
- 验证：`python -m py_compile backend/modules/grpc/config_client.py` 通过。

## 调整后完整 target 对照

| 配置项 | Client 方法 | RPC | target |
|---|---|---|---|
| 唤醒词保存 | `VoiceConfigClient.notify_wake_word` | `NotifyWakeWordChanged` | middleware |
| 唤醒词测试 | `VoiceConfigClient.test_wake_word` | `TestWakeWord` | **agent** |
| TTS 保存 | `VoiceConfigClient.notify_tts` | `NotifyTTSConfigChanged` | middleware |
| TTS 测试 | `VoiceConfigClient.test_tts` | `TestTTSConfig` | **agent** |
| 行走速度保存 | `SpeedConfigClient.notify_speed_level` | `NotifySpeedLevelChanged` | middleware |
| 电量阈值保存 | `BatteryConfigClient.notify_battery_threshold` | `NotifyBatteryThresholdChanged` | agent |
| 人脸库变更 | `FaceRecognitionClient.notify_changed` | `NotifyFaceRecognitionChanged` | agent（广播） |
| 视频监控启停 | `VideoMonitoringClient.notify_video_monitoring_changed` | `NotifyVideoMonitoringChanged` | middleware |

## 相关文件

- `backend/modules/grpc/config_client.py`
- `backend/modules/robot/endpoints/robot_config.py`（`/voice/test-wake-word`、`/voice/test-tts` 调用方，未改）

## 相关历史记忆

- [[2026-07-21_voice-grpc-target-to-middleware]]（上次把 test_wake_word / test_tts / notify_tts 由 agent 统一回归 middleware；本次仅把两个测试再改回 agent，notify_tts 仍留 middleware）
- [[2026-06-30_param-config-grpc-target-tweak]]（更早一次把 test_wake_word 由 middleware 改 agent）
- [[2026-07-03_openapi-nav-grpc]]（speak 复用 test_tts，target 随本次同步）

## 记录日期

2026-07-28
