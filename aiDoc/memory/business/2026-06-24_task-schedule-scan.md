# 定时扫描调度任务并自动启动/恢复执行

**日期**: 2026-06-24
**提出者**: 用户

## 需求描述

增加一个每分钟执行一次的定时任务，扫描所有"配置了定时调度（schedule_enabled=True）且处于启用状态（enabled=True）"的任务。若任务命中调度时间，则：
- 若该任务在执行记录表中已有 paused 状态的执行 → 批量恢复
- 若没有任何活跃执行（running/paused/pending）→ 新建执行（同"启动任务"按钮逻辑一致）

## 状态

已完成

## 涉及范围

### 后端

- 新增 `backend/modules/task/tasks/__init__.py`
- 新增 `backend/modules/task/tasks/scan_scheduled_tasks.py`（@scheduled_task 注册，cron `* * * * *`）
- 修改 `backend/main.py`：在调度器启动前 `import modules.task.tasks.scan_scheduled_tasks` 触发装饰器注册
- 复用现有 `TaskExecutionRecordService.start_or_resume_execution`（source=`platform_schedule`）
- 由 `seed_scheduler` 自动将装饰器注册的任务同步到 `sys_scheduled_task` 表

### 前端

无变更。

## 关键业务规则

### 调度命中判断 `_is_schedule_due`

1. 必须有 `schedule_start_time`，且其 `HH:MM` == 当前 `HH:MM`（精确到分钟）
2. 满足条件 1 后：
   - 若 `schedule_repeat_cycle` 非空：当前星期（`mon`~`sun`）必须在 cycle 列表中
   - 否则若 `schedule_date` 非空：日期必须等于今天
   - 都为空：不命中

### 去重保证

- cron 每分钟触发一次，每个 `schedule_start_time` 在一天内只匹配一分钟，因此同一调度时间点天然只触发一次
- 调度任务自身设置 `concurrent_policy="skip"` + `is_system=True`
- `start_or_resume_execution` 内部已处理 paused→resume / 否则 create 的去重

### source 取值

- 调度触发的执行记录 `source` 字段统一为 `platform_schedule`（与 schema 注释中定义的三种 source 一致：`platform_schedule/voice_trigger/manual`）

### 失败隔离

- 每个命中的 task 单独开 session 处理，单个任务失败不影响其他任务
- 单任务失败计入 `stats.failed`，整体扫描不中断

## 约束与备注

- 不引入新的依赖表/字段，完全复用 task.schedule_* 和 task_execution_record 表
- 不修改前端，仅在调度端到端打通自动触发链路
- 时区使用 `database.utils.timezone.timezone`（默认 `Asia/Shanghai`）
- `expire_on_commit=False`，session 内多次 commit 安全，无需手工管理事务

## 相关文件

- [backend/modules/task/tasks/scan_scheduled_tasks.py](backend/modules/task/tasks/scan_scheduled_tasks.py)
- [backend/modules/task/tasks/__init__.py](backend/modules/task/tasks/__init__.py)
- [backend/main.py](backend/main.py)
- [backend/modules/task/services/task_execution_record_service.py](backend/modules/task/services/task_execution_record_service.py)
- [backend/modules/scheduler/core/registry.py](backend/modules/scheduler/core/registry.py)
- [backend/modules/scheduler/core/scheduler.py](backend/modules/scheduler/core/scheduler.py)

## 关键设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 时间匹配方式 | schedule_start_time 精确到分钟 + repeat_cycle/date 判断 | 用户明确选择"按调度时间匹配（推荐）" |
| 去重策略 | 每分钟匹配一次，cron 本身就是去重粒度 | 用户明确选择"按调度时间窗口去重（推荐）" |
| 启动入口 | 复用 `start_or_resume_execution` | 与"启动任务"按钮逻辑完全一致 |
| source 字段 | `platform_schedule` | 与 schema 注释保持一致，便于前端区分调度触发 |
| 注册方式 | `@scheduled_task` 装饰器 + main.py 导入 | 沿用项目现有调度注册模式（参考 `modules/scene/tasks/sync_map_version.py`）|
| Session 管理 | 扫描阶段一个 session，每个命中任务独立 session | 避免单个任务失败影响整体扫描，且 service 内部已 commit |
