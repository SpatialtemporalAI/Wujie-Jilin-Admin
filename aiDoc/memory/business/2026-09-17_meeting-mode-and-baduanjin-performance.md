# 吉大二院·二期：会议模式 + 中医养生操表演

## 需求描述

来源：飞书 PRD《吉大二院·二期》（https://vcn10ri2y9ti.feishu.cn/wiki/KfJAwuQ9Hi5lnmkJWXQcnLJCnfg 第三点「功能需求」）。新增两个需求：

1. **会议模式**（模块一 FR-07/08/09）：机器人通过语音指令进入会议模式，持续录音解析上下文、不主动发言；会议中可用唤醒词让机器人发表意见；退出指令退出会议模式。参数配置页新增会议模式区块（仅 4-6 字专属指令配置 + 保存），**系统不提供开关**——开启/关闭仅能通过语音指令控制（用户 2026-10-15 明确）；机器人列表页显示会议模式状态（监听中/未开启）。默认指令：进入「开始会议」、退出「结束会议」。
2. **中医养生操表演**（模块二 FR-10~15）：任务类型扩展新增「表演」，支持预训练八段锦动作编排（最多 3 套、可重复）、背景音乐（仅预设，不做用户上传）、播放次数与套间间隔、定时任务；执行列表支持暂停/停止，历史任务按类型/结果/机器人筛选，结果以「已完成/已失败/已取消」标签区分。

## 状态

开发中

## 涉及范围

### 后端

- `backend/modules/task/`：任务类型扩展 `performance`，表演步骤 `performance_steps`（JSON），预设音乐库列表接口
- `backend/modules/robot/`：会议模式配置接口（指令校验 4-6 字、保存/测试、gRPC 下发占位）
- `backend/database/`（子模块）：`task` 表加 `performance_steps`；`robot_voice_config` 加会议模式字段；迁移 `0014_*.py`

### 前端

- `frontend/src/views/task/`：`TaskType` 加 `performance`，创建/编辑弹窗表演类型 UI（动作编排、预设音乐、播放次数/间隔、定时复用），三个 tab 类型映射同步
- `frontend/src/views/settings/`：新增会议模式 Tab/区块
- `frontend/src/views/robots/`：列表卡片新增会议模式状态 tag
- `frontend/src/service/api/`、`frontend/src/typings/api/`：task / robot-config / robot 契约同步

## 约束与备注

- **用户上传音频功能不做**，音乐库只保留「预设音频」一项（用户明确要求）。
- 表演动作最多 3 套，同一任务可重复相同套动作；播放次数最低 1；套间间隔 0-300 秒。
- 音乐仅支持 mp3/wav、时长 ≤ 4 分钟（本期只做预设，前后端校验逻辑预留给后续上传）。
- 会议模式指令 4-6 字，是否限制「仅中文」PRD 未明确，沿用唤醒词同款校验。
- 会议模式开关系统侧不可控：前端保存时 `meeting_mode_enabled` 置 `undefined` 不提交，后端 schema 默认 `None`、service「传 None 保持原值」；后续由机器人端语音识别结果回写该字段。
- 状态流转：暂停/中断→执行列表「已暂停」；恢复时判断进度、节点处重头开始；取消→历史「已取消」；完成→历史「已完成」。

## 相关文件

- 后端：`backend/modules/task/{endpoints,services,schemas}/`、`backend/modules/robot/{endpoints,services,schemas}/robot_config.py`
- 数据库：`backend/database/models/business/task.py`、`backend/database/models/business/robot_voice_config.py`、`backend/database/alembic/versions/0014_*.py`
- 前端：`frontend/src/views/task/modules/task-operate-drawer.vue`、`task-list-tab.vue`、`task-execution-tab.vue`、`task-history-tab.vue`、`task-search.vue`、`task-detail-drawer.vue`、`frontend/src/views/settings/modules/`、`frontend/src/views/robots/index.vue`、`frontend/src/typings/api/{task,robot-config,robot}.d.ts`、`frontend/src/service/api/{task,robot-config,robot}.ts`

## 记录日期

2026-09-17
