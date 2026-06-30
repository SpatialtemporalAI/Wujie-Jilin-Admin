# 移除本服务定时调度 + 启动任务改为纯 gRPC

**日期**: 2026-06-29
**提出者**: 用户

## 需求描述

1. **去除任务管理的定时任务（调度执行）**：定时调度改由**外部程序负责**，本服务不再扫描/触发。仅关闭本服务中"定时任务的处理"，`Task.schedule_*` 字段**保留**（供外部调度程序读取）。
2. **启动任务只调用 gRPC，不写 execution_record**：任务管理「启动」与 OpenAPI（`goto_point` / `navigate_route` / `execute_task`）的启动入口，都改为**只下发 gRPC `run_now`**，不再向 `task_execution_record` 表 INSERT。

## 状态

已完成

## 涉及范围

### 需求 1：关闭定时调度处理（字段保留）

- 删除 `backend/modules/task/tasks/scan_scheduled_tasks.py` 及空目录 `backend/modules/task/tasks/`（每分钟扫描 `schedule_enabled+enabled` 任务的 `@scheduled_task`）。
- `backend/main.py`：移除 lifespan 中 `import modules.task.tasks.scan_scheduled_tasks`（装饰器不再注册）。
- 新增 `backend/database/alembic/versions/0037_remove_task_schedule_scan_job.py`：幂等软删除 `sys_scheduled_task` 中 `task_key='task.scan_scheduled_tasks'` 的系统任务行（`deleted_at=NOW(), status=0`），避免 APScheduler 启动后每分钟加载已删除函数报错。
- **保留**：`Task` 模型 / `TaskCreate` / `TaskUpdate` / `TaskResponseData` 的 `schedule_*` 字段、前端创建/编辑/列表的定时配置 UI、`task.d.ts` 类型——外部调度程序仍依赖这些字段。

### 需求 2：启动任务改为纯 gRPC（任务管理 + OpenAPI）

- `backend/modules/task/services/task_execution_record_service.py`：
  - `start_execution(db, task_id, robot_ids)` 重写为**纯 gRPC**：仅校验任务存在 → `TaskConfigClient.broadcast_task_changed(task_id, "run_now", robot_ids)`，返回 `{total, success_count, failed_count}`。**不再** `db.add(TaskExecutionRecord)`、不再构建 `task_definition`/`progress` 快照。
  - 删除 `start_or_resume_execution`（其 resume 分支也是 execution_record 写操作，与"只调用 gRPC"冲突）。
  - 删除随之失去调用方的私有助手 `_build_task_definition` / `_init_progress`，并清理 service 内不再使用的 import（`TaskPoint/Robot/SceneMap/SysUser/selectinload` 及 5 个 snapshot schema）。snapshot schema 仍被响应模型使用，**schemas 文件不动**。
- `backend/modules/task/endpoints/task_execution_record.py`：
  - `/{task_id}/start` 与 `/start-or-resume/{task_id}` 两个启动接口均改调 `start_execution`，`response_model` 改为 `ResponseModel`（不再返回 record），msg 固定「任务已启动」。前端契约（`fetchStartOrResumeExecution` 发 `{robot_ids, source}`、看 `error`）不变。
- `backend/modules/merchant/services/openapi_service.py`：
  - `goto_point` / `navigate_route`：去掉 `source=`，响应 `data` 去掉 `record_id`，只留 `{task_id}`。
  - `execute_task`：改调 `start_execution`，msg 固定「任务已启动」，`data={task_id, action:"started"}`（不再区分 resumed）。
- `aiDoc/frontend-backend/boundary.md`：同步 `/openapi/v1/goto_point`、`/execute_task` 行为说明。

## 关键决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 定时调度归属 | 移交外部程序，本服务只删扫描器、保留字段 | 用户明确"由别的程序负责调度"，字段仍需对外提供 |
| `schedule_*` DB 列 | 保留（不写 DROP 迁移） | 避免破坏式表结构变更；外部程序仍读取 |
| 启动范围 | 任务管理 + OpenAPI 全改纯 gRPC | 用户确认两条入口都不再写 execution_record |
| `start_or_resume_execution` | 整体删除 | resume 分支写 execution_record，与"只调用 gRPC"冲突；调用方（endpoint + openapi）改调 `start_execution` |
| stale 调度行 | 0037 迁移软删除 | 否则 APScheduler 每分钟尝试加载已删函数报错 |

## 范围外 / 影响

- 启动不再写 `task_execution_record` 后，平台/OpenAPI 触发的执行不再产生记录 → 任务列表 `active_execution_count`（驱动「暂停」按钮显隐）对这类任务常为 0，任务管理「暂停」按钮会基本不再出现；OpenAPI 的 `pause/resume/stop_task` 依赖 `_get_active_record` 查活跃记录，也将无记录可操作。`pause/resume/stop` 及执行记录查询接口本身**保留不动**（本次未要求移除）。如需一并清理，另行处理。
- `TaskExecutionSource.platform_schedule` 枚举值随扫描器删除成为死值，仅字符串注释/前端 label，保留无害。

## 相关文件

- [backend/main.py](backend/main.py)
- [backend/database/alembic/versions/0037_remove_task_schedule_scan_job.py](backend/database/alembic/versions/0037_remove_task_schedule_scan_job.py)
- [backend/modules/task/services/task_execution_record_service.py](backend/modules/task/services/task_execution_record_service.py)
- [backend/modules/task/endpoints/task_execution_record.py](backend/modules/task/endpoints/task_execution_record.py)
- [backend/modules/merchant/services/openapi_service.py](backend/modules/merchant/services/openapi_service.py)
- [aiDoc/frontend-backend/boundary.md](aiDoc/frontend-backend/boundary.md)

## 相关历史记忆

- [2026-06-24 定时扫描调度任务](./2026-06-24_task-schedule-scan.md)（本次移除其扫描器）
- [2026-06-26 任务执行 gRPC 推送补全](./2026-06-26_task-execution-grpc-push.md)（本次将 start 路径简化为仅 gRPC）
