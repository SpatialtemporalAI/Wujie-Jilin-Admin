# 任务运控动作选项替换为新14项

## 需求描述

任务管理「任务列表」新增/编辑巡逻任务时，点位运控动作下拉选项整体替换为机器人真实支持的 14 个动作：

| 中文 | value |
| --- | --- |
| 握手 | `shake_hand` |
| 击掌 | `high_five` |
| 拥抱 | `hug` |
| 高举挥手 | `high_wave` |
| 鼓掌 | `clap` |
| 挥手 | `face_wave` |
| 左手飞吻 | `left_kiss` |
| 平举双手 | `hands_up` |
| 动感光波 | `x_ray` |
| 平举右手 | `right_hand_up` |
| 拒绝 | `reject` |
| 右手飞吻 | `right_kiss` |
| 双手飞吻 | `two_hand_kiss` |
| 无动作 | `no` |

旧 7 项（`shake_hands`/`wave`/`left_hand`/`right_hand`/`bend_no_hands`/`bend_with_hands`/`no`）从下拉移除。注意 `shake_hand`（单数）与旧值 `shake_hands`（复数）拼写不同；`挥手` 由 `wave` 改为 `face_wave`；`no`（无动作）保留。

## 状态

已完成

## 涉及范围

### 前端

- `frontend/src/typings/api/task.d.ts`
  - `TaskAction`（L11）：枚举替换为新 14 项
- `frontend/src/views/task/modules/task-operate-drawer.vue`
  - `actionOptions`（L36）：替换为新 14 项
  - `addAction` 默认 action 仍为 `'no'`，无需改
  - 编辑回填 fallback `'no'` 仍兼容（`no` 仍在列表中）
- `frontend/src/views/task/modules/task-detail-drawer.vue`
  - `actionLabel`（L38）：替换为新 14 项标签，**同时保留**旧值（`shake_hands`/`wave`/`left_hand`/`right_hand`/`bend_no_hands`/`bend_with_hands`/`bow`/`turn`/`wait`/`nod`）中文标签，兼容历史执行快照显示

### 后端

- `backend/modules/task/schemas/task.py`
  - `TaskActionItem.action`（L37）：仅更新 `description` 列出新合法值；仍 `Field(...)` 必填，`max_length=20`（新值最长 `two_hand_kiss`=13、`right_hand_up`=13，不超限）
- `TaskActionSnapshot.action`（`schemas/task_execution_record.py:27`）description 已泛化为「运控动作」，无需改

## 约束与备注

- **单项 action 仍然必填**：列表可为空，但只要添加动作项就必须有值（沿用 [2026-06-26 任务运控动作选项更新](./2026-06-26_task-action-options-update.md) 的语义）。
- **新增动作项默认值**：`'no'`（无动作），不变。
- **DB 无需迁移**：`TaskPoint.actions` 是 `JSON nullable=True`，新枚举值以字符串透传到 gRPC 推送与执行快照，无需改 proto 或客户端。
- **历史数据兼容**：详情抽屉 `actionLabel` 保留旧值中文标签；编辑抽屉里若老任务 action 值不在新选项中，NSelect 显示为空，用户需重新选择新值保存。

## 相关文件

- `frontend/src/typings/api/task.d.ts`
- `frontend/src/views/task/modules/task-operate-drawer.vue`
- `frontend/src/views/task/modules/task-detail-drawer.vue`
- `backend/modules/task/schemas/task.py`

## 记录日期

2026-07-01
