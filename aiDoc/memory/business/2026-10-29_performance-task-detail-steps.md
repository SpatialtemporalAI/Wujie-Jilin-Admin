# 任务管理 · 表演任务执行详情展示任务内容和步骤

**日期**: 2026-10-29
**提出者**: 用户

## 需求概述

任务管理的表演类型执行详情需要参考巡逻、播报任务，展示任务内容和步骤。

## 关键决策

- 前端直接渲染执行详情接口的 `detail.task_definition.performance_steps`，API 类型无需调整。
- 历史执行快照的表演步骤实际保存在 `sets`（`action_id / play_count / music / interval_seconds`），后端 `TaskDefinitionSnapshot` 在响应校验时将其规范化为 `performance_steps`；已有新格式优先，不使用当前任务配置覆盖历史快照。
- 使用 `NTimeline` 按顺序展示“第 N 套”，每套包含表演动作、背景音乐、播放次数；无音乐显示“无”。
- 非最后一套且间隔有效时展示“与下一套间隔”，最后一套即使历史快照残留间隔也不展示。
- 仅表演任务加载动作和音乐选项，将标识映射为中文名称；选项缺失或请求失败时回退显示原始标识。
- 表演步骤复用巡逻的 `pointStatusType(index)` 和 `progress.points_status`，已完成显示绿色、失败显示红色，其他状态沿用默认样式。
- 巡逻、播报及其他任务类型的展示逻辑保持不变。

## 实现范围

- `frontend/src/views/task/modules/task-detail-drawer.vue`：补充表演动作/音乐名称映射、表演内容时间线、通用步骤间隔判断和步骤执行状态。
- `backend/modules/task/schemas/task_execution_record.py`：将历史快照 `sets` 规范化为 `performance_steps`，保留已有新格式。

## 验证

- `pnpm typecheck`：通过。
- `pnpm exec eslint src/views/task/modules/task-detail-drawer.vue`：通过。
- `pnpm build`：通过。
- `python -m py_compile modules/task/schemas/task_execution_record.py`：通过。
- 使用真实历史执行记录校验详情响应模型：多套动作、上传/预设音乐、播放次数和间隔均能正确输出；新格式快照保持不变；进度快照包含每套状态供时间线复用。
- 浏览器预览可正常打开登录页；因没有系统登录状态，未完成任务管理实际数据页面的手动验证。
