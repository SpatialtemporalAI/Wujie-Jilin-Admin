# 删除废弃 task_execution 表 + 补 task_execution_record JSON 注解

## 需求描述

1. **检查并清理 task_execution 旧表**：2026-06-23 的迁移 `0025_task_execution_record_table` 新建独立 `task_execution_record` 表后，旧 `task_execution` 表按"暂保留"策略一直没清理。本次确认代码侧零引用后，删代码 + drop 物理表。
2. **加强 task_execution_record JSON 字段类型注解**：`task_definition` / `progress` 两个 JSON 字段在 ORM 上只是 `Mapped[Optional[Dict[str, Any]]]`，看不出对应哪个 Pydantic 类。补注释指向 `TaskDefinitionSnapshot` / `ProgressDetail`，纯文档作用，不加运行时校验。

## 状态

已完成

## 涉及范围

### 探查结论

- **task_execution 表确认死代码**：
  - 后端：仅 ORM 模型 / service / endpoint / schema 内部闭环；定时任务 `scan_scheduled_tasks.py` 用的是新 `TaskExecutionRecordService`
  - 前端：`frontend/src/service/api/task.ts` 第 61-120 行的 7 个旧 API 函数零调用，`task-execution-tab.vue` / `task-list-tab.vue` 只 import 新版 `*Record` 函数

### 后端 submodule (`backend/database/`，独立仓库 Wujie-Jilin-Database)

**删除**：
- `backend/database/models/business/task_execution.py`

**修改**：
- `backend/database/models/business/__init__.py` — 移除 `TaskExecution` import + `__all__` 条目
- `backend/database/models/business/task.py` — 移除 `TYPE_CHECKING` 导入 + `Task.executions` relationship
- `backend/database/models/business/task_execution_record.py` — `task_definition` / `progress` 字段补文档注释，指向对应 Pydantic 类

**新建**：
- `backend/database/alembic/versions/0032_drop_task_execution_table.py`
  - `down_revision = "0031_menu_meta_icon_type"`
  - `upgrade()` 执行 `op.drop_table("task_execution")`
  - `downgrade()` 从 `0004_task_tables.py` 抄回完整字段重建

### 后端主仓

**删除**：
- `backend/modules/task/services/task_execution_service.py`
- `backend/modules/task/endpoints/task_execution.py`

**修改**：
- `backend/modules/task/router.py` — 移除 `task_execution_router` 的 import + include_router
- `backend/modules/task/schemas/task.py` — 移除 `TaskExecutionQueryParams` / `TaskExecutionResponseData` / `TaskExecutionDetailResponseData` 三个 schema

### 前端

**修改**：
- `frontend/src/service/api/task.ts` — 移除 7 个旧 API 函数（`fetchStartTaskExecution` / `fetchPauseExecution` / `fetchResumeExecution` / `fetchStopExecution` / `fetchGetActiveExecutions` / `fetchGetExecutionHistory` / `fetchGetExecutionDetail`）
- `frontend/src/typings/api/task.d.ts` — 移除 4 个旧类型（`TaskExecutionStatus` / `TaskExecution` / `TaskExecutionSearchParams` / `TaskExecutionList` / `TaskExecutionDetail`）

## 关键决策

### 不引入运行时校验，只补文档

ORM 层 `Mapped[Optional[Dict[str, Any]]]` 保持不变。Pydantic 类（`TaskDefinitionSnapshot` / `ProgressDetail`）在写入路径（service `model_dump(mode="json")`）和响应路径（response schema）已经强约束，再加 ORM 层校验属于冗余。仅把 Pydantic 类名写进字段注释 + `comment=`，便于 IDE 阅读模型时能反查到对应 Pydantic 类。

### ORM 模型不 import schemas 模块

`backend/database/models/business/task_execution_record.py` 仅用纯文本注释指向 Pydantic 类，**不**做 `from modules.task.schemas.task_execution_record import ...`，避免 `database` 子模块依赖 `modules`，保持分层单向。

### drop 迁移 downgrade 完整保留字段

downgrade 重建表的字段从 `0004_task_tables.py` 原样抄过来，确保 `alembic downgrade` 能恢复原结构（不含数据）。

### task_execution_record 表的 Pydantic 类早已有

`schemas/task_execution_record.py:23-64` 已定义 `TaskDefinitionSnapshot` / `TaskPointSnapshot` / `TaskActionSnapshot` / `ProgressDetail` / `PointProgressStatus`。本次只补 ORM 层文档，不动这些类。

## 验证

### 后端（已通过）

```bash
cd backend
python -m py_compile \
  database/models/business/__init__.py \
  database/models/business/task.py \
  database/models/business/task_execution_record.py \
  modules/task/router.py \
  modules/task/schemas/task.py \
  modules/task/services/task_service.py \
  modules/task/services/task_execution_record_service.py \
  database/alembic/versions/0032_drop_task_execution_table.py

python -c "
from database.models.business import Task, TaskPoint, TaskExecutionRecord, task_robot_association
from modules.task.router import router
from modules.task.services.task_service import TaskService
from modules.task.services.task_execution_record_service import TaskExecutionRecordService
print('Task.executions exists?', hasattr(Task, 'executions'))  # False
print('routes:', [r.path for r in router.routes])  # 不应再有 /task/execution/*
"
```

### 前端（已通过）

```bash
cd frontend
pnpm typecheck
```

输出中 task 模块零报错（仅 scene/map 与 scheduler 有与本次无关的存量报错）。

### 数据库（待人工执行）

```bash
cd backend
alembic upgrade head
# 确认 0032_drop_task_execution_table 应用成功
# 确认 \d task_execution 报"不存在"
```

## 子模块提醒

`backend/database` 是独立 git 子模块（仓库 `SpatialtemporalAI/Wujie-Jilin-Database`），本次变更包括：

- 删除 1 个模型文件
- 修改 3 个模型文件
- 新增 1 个 alembic 迁移

需要在子模块仓库内单独 commit + push，再在主仓更新 submodule ref。

## 相关文件

后端 submodule：
- `backend/database/models/business/task_execution.py`（删）
- `backend/database/models/business/__init__.py`、`task.py`、`task_execution_record.py`（改）
- `backend/database/alembic/versions/0032_drop_task_execution_table.py`（新）

后端主仓：
- `backend/modules/task/services/task_execution_service.py`、`endpoints/task_execution.py`（删）
- `backend/modules/task/router.py`、`schemas/task.py`（改）

前端：
- `frontend/src/service/api/task.ts`、`typings/api/task.d.ts`（改）

## 记录日期

2026-06-26
