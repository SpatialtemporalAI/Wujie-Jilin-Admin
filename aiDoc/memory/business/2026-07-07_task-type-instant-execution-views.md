# 任务执行/历史列表与执行详情补齐「即时」任务类型

## 需求描述

承接 [2026-06 任务类型新增「即时」(instant)](./2026-07-06_task-type-instant.md)：上次只改了任务管理主页筛选与表格，执行列表、历史列表表格及执行详情抽屉的 `task_type` 展示未补齐（`instant` 会回退为 `-`）。本次补齐这三处，使 `instant` 正确显示为「即时」并带专属 NTag 颜色。

## 状态

已完成

## 涉及范围

### 后端

无改动。

### 前端

统一采用上次 `task-list-tab.vue` 的写法：`taskTypeLabel`（patrol=巡逻 / broadcast=播报 / instant=即时）+ `taskTypeTagType`（patrol=info / broadcast=success / instant=warning，未知回退 `default`）。

- `frontend/src/views/task/modules/task-history-tab.vue`（历史列表表格）
  - `taskTypeLabel` 追加 `instant: '即时'`。
  - 新增 `taskTypeTagType`（类型沿用本文件 `statusColorMap` 的 `NaiveUI.ThemeColor`）。
  - 「任务类型」列 NTag `type` 由 `taskType === 'patrol' ? 'info' : 'success'` 改为 `taskTypeTagType[taskType] || 'default'`。
- `frontend/src/views/task/modules/task-execution-tab.vue`（执行列表表格）
  - 新增 `taskTypeLabel` + `taskTypeTagType`（本文件原先无此 map，标签用内联三元）。
  - 「任务类型」列由内联三元 `taskType === 'patrol' ? '巡逻' : taskType === 'broadcast' ? '播报' : '-'` 改为查表 `taskTypeLabel[taskType] || taskType || '-'`，NTag `type` 同样查 `taskTypeTagType`。
- `frontend/src/views/task/modules/task-detail-drawer.vue`（执行详情抽屉）
  - `taskTypeLabel` 追加 `instant: '即时'`。
  - 该处为 NDescriptions 纯文本展示（非 NTag），第 106 行 `taskTypeLabel[task_type] || task_type || '-'` 查表逻辑本就支持，无需颜色 map。

## 约束与备注

- 三处的 `task_type` 取值均来自执行记录快照 `task_definition.task_type`（不是任务主表的 `task_type`），与列表行 `row.task_definition?.task_type` 一致。
- 颜色 map 在 `task-history-tab` / `task-execution-tab` 用本文件既有的 `NaiveUI.ThemeColor`；`task-list-tab` 用的是 `import('naive-ui').TagProps['type']`，两者等价，按各文件现有风格就近一致即可。
- 详情抽屉的时间线区块仍按 `task_type === 'patrol'` 判断是否渲染巡逻点位时间线，`instant` 不渲染时间线（即时任务无巡逻点位），符合预期，未改动。
- 新增/编辑抽屉 `task-operate-drawer.vue` 的单选仍是 巡逻/播报，不在本次范围。

## 相关文件

- `frontend/src/views/task/modules/task-history-tab.vue`
- `frontend/src/views/task/modules/task-execution-tab.vue`
- `frontend/src/views/task/modules/task-detail-drawer.vue`
- 参考：`frontend/src/views/task/modules/task-list-tab.vue`（上次已改）

## 记录日期

2026-07-07
