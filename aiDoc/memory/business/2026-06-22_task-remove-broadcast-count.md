# 移除播报类型任务的播报次数配置

## 需求描述

任务管理中，移除播报类型（broadcast）任务的"播报次数"配置项。播报任务只保留"播报文本"配置，不再支持选择播报次数（1/2/3/5/循环）。

## 状态

已完成

## 涉及范围

### 后端

不改动。`broadcast_count` 字段在数据库、ORM、Schema、Service 中保留，兼容历史数据。前端不再提交该字段，后端接收到不传 `broadcast_count` 的请求时按默认值 `None` 处理。

### 前端

- `frontend/src/views/task/modules/task-operate-drawer.vue`
  - 删除 `broadcastCountOptions` 常量
  - 从 `FormModel` 接口删除 `broadcast_count` 字段
  - 从 `createDefaultModel` 默认值删除 `broadcast_count`
  - 从 `handleInitModel` 编辑回填逻辑删除 `broadcast_count`
  - 从 `handleSubmit` 提交数据 `submitData` 删除 `broadcast_count`
  - 模板中删除"播报次数" `NFormItem` 及 `NSelect`
- `frontend/src/typings/api/task.d.ts`
  - `Api.Task.Task` 类型删除 `broadcast_count`
  - `Api.Task.TaskCreate` 类型删除 `broadcast_count`

## 约束与备注

- 后端字段保留，无需数据库迁移
- 后端历史任务数据如果存在 `broadcast_count` 值，前端不再消费
- 详情抽屉、列表、搜索、执行 tab、历史 tab 本来就没有展示播报次数，无需改动

## 相关文件

- `frontend/src/views/task/modules/task-operate-drawer.vue`
- `frontend/src/typings/api/task.d.ts`
- `backend/modules/task/schemas/task.py`（未改动，保留字段）
- `backend/modules/task/services/task_service.py`（未改动）
- `backend/database/models/business/task.py`（未改动）
- `backend/alembic/versions/0004_task_tables.py`（未改动）

## 记录日期

2026-06-22
