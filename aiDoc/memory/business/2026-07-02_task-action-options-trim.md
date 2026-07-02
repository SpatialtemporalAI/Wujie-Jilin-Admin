# 任务运控动作下拉精简（移除击掌/拥抱/飞吻/动感光波）

## 需求描述

任务管理「任务列表」新增/编辑巡逻任务时，点位运控动作下拉选项移除以下 6 项：

| 中文 | value | 移除原因 |
| --- | --- | --- |
| 击掌 | `high_five` | 用户要求移除 |
| 拥抱 | `hug` | 用户要求移除 |
| 左手飞吻 | `left_kiss` | 属「飞吻」 |
| 右手飞吻 | `right_kiss` | 属「飞吻」 |
| 双手飞吻 | `two_hand_kiss` | 属「飞吻」 |
| 动感光波 | `x_ray` | 用户要求移除 |

保留下拉可选项 8 项：`shake_hand`(握手) / `high_wave`(高举挥手) / `clap`(鼓掌) / `face_wave`(挥手) / `hands_up`(平举双手) / `right_hand_up`(平举右手) / `reject`(拒绝) / `no`(无动作)。

## 状态

已完成

## 涉及范围

### 前端

- `frontend/src/views/task/modules/task-operate-drawer.vue`
  - `actionOptions`（L37）：移除上表 6 项，剩余 8 项保持原相对顺序

### 保留不改（历史数据兼容）

- `frontend/src/views/task/modules/task-detail-drawer.vue`
  - `actionLabel`（L38）：**保留**被移除 6 项的中文标签，历史执行快照仍能正确显示
- `frontend/src/typings/api/task.d.ts`
  - `TaskAction`（L12）：**保留** 14 项联合类型不动（超集，兼容历史数据类型）
- `backend/modules/task/schemas/task.py`
  - `TaskActionItem.action`（L37）：**保留** description 列出全部合法值不动；仍 `Field(...)` 必填、`max_length=20`，字符串透传到 gRPC 与执行快照

## 约束与备注

- **仅改下拉、不改类型与后端**：被移除的 action 值仍是合法的透传字符串，老任务/历史快照含这些值时不报错，详情抽屉仍显示中文标签。
- **编辑回填**：老任务 action 值若不在新 8 项下拉中，NSelect 显示为空，用户需重新选择新值保存（沿用 [2026-07-01 任务运控动作选项替换为新14项](./2026-07-01_task-action-options-replace.md) 的语义）。
- **DB 无需迁移**：`TaskPoint.actions` 为 `JSON nullable=True`。

## 相关文件

- `frontend/src/views/task/modules/task-operate-drawer.vue`

## 记录日期

2026-07-02
