# 参数配置 gRPC 调用从 robot.grpc_config 取地址

## 需求描述

参数配置服务（语音 / 速度 / 电量 / 人脸 4 类 RPC）调用外部 ConfigService 时，地址原本全部走全局 `settings.GRPC.CONFIG_SERVICE_ADDR`，所有机器人共用一个地址。

需求：让 4 类 RPC 按 RPC 类型分流到 `robot.grpc_config` 的不同子键（agent / middleware / ros），地址完全来自 `robot.grpc_config`，不再回退到 settings。

## 状态

已完成

## 分流规则

| Client.method | target | 说明 |
|---|---|---|
| `VoiceConfigClient.notify_wake_word` | middleware | 唤醒词配置 |
| `VoiceConfigClient.test_wake_word` | middleware | 唤醒词测试 |
| `VoiceConfigClient.notify_tts` | agent | TTS 音色/语速/音量 |
| `VoiceConfigClient.test_tts` | agent | TTS 测试 |
| `SpeedConfigClient.notify_speed_level` | middleware | 行走速度 |
| `BatteryConfigClient.notify_battery_threshold` | middleware | 电量阈值 |
| `FaceRecognitionClient.notify_changed` | agent（广播） | 遍历所有启用 agent 的 robot |

## 兜底规则

- **完全依赖 grpc_config**：`grpc_config[target]` 缺失 / enabled=false / 无 host/port → 返回 `success=False` 失败哨兵（消息含 `target=xxx`），**不回退 settings**
- `settings.GRPC.ENABLED=false` 仍作为总开关短路（开发环境关闭）
- 人脸广播：查不到任何启用 agent 的 robot → 失败哨兵 `无启用 agent 的机器人`；任一 robot 成功即整体 `success=True`

## 涉及范围

### 后端

- `backend/modules/grpc/addr_provider.py`
  - 抽象 `ConfigServiceAddrProvider.get_addr(robot_id, target)`，新增 `find_addrs_by_target(target)`
  - 新增 `RobotConfigAddrProvider`：从 `robot.grpc_config` JSON 解析 host:port；广播接口遍历所有启用该 target 的 robot
  - 保留 `SettingsConfigAddrProvider` 做兼容兜底
  - 默认全局单例切到 `RobotConfigAddrProvider()`
- `backend/modules/grpc/channel.py`
  - ConfigService channel 从单例改为 **按地址缓存多通道**：`_config_channels: dict[addr, Channel]`
  - 新增 `get_config_channel_by_addr(addr)` / `close_all_config_channels()`
  - `close_channel()` 内部统一关闭 MapService + ConfigService 全部通道
- `backend/modules/grpc/config_client.py`
  - `_dispatch` 改造为 `_dispatch_with_target(robot_id, target, stub_factory, ...)`：先 ENABLED 短路 → 调 provider 解析 addr → 按 addr 取 stub → 调用
  - 每个 Client 类的 `_stub` 单例 → `_stubs_by_addr: dict[addr, XStub]`，按 addr 缓存 stub
  - 每个 RPC 方法显式声明 target（middleware / agent）
  - `FaceRecognitionClient.notify_changed` 改为广播：内部调 `find_addrs_by_target("agent")` 取地址列表，逐个推送，任一成功即整体成功
- `backend/main.py`
  - lifespan init 阶段显式注入 `set_config_addr_provider(RobotConfigAddrProvider())`
  - shutdown 阶段复用 `close_channel()`（内部已调 `close_all_config_channels()`）

### 调用方零改动

- `backend/modules/robot/services/robot_config_service.py`：所有 client 调用签名不变，`_push_with_retry` 包装不变
- `backend/modules/grpc/retry_service.py`：`_ROUTING` 路由表不变；重试时 client 内部按当前 `robot.grpc_config` 取地址，自动跟随 grpc_config 变更

### 前端

- **无改动**：`grpc_config` 字段在前端 drawer 里已可配，本次仅消费侧接入

## 关键决策

- **完全依赖 grpc_config 不回退**：保证"机器人没配 grpc_config 就不调" 的强契约，避免误打全局地址
- **人脸走广播而非单 robot**：人脸配置表无 robot_id 字段，业务语义是"广播给所有 robot 的 agent"
- **channel 按 addr 缓存**：避免不同 robot 切换时反复重建 channel
- **保留 SettingsConfigAddrProvider 与 .env 配置**：兼容单测和临时回退，不删
- **不做 channel 主动清理**：robot.grpc_config 变更时不主动关闭旧 addr 通道，依赖自然淘汰

## 约束与备注

- 仅做后端改动，未做 UI 测试（本次纯消费侧接入）
- 与 [[2026-06-25_robot-grpc-config-add-ros]] 同源：那次加了 ros 子键，这次让 grpc_config 真正被消费
- 与 [[2026-06-24_robot-manage-grpc-config-and-fixes]] 对接：那次引入 grpc_config JSON 字段，这次让参数配置 RPC 真正按 robot 维度路由

## 相关文件

后端：
- `backend/modules/grpc/addr_provider.py`
- `backend/modules/grpc/channel.py`
- `backend/modules/grpc/config_client.py`
- `backend/main.py`

调用方（未改）：
- `backend/modules/robot/services/robot_config_service.py`
- `backend/modules/grpc/retry_service.py`

## 记录日期

2026-06-25
