# 修复分页 count 恒返回 1（操作日志等纯实体查询页）

## 需求描述

操作日志查询返回 `total=1`（实际远不止 1 条），导致分页只有 1 页、表格仅显示 1 行。

## 根因（关键）

`get_paginated_results` 等分页处用 `base_query.with_only_columns(func.count()).order_by(None)`
生成计数 SQL。在 **SQLAlchemy 2.0** 中，`with_only_columns` 默认 `maintain_column_froms=False`，
会**丢弃仅由被替换列（实体列）派生的 FROM**。

- 当 `base_query` 是 `select(Entity)`（纯实体查询，无显式 join）时，FROM 完全由实体列派生 →
  被丢弃 → 计数 SQL 退化为 `SELECT count(*)`（**无 FROM**）。
- PostgreSQL 中无 FROM 的 `SELECT count(*)` 恒返回一行、值为 `1` → `total` 恒为 1。

经实测编译确认：
```
修复前：SELECT count(*) AS count_1            ← 无 FROM，PG 返回 1
修复后：SELECT count(*) AS count_1 FROM sys_operation_log
```

### 为什么只有部分页面中招

带**显式 `.join()`** 的查询（user/task/notice）FROM 由 join 显式提供、不被丢弃，计数正确；
只有**纯实体 select** 的列表页中招：操作日志、登录日志、字典、角色、场景地图、场景分组、
机器人/型号/事件日志、商户、配置、文件、IP 黑名单、调度任务/日志等（用户只注意到操作日志）。

> 这是 SA 1.4 → 2.0 的经典迁移坑：1.4 默认保留 FROM，2.0 改为默认丢弃，旧的计数写法静默失效。

## 状态

已完成

## 涉及范围

三处同一模式统一加 `maintain_column_froms=True`：

- `backend/app/models/common/page.py` — `get_paginated_results`（共享分页助手，影响绝大多数列表接口）
- `backend/modules/scene/services/scene_map_service.py` — `get_list_with_group_name` 计数
- `backend/modules/scene/services/scene_group_service.py` — `get_list` 计数

```python
count_query = base_query.with_only_columns(
    func.count(), maintain_column_froms=True
).order_by(None)
```

## 关键决策

- 选 `maintain_column_froms=True` 而非 `select(count()).select_from(query.subquery())`：
  前者生成 `SELECT count(*) FROM tbl WHERE ...`（含 join 时保留 join），SQL 干净；
  后者恒套子查询、较重。当前所有分页调用方均为「纯实体 select」或「实体 + join」，
  两种情况 `maintain_column_froms=True` 均已实测生成正确 SQL。
- 未改 `data_query`（数据查询本就正确，仅 count 错）。
- 带 `group_by` 的查询（task_service 点位计数、monitor 统计）不经过 `get_paginated_results`，
  不受影响；若未来分页处出现 `group_by`/`distinct`，应改用 subquery 计数法。

## 验证方案

- 实测编译：纯实体 select 与 join select 两种 count SQL 均含正确 FROM（见根因）。
- `python -m py_compile` 三个文件通过。
- 端到端：操作日志页 `total` 应返回真实条数、分页恢复正常（纯实体查询的其它列表页同步恢复）。

## 相关文件

- `backend/app/models/common/page.py`
- `backend/modules/scene/services/scene_map_service.py`
- `backend/modules/scene/services/scene_group_service.py`

## 记录日期

2026-07-07
