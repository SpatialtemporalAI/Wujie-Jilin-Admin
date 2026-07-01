# 任务点位动作列表可为空

## 需求描述

任务管理-添加/编辑任务中，添加巡逻点位时，该点位对应的运控动作列表可以为空（不再强制至少一个动作）。

## 状态

已完成

## 涉及范围

### 后端

无。后端 `TaskPointCreate.actions` 本就用 `default_factory=list` 且描述标注「可为空」，service 层 `[a.model_dump() for a in pt.actions]` 对空列表产出 `[]`，契约无需调整。

### 前端

- 新增点位（`addPoint`）时不预置默认动作，`actions` 初始为 `[]`。
- 「删除动作」按钮去掉 `point.actions.length > 1` 限制，允许删除最后一个动作直至列表为空。
- 提交校验中遍历 `point.actions` 找未选动作的逻辑对空数组天然放行（`findIndex` 返回 -1），无需改动。
- 编辑回填已有 `actions.length > 0 ? ... : []` 兜底，存量空动作点位可正常回显。

## 约束与备注

- 本需求与 [2026-06-17 任务新增编辑必填校验](./2026-06-17_task-form-required-validation.md) 中「动作不能为空」一条方向相反：动作列表从「至少一个」改为「允许为空」。点位本身（巡逻点位 annotation_id）仍必填。
- 单个动作项内部的 `action` 类型选择仍必填（若用户添加了动作行却未选类型，提交仍会拦截）。
- 仅前端表单层调整，未触碰前后端字段契约。

## 相关文件

- frontend/src/views/task/modules/task-operate-drawer.vue
- backend/modules/task/schemas/task.py（TaskPointCreate.actions，未改动，已支持空）

## 记录日期

2026-07-01
