# 导出任务卡死修复：定时兜底生成 + 超时失效（状态同步保留轮询）

## 需求描述

日志导出任务经常**一直停留在「排队中」**。用户要求：

1. 增加异步定时任务进行生成，超时后删除文件并标记导出任务为失效；拆成两个按分钟执行、不允许并发的定时任务。
2. 评估前端轮询同步导出状态是否换成 WebSocket。

## 根因

`export_task_service.py` 的 `submit_task` 用 `asyncio.create_task(_execute_task)` 触发生成，是 fire-and-forget。生产环境 gunicorn 配了 `max-requests=5000`（`backend/start_prod.sh`），worker 会定期回收；任何部署/崩溃/回收都杀死该协程，而 DB 记录永卡 `pending`/`processing`。现有 `try/except` 只捕获协程运行中的异常，捕获不到「整个事件循环被杀」。

## 状态

已完成（后端 + 前端）。

- 后端：4 文件改 + 1 新建任务模块；`py_compile` 通过；项目 venv 真实 import 验证两个 task_key（`admin.recover_stuck_export_tasks`、`admin.expire_timeout_export_tasks`）注册成功。
- 前端：5 文件改；`pnpm typecheck` 本次改动文件无新增报错（既有 `locales/langs` 的 `map-editor` 路由 i18n 报错为 pre-existing，与本次无关，用户选择不修 —— 同 [2026-07-06 导出 Excel](./2026-07-06_log-export-excel.md)）。

## 决策（已与用户确认）

- **生成机制**：保留 `asyncio` 即时触发（正常秒级出结果） + 新增定时兜底（worker 回收后 ~2 分钟内自动捞起）。不移除即时触发。
- **状态同步**：**保留前端 3s 轮询**，不改 WebSocket。理由：`FastAPIConnectionManager`（`core/websocket/connection.py`）是进程内存字典，生产 4 worker 下推送会丢；要可靠推送须额外加 Redis pub/sub 桥接层，对低频导出收益不抵成本。轮询天然多 worker 安全（共享 DB），现状已实现「无 pending 时自动停止」。

## 涉及范围

### 后端

- **新建 `backend/modules/admin/tasks/__init__.py` + `export_task.py`**：两个 `@scheduled_task`，仿 `modules/scene/tasks/sync_map_version.py` / `modules/grpc/tasks/retry_failed_pushes.py` 模式，`cron="* * * * *"`、`concurrent_policy="skip"`、`is_system=True`：
  - `recover_stuck_export_tasks`（task_key=`admin.recover_stuck_export_tasks`，timeout=900）：扫 `status='pending'` 且 `created_at < now-90s`（限 50 条），串行 `await ExportTaskService._execute_task(tid)`。
  - `expire_timeout_export_tasks`（task_key=`admin.expire_timeout_export_tasks`，timeout=120）：扫 `status='processing'` 且 `started_at < now-600s`，删残留文件 + 置 `status='expired'`/`error_message='导出超时已失效'`/`finished_at=now`。
- **改造 `export_task_service.py:_execute_task` 为「原子领取」**：用 `update(SysExportTask).where(id=task_id, status='pending').values(status='processing', started_at=now)`，`rowcount==0` 即放弃。即时触发的 asyncio 路径毫秒级领取，与兜底任务不会撞；多 worker 的兜底任务同时扫到同一 pending 任务时，原子 UPDATE 保证只一个 `rowcount=1`。
- **阈值常量**提到 `export_task_service.py` 顶部：`RECOVER_PENDING_AGE_SECONDS=90`、`EXPORT_TIMEOUT_SECONDS=600`，任务文件 import。
- **`main.py`** 任务 import 区追加 `import modules.admin.tasks.export_task  # noqa: F401`（`seed_scheduler` 自动同步装饰器任务到 `sys_scheduled_task` 表）。
- **`database/models/sys/export_task.py`** `status` 注释加 `expired`（仅注释，无 schema 变更、无迁移）。
- **`export_task_service.py:cleanup_old_tasks`** 状态白名单 `["completed","failed"]` 加 `"expired"`（让超时失效记录 7 天后随清理删除）。

「不允许并发」两层保障：APScheduler `max_instances=1`+`coalesce=True`（`modules/scheduler/core/scheduler.py`）保单 worker 内不并发；原子领取保多 worker 间不重复生成。

### 前端

保留轮询，仅补 `expired` 状态展示（角标 `pendingCount` 不变，只统计 pending/processing）：

- `frontend/src/typings/api/export.d.ts`：`ExportTaskStatus` 加 `'expired'`。
- `frontend/src/layouts/modules/global-header/components/export-center.vue`：`getStatusMeta` 加 `case 'expired'`（error tag + `statusExpired` 文案）。
- `frontend/src/typings/app.d.ts`：i18n Schema `exportCenter` 加 `statusExpired: string`（本项目 I18nKey 基于显式 Schema，新增 key 必须三处同步，否则 vue-tsc 报 I18nKey 不可赋值）。
- `frontend/src/locales/langs/zh-cn.ts`：`statusExpired: '已失效'`。
- `frontend/src/locales/langs/en-us.ts`：`statusExpired: 'Expired'`。

## 约束与备注

- 不动 WebSocket / `FastAPIConnectionManager`，不引入 Redis pub/sub 桥接。
- 不移除 `asyncio.create_task` 即时触发，不改前端轮询间隔/逻辑。
- `expired` 与 `failed` 区分：`expired`=processing 超时被定时任务置失效（可重试=用户重新点导出）；`failed`=`_execute_task` 运行中抛异常。两者都是终态，不自动重试。
- 后端改动需重启 FastAPI 服务才生效；新任务首次启动由 `seed_scheduler` 写入 DB 后加载进 APScheduler。
- 阈值（90s/600s）为模块常量，如需调整改 `export_task_service.py` 顶部（未来可提取到 settings）。

## 相关文件

后端：

- `backend/modules/admin/tasks/export_task.py`（新建）、`backend/modules/admin/tasks/__init__.py`（新建空包）
- `backend/modules/admin/services/sys/export_task_service.py`（原子领取 + 阈值常量 + cleanup 白名单）
- `backend/main.py`（注册 import）
- `backend/database/models/sys/export_task.py`（status 注释）
- 复用（未改）：`backend/modules/scheduler/core/registry.py`、`backend/modules/scheduler/core/scheduler.py`

前端：

- `frontend/src/typings/api/export.d.ts`、`frontend/src/typings/app.d.ts`
- `frontend/src/layouts/modules/global-header/components/export-center.vue`
- `frontend/src/locales/langs/{zh-cn,en-us}.ts`

## 记录日期

2026-07-07
