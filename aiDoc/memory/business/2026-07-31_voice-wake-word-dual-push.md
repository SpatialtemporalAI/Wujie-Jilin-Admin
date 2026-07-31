# 唤醒词保存 gRPC 改为同时推 middleware + agent

**日期**: 2026-07-31
**提出者**: 用户

## 需求描述

参数配置保存唤醒词时的 gRPC 推送，由「只推 middleware」改为「同时发送 agent 和 middleware」。

- 涉及方法：`VoiceConfigClient.notify_wake_word`（RPC `NotifyWakeWordChanged`）
- 唤醒词测试（`test_wake_word` / `TestWakeWord`）仍走 agent，**不动**
- TTS 保存/测试（`notify_tts` / `test_tts`）**不动**

## 状态

已完成

## 涉及范围

### 后端

仅 `backend/modules/grpc/config_client.py`：

- 重写 `VoiceConfigClient.notify_wake_word`：不再走单 target 的 `_dispatch_with_target`，改为
  1. 解析 `middleware` 与 `agent` 两个地址，仅收集「已配置且 enabled」的 target（未配置端跳过，兼容只配一端的机器人）
  2. `asyncio.gather` 并发向各 target 下发 `NotifyWakeWordChanged`（agent/middleware 是两个独立地址，各自复用 `_stubs_by_addr` 缓存的 stub）
  3. 聚合响应：所有「已配置端」全部 `success=True` 才返回 success；任一失败 → `success=False`，message 拼接各失败端原因
  4. 两端均未配置 → `success=False` 哨兵（按失败处理，可入重试队列等待配置）
- 新增 `import asyncio`
- 同步更新文件头「地址解析规则」与 `VoiceConfigClient` 类 docstring，反映双推语义

### 前端

无改动。

## 聚合语义（用户选定：都成功才算成功）

配合上层 `_push_with_retry` 的最终一致模型：

- 任一已配置端失败 → 整体 `success=False` → 由 `robot_config_service.save_voice_config` 入 `grpc_retry_task` 重试队列
- 重试时 `retry_service._wrap_voice_wake → notify_wake_word` 自动再次双推；`NotifyWakeWord` 是全量覆盖语义，重复推送幂等，不会造成设备端数据错误
- 覆盖键不变：仍为 `(voice, NotifyWakeWordChanged, robot_id)`，双推只产生**单条**重试任务，不存在两条任务互相 cancel 的问题（这也是选择在 client 层聚合、而非 service 层推两次的关键原因——`grpc_retry_task` 表无 target 维度，service 层推两次会用同覆盖键互相取消）

## 约束与备注

- **前置条件**：agent 端需已实现 `VoiceConfigService.NotifyWakeWordChanged`（与 middleware 共用同一 proto 生成的 stub）。若 agent 端未实现，推送会返回 `UNIMPLEMENTED` → 触发整体重试 → 最终 dead，前端会看到「未同步」。语义与 [[2026-07-07_map-grpc-agent-push]] 的 agent 端前置一致。
- 不复用 `_dispatch_with_target`：该内核把「地址未配置」与「调用失败」都返回 `success=False` 哨兵，无法区分「跳过未配置端」；故 `notify_wake_word` 自解析地址 + 内联异常处理，其余 client 方法仍走 `_dispatch_with_target`。
- `GRPC.ENABLED=false` 仍短路返回失败哨兵；stub 缓存按 addr 区分，middleware/agent 各自独立 stub，并发无 race。
- service 层 `save_voice_config` 调用签名不变；retry 层路由 `(voice, NotifyWakeWordChanged)` 不变；proto / DB / 前端零改动。
- 验证：`python -m py_compile` + `from modules.grpc.config_client import VoiceConfigClient` import 通过（项目无 ruff/mypy 配置）。

## 调整后完整 target 对照

| 配置项 | Client 方法 | RPC | target |
|---|---|---|---|
| 唤醒词保存 | `notify_wake_word` | `NotifyWakeWordChanged` | **middleware + agent（双推）** |
| 唤醒词测试 | `test_wake_word` | `TestWakeWord` | agent |
| TTS 保存 | `notify_tts` | `NotifyTTSConfigChanged` | middleware |
| TTS 测试 | `test_tts` | `TestTTSConfig` | agent |
| 行走速度保存 | `SpeedConfigClient.notify_speed_level` | `NotifySpeedLevelChanged` | middleware |
| 电量阈值保存 | `BatteryConfigClient.notify_battery_threshold` | `NotifyBatteryThresholdChanged` | agent |
| 人脸库变更 | `FaceRecognitionClient.notify_changed` | `NotifyFaceRecognitionChanged` | agent（广播） |
| 视频监控启停 | `VideoMonitoringClient.notify_video_monitoring_changed` | `NotifyVideoMonitoringChanged` | middleware |

## 相关文件

- `backend/modules/grpc/config_client.py`
- `backend/modules/robot/services/robot_config_service.py`（调用方，未改）
- `backend/modules/grpc/retry_service.py`（重试路由，未改）

## 相关历史记忆

- [[2026-07-28_voice-test-push-to-agent]] — 测试推送改走 agent；当时明确「保存类 notify_wake_word/notify_tts 不动仍走 middleware」
- [[2026-07-21_voice-grpc-target-to-middleware]] — 语音 target 曾统一回归 middleware
- [[2026-07-07_map-grpc-agent-push]] — 地图保存/切换由「只推 middleware」改为「middleware + agent 双推」，是本次同型改动的先例（同为 client 层路由扩展、agent 端需部署对应 service）
- [[2026-06-25_param-config-grpc-from-robot]] — 参数配置 gRPC 原始 target 路由表

## 记录日期

2026-07-31
