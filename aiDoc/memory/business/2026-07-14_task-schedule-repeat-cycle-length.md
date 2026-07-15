# 任务管理：重复周期全选 7 天报「字段长度不够」

## 需求描述

任务管理新增/编辑任务，「重复周期」勾选全部 7 天（周一~周日）后提交报错，用户判断为字段长度不够。

## 根因

- 0004 建表时 `task.schedule_repeat_cycle` 列为 `String(20)`（当时语义为 none/daily/weekly/monthly）。
- 后业务改为「逗号分隔的星期值」`mon,tue,wed,thu,fri,sat,sun`，全选 7 天 = 27 字符。
- 模型 `database/models/business/task.py` 已改为 `String(100)`，但**未补 ALTER 迁移**，DB 实际仍为 `varchar(20)` → 27 > 20，PG 抛 `value too long for type character varying(20)`。
- 前端 `frontend/src/views/task/modules/task-operate-drawer.vue` 提交时 `schedule_repeat_cycles.join(',')`，无长度截断，故直接顶到 DB 上限。

## 关键实现

- 新建迁移 `backend/database/alembic/versions/0043_task_repeat_cycle_len.py`：`op.alter_column('task','schedule_repeat_cycle', String(20)→String(100))`，同步 comment。`down_revision = "06544a089658"`（当时的单 head，链序 0042 → 06544a089658 → 0043）。
- 模型层无需改（已是 String(100)）。

## 踩坑：revision id 超长

- 初版 revision id 用 `0043_task_schedule_repeat_cycle_len`（35 字符），迁移 ALTER 成功，但写 `alembic_version.version_num` 时报 `value too long for type character varying(32)` —— **alembic 默认 version_num 列为 varchar(32)**，revision id 必须 ≤32 字符。
- PG DDL 事务化，version 写入失败连带 ALTER 回滚，DB 回到干净态（仍 varchar(20)、version 仍 `06544a089658`）。
- 改 revision id 为 `0043_task_repeat_cycle_len`（26 字符）后重新 `alembic upgrade head` 通过。命名约定：`00XX_<简短名>`，简短名需为 revision 总长留足 ≤32 余量。

## 约束与备注

- 加宽 varchar 属元数据级变更，无数据丢失、无需 USING；未走「新建并存表」（[[feedback-dual-table-migration]] 针对「大改」，列加宽不适用）。
- **需执行 `alembic upgrade head` 并重启 FastAPI 生效**；仅改模型不跑迁移无效。
- 既有 `06544a089658_drop_task_execution_record_task_id_fk` 用哈希 revision（非 00XX 命名），新增迁移务必先 `alembic heads` 确认当前单 head 再决定 `down_revision`，避免分叉多 head。

## 相关文件

- 后端：`backend/database/alembic/versions/0043_task_schedule_repeat_cycle_len.py`（新建）、`backend/database/models/business/task.py`（已是 String(100)，未改）

## 记录日期

2026-07-14
