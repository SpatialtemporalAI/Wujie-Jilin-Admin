# 创建机器人时默认启用唤醒词「小护小护」

**日期**: 2026-06-30
**提出者**: 用户

## 需求描述

创建机器人时，默认开启唤醒词唤醒，唤醒词默认值为「小护小护」。

## 背景

唤醒词（`wake_word_enabled` / `wake_word`）存储在 `robot_voice_config` 表（与 TTS 音色/语速/音量同表），按 `robot_id` 唯一。此前该配置**惰性创建**：

- `RobotService.create` 只建 `Robot` + `RobotStatusRecord`，**不建** `RobotVoiceConfig`。
- `RobotConfigService.get_voice_config` 在无配置行时返回**未持久化**的兜底对象，原默认 `wake_word_enabled=False, wake_word=""`。
- 配置行只在用户进「参数配置→语音合成」保存（`save_voice_config` upsert）时才落库。

因此新机器人默认是「唤醒词关闭、空」。本次改为创建即落库默认启用「小护小护」。

## 状态

已完成

## 涉及范围

### 后端

唯一机器人创建入口为 `RobotService.create`（全仓库仅此一处构造 `Robot(...)`），三个文件：

- `backend/database/models/business/robot_voice_config.py`：新增模块级常量（单一真源）
  - `DEFAULT_WAKE_WORD_ENABLED = True`
  - `DEFAULT_WAKE_WORD = "小护小护"`
  - `DEFAULT_TTS_VOICE = "female"` / `DEFAULT_TTS_SPEED = 1.0` / `DEFAULT_TTS_VOLUME = 80`
- `backend/modules/robot/services/robot_service.py`：
  - 导入上述常量
  - `create()` 在 `db.add(status_record)` 之后、`commit` 之前，追加创建 `RobotVoiceConfig(robot_id=..., wake_word_enabled=True, wake_word="小护小护", tts_voice="female", tts_speed=1.0, tts_volume=80)`
- `backend/modules/robot/services/robot_config_service.py`：
  - 导入上述常量
  - `get_voice_config()` 的兜底对象由 `wake_word_enabled=False, wake_word=""` 改为常量值（启用 +「小护小护」），保证「无配置行」的旧机器人也能拿到一致默认值

### 前端

无改动。机器人新增/编辑表单（`robot-operate-drawer.vue`）本就不含唤醒词；唤醒词在「参数配置→语音合成」配置。

## 关键业务规则

- 唤醒词启用时，schema 校验长度 4-6 字（`RobotVoiceConfigSchema.validate_wake_word`）。「小护小护」= 4 字，合法。
- 创建机器人时**不触发 gRPC 推送**（沿用 create 原本零推送的语义；机器人创建时通常离线）。默认配置落库后，仍由用户后续在语音合成页保存（`save_voice_config` 的字段变化检测）触发 `NotifyWakeWordChanged` 推送给 agent。
- 软删除联动已覆盖：`RobotService.delete` 本就会软删 `RobotVoiceConfig`，无需额外处理。

## 约束与备注

- 无 DB 迁移：`robot_voice_config` 表已存在，仅运行时多写一行。
- 兜底默认（`get_voice_config`）一并改为启用「小护小护」：使「默认唤醒词」在全系统只有一个定义，避免「创建默认」与「读取兜底默认」两套值漂移。存量未保存过语音配置的旧机器人，打开语音合成页会显示启用「小护小护」，保存后才真正落库。
- 验证手段：`python -m py_compile` 三个文件均通过（项目约定前端走 typecheck，后端无统一校验命令时用 py_compile 兜底）。

## 相关文件

- `backend/database/models/business/robot_voice_config.py`
- `backend/modules/robot/services/robot_service.py`
- `backend/modules/robot/services/robot_config_service.py`

## 相关历史记忆

- [2026-06-24 voice.proto 拆分为唤醒词 + TTS 两个 RPC](./2026-06-24_voice-proto-split-wakeword-tts.md)（唤醒词字段语义、推送 RPC）
- [2026-06-25 参数配置 gRPC 调用从 robot.grpc_config 取地址](./2026-06-25_param-config-grpc-from-robot.md)（唤醒词走 middleware target）
- [2026-06-11 机器人配置迁移修复](./2026-06-11_robot-config-migration-fix.md)（robot_voice_config 表结构）

## 记录日期

2026-06-30
