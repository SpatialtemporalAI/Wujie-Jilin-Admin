# 历史任务列表按结束时间倒序

## 需求描述

任务管理「历史任务」Tab 的列表默认排序由按 `id` 倒序，改为按**结束时间 `finish_time` 倒序**，让最近结束的任务排在最前。

## 状态

已完成

## 涉及范围

### 后端

- `backend/modules/task/services/task_execution_record_service.py`：`TaskExecutionRecordService.build_history_query()` 末尾 `order_by` 由 `TaskExecutionRecord.id.desc()` 改为 `TaskExecutionRecord.finish_time.desc().nulls_last()`。

### 前端

无改动（前端未传排序参数，排序完全由后端 `build_history_query` 决定）。

## 约束与备注

- 仅作用于**历史任务**列表（`build_history_query`，查询 completed/failed/cancelled 三种状态）；**活跃任务**列表 `build_active_query` 仍按 `id.desc()`，本次未改。
- `nulls_last()`：历史任务里 failed 等状态可能未记录 `finish_time`，PostgreSQL `DESC` 默认 NULLS FIRST 会把空值排到顶部，加 `nulls_last()` 让空值落到列表末尾。数据库为 PostgreSQL，原生支持该方法。
- `build_history_query` 仅产出已排序的 Select，分页仍走共享 `get_paginated_results`，不影响分页结构。

## 相关文件

- `backend/modules/task/services/task_execution_record_service.py`
- `backend/database/models/business/task_execution_record.py`（`finish_time` 字段，第 90-92 行）
- `frontend/src/views/task/modules/task-history-tab.vue`（仅展示，无需改动）

## 记录日期

2026-07-07
