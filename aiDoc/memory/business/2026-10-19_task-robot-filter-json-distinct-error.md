# 修复任务管理按机器人筛选报错

## 需求描述

任务管理列表按「机器人」筛选时接口报错（500）。根因：`TaskService.build_query` 在 robot_id 过滤时使用 join + `distinct()`，`SELECT DISTINCT task.*` 要求对全列做相等比较；2026-09-17 迁移 0014 新增的 `task.performance_steps` 为 PostgreSQL `json` 类型（无相等操作符），触发 `could not identify an equality operator for type json`。

修复：robot_id 过滤改为 EXISTS 子查询（关联表主键 `(task_id, robot_id)` 保证单机器人过滤不会重复，无需 distinct），并保留 Robot 未软删校验。

## 状态

已完成

## 涉及范围

### 后端

- `modules/task/services/task_service.py`：`build_query` 的 robot_id 分支改为 EXISTS 子查询

### 前端

- 无改动（筛选参数契约不变）

## 约束与备注

- `task.broadcast_steps` 在库中已是 `jsonb`，`performance_steps` 仍为 `json`；如后续有按 task 全列 DISTINCT/GROUP BY 的需求，建议加迁移统一为 `jsonb`
- 已在开发库（PostgreSQL 16）实测：带 robot_id 的分页查询 total 与关联表去重计数一致

## 相关文件

- `backend/modules/task/services/task_service.py`
- `backend/database/alembic/versions/0014_add_performance_steps_and_meeting_mode.py`

## 记录日期

2026-10-19
