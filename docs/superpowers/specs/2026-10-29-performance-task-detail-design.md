# 表演任务执行详情展示设计

## 目标

任务管理的执行详情抽屉在任务类型为 `performance` 时，展示任务内容及各套表演步骤，与现有巡逻点位、播报步骤的展示方式保持一致。

## 实现范围

- `frontend/src/views/task/modules/task-detail-drawer.vue`：渲染详情接口返回的 `detail.task_definition.performance_steps`，前端 API 类型保持不变。
- `backend/modules/task/schemas/task_execution_record.py`：兼容历史执行快照，将机器人端 `sets` 结构规范化为 `performance_steps`；已有新格式优先，不读取当前任务配置覆盖历史快照。

## 展示设计

- 使用 `NDivider` 添加“表演内容”区域，使用 `NTimeline` 按数组顺序渲染步骤，标题为“第 N 套”。
- 每一步展示 `action` 对应的表演动作、`music` 对应的背景音乐、`play_count` 对应的播放次数。
- 背景音乐为空时显示“无”。
- `interval` 仅在非最后一步且值不为 `null` 或 `undefined` 时显示为“与下一套间隔: N 秒”。
- 加载表演任务详情后并行获取表演动作和音乐选项，将接口标识映射为中文名称；其他任务类型不请求这些选项。
- 选项不存在或选项接口请求失败时，显示步骤中的原始标识；步骤数据仍可正常展示。
- 表演步骤复用巡逻的 `pointStatusType(index)` 和 `progress.points_status`：已完成显示绿色、失败显示红色，其他状态沿用巡逻默认样式，无需新增后端进度字段。

## 验证

- 执行前端 TypeScript 类型检查。
- 检查表演任务详情的多步骤、无音乐、末步间隔隐藏及选项加载失败降级行为。
- 使用真实历史记录核对表演步骤的完成、失败及其他进度状态与 `points_status` 一致。
- 确认巡逻和播报任务现有详情展示不受影响。
