# gRPC 重试任务置 dead 时 next_retry_at 不能置 NULL

## 需求描述

定时任务 `grpc.retry_failed_pushes` 执行失败：
`null value in column "next_retry_at" of relation "grpc_retry_task" violates not-null constraint`。

任务重试到第 3 次（max_retries）转 dead 时，commit 抛 `NotNullViolationError`，
整个调度任务失败；且因事务回滚，该任务 DB 中 retry_count 仍停在 2，下一分钟
又被扫到、又走同一 dead 路径 → 每分钟失败一次、卡死任务永远标不了 dead。

## 根因

`grpc_retry_task.next_retry_at` 建表即为 `NOT NULL`（迁移 0029 + model 均如此），
但 `_advance_fields` 在 dead 分支显式 `task.next_retry_at = None`，与约束冲突。

另两条 dead 路径（无路由、payload 缺字段）本就不动 `next_retry_at`，一直正常；
只有重试耗尽的 dead 路径置空，是历史遗留不一致。

## 状态

已完成

## 涉及范围

### 后端

- `backend/modules/grpc/retry_service.py`
  - `_advance_fields` dead 分支删除 `task.next_retry_at = None`
  - dead 行保留原 `next_retry_at`（NOT NULL 不变），靠扫描查询的
    `status == "pending"` 过滤排除，不会被重复调度
  - 无需 schema/迁移改动

## 关键决策

### 不改 schema，只删一行

扫描查询：`status == "pending" AND next_retry_at <= now() AND deleted_at IS NULL`，
`status` 是真正的闸门。dead 行的 `next_retry_at` 取何值都不影响调度正确性，
故保留原值即可，无需把列改成 nullable（避免迁移 + 部署协调）。

### 与前序修复的关系

承接 [[2026-06-26_grpc-retry-count-not-advancing]]：那次让三种失败路径统一走
`_advance_fields` 推进 retry_count，使任务能正常走到第 3 次；但 dead 分支的
置空 bug 一直潜伏，直到真有任务连续失败 3 次才暴露。

## 验证

- `python -m py_compile modules/grpc/retry_service.py` 通过
- 存量卡死任务（retry_count 已到 2）：下次扫描重试失败 → _advance_fields
  计数到 3 → 不再置空 → commit 成功 → status=dead，自动解锁

## 相关文件

- `backend/modules/grpc/retry_service.py`
- `backend/database/models/business/grpc_retry_task.py`
- `backend/database/alembic/versions/0029_grpc_retry_task_table.py`

## 记录日期

2026-07-13
