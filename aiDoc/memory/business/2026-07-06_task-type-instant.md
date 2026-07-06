# 任务类型新增「即时」(instant)

## 需求描述

任务管理列表的**筛选**与**表格展示**中，任务类型新增「即时」一项，对应 key 为 `instant`。

## 状态

已完成

## 涉及范围

### 后端

无改动（本次仅前端筛选下拉与表格展示）。

### 前端

- `frontend/src/typings/api/task.d.ts`：`Api.Task.TaskType` 联合类型追加 `'instant'`（`'patrol' | 'broadcast' | 'instant'`）。
- `frontend/src/views/task/modules/task-search.vue`：筛选下拉 `taskTypeOptions` 追加 `{ label: '即时', value: 'instant' }`。
- `frontend/src/views/task/modules/task-list-tab.vue`：
  - `taskTypeLabel` 追加 `instant: '即时'`。
  - 新增 `taskTypeTagType` 颜色映射（patrol=info / broadcast=success / instant=warning），表格「任务类型」列 NTag 的 `type` 由原 `patrol ? 'info' : 'success'` 三元改为查表，未知类型回退 `default`。

## 约束与备注

- 本次范围仅限任务管理主页的筛选与表格列，**不动**新增/编辑抽屉 `task-operate-drawer.vue`（其单选仍为 巡逻/播报）。
- 历史记录 tab / 执行记录 tab / 详情抽屉中的 `task_type` 展示未改动：其标签使用 `taskType === 'patrol' ? '巡逻' : taskType === 'broadcast' ? '播报' : '-'` 形式，`instant` 会回退为 `-`；如后续这些视图也要显示「即时」，需同步补齐。
- 即时任务的创建来源、后端是否落库该枚举由其它流程决定，本次只保证前端能筛选与展示。

## 相关文件

- `frontend/src/typings/api/task.d.ts`
- `frontend/src/views/task/modules/task-search.vue`
- `frontend/src/views/task/modules/task-list-tab.vue`

## 记录日期

2026-07-06
