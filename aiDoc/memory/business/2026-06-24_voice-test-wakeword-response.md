# 唤醒词测试按钮右侧显示模拟回应话术 + proto 新增测试 RPC

## 需求描述

参数配置 → 语音合成 → 唤醒词配置，点击「测试」按钮时：

1. 在测试按钮**右侧**显示机器人模拟被唤醒后的回应话术：`<唤醒词>在呢，有什么可以帮您？`
   - `<唤醒词>` 替换为用户当前输入的唤醒词内容（例如用户填「你好小捷」时显示「你好小捷在呢，有什么可以帮您？」）
2. `voice.proto` 增加与「测试」语义对应的 RPC，与上一次拆分的 Notify 类 RPC 保持对称。

## 状态

已完成

## 涉及范围

### 后端

- proto：`backend/grpc/protos/config/voice.proto`
  - service `VoiceConfigService` 新增两个 rpc：
    - `TestWakeWord(TestWakeWordRequest) returns (TestWakeWordResponse)`
    - `TestTTSConfig(TestTTSConfigRequest) returns (TestTTSConfigResponse)`
  - 新增 message：
    - `TestWakeWordRequest { robot_id, wake_word }`
    - `TestWakeWordResponse { success, message }`（message 注释示例：`<wake_word>在呢，有什么可以帮您？`）
    - `TestTTSConfigRequest { robot_id, tts_voice, tts_speed(float), tts_volume, text }`
    - `TestTTSConfigResponse { success, message }`
- 生成代码（重新编译产出）：`backend/grpc/generated/config/voice_pb2.py` / `voice_pb2_grpc.py`
- HTTP 端点（**已存在、未改**）：
  - `POST /robot/config/voice/test-wake-word`（空壳端点）
  - `POST /robot/config/voice/test-tts`（空壳端点）
- 服务端 servicer 实现：**尚未实现**，与 Notify 类 RPC 状态一致；后续接入方需实现 `TestWakeWord` / `TestTTSConfig`

### 前端

- 页面：`frontend/src/views/settings/modules/voice-synthesis-tab.vue`
  - 新增响应式状态 `wakeWordTestText` + 定时器 `wakeWordTestTimer`
  - `handleTestWakeWord` 成功后：
    - 赋值 `wakeWordTestText = '${model.wake_word}在呢，有什么可以帮您？'`
    - 5 秒后自动清空（与 `showAlert` 行为一致）
  - 模板：唤醒词「测试」按钮所在 `NSpace` 增加 `align="center"`，并在按钮右侧追加 `<NText v-if="wakeWordTestText" type="info">` 显示话术
- API：`fetchTestWakeWord`（已存在，未改）

## 约束与备注

- 前端展示的话术中 `<唤醒词>` 占位符在渲染时替换为 `model.wake_word` 实际值
- 测试按钮仅在 `!faceWakeEnabled`（即唤醒词模式）下显示；人脸识别免唤醒模式点击测试会给出 warning 提示
- 测试话术 5 秒后自动消失，避免长时间停留
- proto 中 `TestTTSConfigRequest.text` 由前端传入（当前前端固定为「您好，这是语音合成测试。」）
- proto 编译命令：`cd backend/grpc && PYTHONIOENCODING=utf-8 PYTHONUTF8=1 uv run python main.py`（Windows GBK 控制台需显式 UTF-8）

## 相关文件

- backend/grpc/protos/config/voice.proto
- backend/grpc/generated/config/voice_pb2.py
- backend/grpc/generated/config/voice_pb2_grpc.py
- backend/modules/robot/endpoints/robot_config.py（端点已存在，未改）
- frontend/src/views/settings/modules/voice-synthesis-tab.vue
- frontend/src/service/api/robot-config.ts（已存在，未改）

## 记录日期

2026-06-24
