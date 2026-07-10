---
date: 2026-07-10
type: business
---

# 取消任务执行记录 task_id 外键约束

## 需求

取消 `task_execution_record` 表 `task_id` 字段对 `task.id` 的外键约束，保留字段本身及索引。

## 背景

`task_execution_record` 定位为独立执行记录，通过 `task_definition` JSON 保存任务快照，本就不应强依赖 `task` 表。
0026 迁移曾为 `task_id` 添加 `ForeignKey("task.id", ondelete="SET NULL")`，导致删除任务时相关执行记录的 `task_id` 被清空。
业务上需要保留原始来源任务 ID，因此取消外键约束，使 `task_id` 成为普通可空字段。

## 实现

- 模型 `backend/database/models/business/task_execution_record.py`
  - 移除 `task_id` 字段的 `ForeignKey("task.id", ondelete="SET NULL")` 定义
- Alembic 环境 `backend/database/alembic/env.py`
  - 补充导入 `models.business.task_execution_record`，修复 autogenerate 模型覆盖
- 迁移 `backend/database/alembic/versions/06544a089658_drop_task_execution_record_task_id_fk.py`
  - `upgrade`: `drop_constraint('task_execution_record_task_id_fkey', 'task_execution_record', type_='foreignkey')`
  - `downgrade`: 重新创建外键 `create_foreign_key(..., ondelete='SET NULL')`

## 影响范围

- 仅数据库层约束变更，代码中无 `TaskExecutionRecord.task` relationship，服务层仅使用 `record.task_id` 整数值，无需改动。
- 保留 `ix_task_execution_record_task_id` 索引，查询性能不变。
