# 参数配置页面接入 gRPC client 骨架（通用调度层 + 地址 Provider 抽象）

## 需求描述

「参数配置」页面（语音合成 / 人脸识别 / 行走速度 / 电量阈值 4 个 Tab）所有按钮原本只调 HTTP + 操作数据库，
**未调用任何 gRPC 服务**——用户改了参数，机器人侧不会立即收到通知。

本次接入 gRPC client 骨架：
1. 各 Tab 的「保存」按钮：DB 写入成功后调用对应 NotifyXxxChanged RPC 推送给机器人侧立即生效
2. voice Tab 的「测试」按钮：调用 TestXxx RPC（原本是空壳端点，本次接真实 gRPC）
3. 人脸库增/改/删：DB 操作后调用 NotifyFaceRecognitionChanged（带 operation 枚举）

**用户的关键诉求是「grpc 服务动态传参调用」**，最终采用方案：**proto 强类型不变 + client 层通用调度内核**。

服务端尚未就绪，本次只搭 client 侧：
- `GRPC.ENABLED=false` 时静默跳过（返回 success=False 哨兵响应，不抛异常）
- `GRPC.ENABLED=true` 但无服务端时，gRPC 异常被 _dispatch 吞掉，仅记 WARNING 日志，不阻塞业务

## 状态

已完成

## 涉及范围

### 后端（新建 2 + 修改 5）

#### 新建

- `backend/modules/grpc/addr_provider.py`：ConfigServiceAddrProvider 抽象接口 + SettingsConfigAddrProvider 默认实现 + `set_config_addr_provider()` 全局注入点
  - 为「后续从数据库表读地址（按 robot_id 维度等）」预留扩展点
  - 切换实现只需启动时 `set_config_addr_provider(DbConfigAddrProvider())`，业务代码零改动
- `backend/modules/grpc/config_client.py`：通用调度内核 + 4 个业务 Client
  - `_dispatch()` 统一处理：ENABLED 短路、stub 惰性创建+缓存、超时、grpc.aio.AioRpcError 异常吞掉、logger.warning、失败响应构造
  - `VoiceConfigClient`：notify_wake_word / notify_tts / test_wake_word / test_tts
  - `SpeedConfigClient`：notify_speed_level
  - `BatteryConfigClient`：notify_battery_threshold
  - `FaceRecognitionClient`：notify_changed / notify_create / notify_update / notify_delete

#### 修改

- `backend/core/config/settings_model.py`：GrpcModel 新增 `CONFIG_SERVICE_ADDR`（默认 127.0.0.1:50052，与 MAP_SERVICE_ADDR 解耦）
- `backend/.env.dev` / `.env.test` / `.env.prod`：各加一行 `GRPC__CONFIG_SERVICE_ADDR`
- `backend/modules/grpc/channel.py`：
  - 新增 `_config_channel` + `_config_channel_addr` + `_config_reconfigure_lock`
  - 新增 `get_config_channel()` 协程：惰性创建 ConfigService channel，地址变更时关闭旧 channel 重建
  - `close_channel()` 同时关闭 MapService 和 ConfigService 两个 channel
  - 不与现有 MapService channel 耦合
- `backend/modules/robot/schemas/robot_config.py`：
  - `TestWakeWordRequest` 新增 `robot_id: int`
  - `TestTTSRequest` 新增 `robot_id: int`
- `backend/modules/robot/services/robot_config_service.py`：5 个方法 DB commit 后插入推送
  - `save_voice_config`：智能拆分（对比 existing 与 schema 字段变化，决定调 NotifyWakeWordChanged / NotifyTTSConfigChanged 中的一个或两个；新建时全推）
  - `create_face` → notify_create
  - `update_face` → notify_update
  - `delete_face` → notify_delete
  - `update_speed_level` → SpeedConfigClient.notify_speed_level
  - `update_battery_threshold` → BatteryConfigClient.notify_battery_threshold
- `backend/modules/robot/endpoints/robot_config.py`：
  - `test_wake_word`：空壳端点替换为 `VoiceConfigClient.test_wake_word` 真实调用
  - `test_tts`：空壳端点替换为 `VoiceConfigClient.test_tts` 真实调用
  - 字段映射：前端 `voice/speed/volume` → proto `tts_voice/tts_speed/tts_volume`（在 client 方法内完成）

### 前端（修改 3）

- `frontend/src/typings/api/robot-config.d.ts`：TestWakeWordRequest / TestTTSRequest 加 `robot_id: number`
- `frontend/src/service/api/robot-config.ts`：`fetchTestWakeWord` 签名从 `(text: string)` 改为 `(data: TestWakeWordRequest)`，整体传 data
- `frontend/src/views/settings/modules/voice-synthesis-tab.vue`：
  - `handleTestWakeWord`：调用改为 `fetchTestWakeWord({ robot_id: model.robot_id, text: model.wake_word })`，补「请先选择机器人」前置校验
  - `handleTestTTS`：调用时补 `robot_id: model.robot_id`，补前置校验

### 不动

- proto 文件：speed/battery/face 已有 Notify RPC，voice 已有 Test RPC，本次不新增
- MapServiceClient：保持原样，新增 config_client 与之并行
- 前端按钮：仅接入现有按钮，不新增按钮
- 数据库表：本次不建表，地址 Provider 抽象已预留扩展点

## 关键设计决策

### 1. 强类型 + 通用调度内核（不做"万能 dispatch"）

考虑过用反射做 `dispatch(service_name, method_name, params_dict)` 一个 endpoint 通吃，但：
- Python gRPC stub 方法绑定在生成类上，按字符串路由丢失类型提示
- 弱类型增加心智负担、错误难定位

最终方案：proto 强类型不变，client 层用通用 `_dispatch` 内核统一处理样板逻辑（ENABLED/超时/异常/日志），每个 RPC 仍有专门方法。

### 2. 最终一致语义（不回滚 DB）

DB commit 成功后再推送 gRPC，**推送失败不回滚 DB、不抛异常**：
- DB 是 source of truth，设备掉线时本来就该容忍
- 后续可加补偿任务（超时未确认则重推）
- 前端不会因 gRPC 失败看到 500（但 DB 已改）

### 3. voice 保存的智能拆分

按字段变化决定调几个 RPC，避免每次保存都全量推送：
- 唤醒词开关或内容变化 → NotifyWakeWordChanged
- TTS 音色/语速/音量变化 → NotifyTTSConfigChanged
- 字段未变时不推
- 新建记录时全推

### 4. 地址 Provider 抽象（为数据库读取预留）

用户决策："config 类 gRPC 服务的地址如何配置？" → "预留位置，后续会从数据库表中获取"

抽象出 `ConfigServiceAddrProvider`：
- 默认 `SettingsConfigAddrProvider` 从 `settings.GRPC.CONFIG_SERVICE_ADDR` 读
- 提供 `set_config_addr_provider(p)` 全局注入点
- 将来要做机器人维度独立地址时，新增 `DbConfigAddrProvider` 实现并在启动时注入

## 验证方案

服务端未就绪，分两档验证：

### 档 1：GRPC_ENABLED=false（开发默认）
- 点全部 5 类按钮（voice 保存/voice 测试×2/speed 保存/battery 保存/face 增改删）
- 预期：DB 正常写入，前端成功提示，gRPC client 返回 disabled 哨兵，日志无 ERROR

### 档 2：GRPC_ENABLED=true（无服务端）
- 同上点全部按钮
- 预期：DB 正常写入，前端仍成功（service 层吞掉 RpcError）；后端日志出现 `WARNING ... grpc.RpcError code=UNAVAILABLE`

### 前端验证
- `pnpm typecheck` 通过（参照 long-term 偏好 [[feedback-typecheck-only]]）

## 相关文件

后端：
- backend/modules/grpc/addr_provider.py（新建）
- backend/modules/grpc/config_client.py（新建）
- backend/modules/grpc/channel.py（修改）
- backend/core/config/settings_model.py（修改）
- backend/.env.dev / .env.test / .env.prod（修改）
- backend/modules/robot/schemas/robot_config.py（修改）
- backend/modules/robot/services/robot_config_service.py（修改）
- backend/modules/robot/endpoints/robot_config.py（修改）

前端：
- frontend/src/typings/api/robot-config.d.ts（修改）
- frontend/src/service/api/robot-config.ts（修改）
- frontend/src/views/settings/modules/voice-synthesis-tab.vue（修改）

## 记录日期

2026-06-24
