# task 表 task_type 注释补充表演类型枚举

## 需求描述

数据库表 `task` 的 `task_type` 列注释仍停留在 `patrol-巡逻, broadcast-播报`，0014 迁移引入表演任务后未同步枚举说明，需补充 `performance-表演`。

## 状态

已完成

## 涉及范围

### 后端

- ORM 模型列注释：`database/models/business/task.py` 的 `Task.task_type` comment
- 新增迁移 `0015_update_task_type_comment.py`：`op.alter_column` 仅更新列注释，不改类型与存量数据

### 前端

无

## 约束与备注

- 不改历史迁移 0001/0014，保持迁移链不可变，新装库按 0001→0015 顺序执行后注释亦正确
- 商户开放 API（`modules/merchant/schemas/openapi.py` 的 `TaskTypeField`）有意仅放行 patrol/broadcast，本次未扩展，如后续要对商户开放表演任务需同步放开该校验

## 相关文件

- `backend/database/models/business/task.py`
- `backend/database/alembic/versions/0015_update_task_type_comment.py`

## 记录日期

2026-10-15
