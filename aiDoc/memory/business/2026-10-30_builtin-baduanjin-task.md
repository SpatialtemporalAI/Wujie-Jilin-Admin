# 任务管理 · 固定 ID 的内置八段锦任务

**日期**: 2026-10-30
**提出者**: 用户

## 需求概述

将“八段锦1111”任务改为 `id=1`、名称“八段锦”，增加内置标识并作为迁移种子。前端在名称旁显示“内置”；内置任务允许查询、立即启动和修改绑定机器人，其他操作禁止。

## 关键决策

- 操作边界：允许任务列表、任务详情、执行记录和执行详情查询，允许立即启动；编辑仅接受 `robot_ids`，禁止其他字段更新、复制、删除、启禁用、暂停、恢复和停止。
- `task.is_builtin` 为 `Boolean NOT NULL DEFAULT false`，后端响应和前端 `Api.Task.Task` 同步暴露。
- 迁移采用“复制主记录 → 转移 `task_robot` / `task_point` / `task_execution_record` 关联 → 删除旧主记录”，不修改外键约束，不用当前任务配置覆盖历史快照。
- 新环境无源任务时插入三套八段锦标准种子；`id=1` 被无关任务占用时迁移报错，不覆盖数据。
- 后端更新内置任务时要求请求字段严格等于 `{robot_ids}`，管理接口与开放 API 的启动共用服务入口；其他禁止操作返回“内置任务仅支持启动和修改绑定机器人”。
- 前端内置行只显示立即启动和编辑；编辑抽屉保留表演动作编排展示，除机器人外的输入和编排按钮全部禁用，提交仅携带 `robot_ids`。
- 任务列表后端按 `is_builtin DESC, id DESC` 排序，保证所有分页和筛选结果中内置任务最前，普通任务相对顺序不变。

## 实现范围

- `backend/database/alembic/versions/0020_seed_builtin_baduanjin_task.py`：新增字段、迁移既有任务、种子和回退逻辑。
- `backend/database/models/business/task.py`、`backend/modules/task/schemas/task.py`、`frontend/src/typings/api/task.d.ts`：内置字段契约。
- `backend/modules/task/services/task_service.py`、`backend/modules/task/services/task_execution_record_service.py`：操作约束和内置优先排序。
- `frontend/src/views/task/modules/task-list-tab.vue`：名称旁“内置”标签及启动/编辑入口。
- `frontend/src/views/task/modules/task-operate-drawer.vue`：内置编辑禁用状态和仅机器人提交。
- `aiDoc/frontend-backend/boundary.md`：跨栈契约。

## 验证

- 迁移和回退在事务中验证后回滚：ID、名称、标识、机器人关联、38 条执行记录均正确；全新环境种子与 ID 冲突拒绝也通过。
- 当前开发库已应用 `0020`；实际数据为 `id=1 / 八段锦 / is_builtin=true`，保留一个机器人关联和 38 条历史执行记录。
- 真实列表及表演筛选查询均以 ID=1 的内置任务为首，普通任务 ID 倒序保持不变。
- 仅机器人更新和立即启动通过；名称等其他字段更新及暂停返回 `ConflictError(msg="内置任务仅支持启动和修改绑定机器人")`。验证使用 mock gRPC，未向机器人真实下发，机器人绑定保持原值。
- 后端相关文件 `py_compile` 通过；前端 `pnpm typecheck` 通过。
- 相关 Vue 文件存在大量既有 ESLint 错误和格式警告；未扩大范围处理无关问题。
