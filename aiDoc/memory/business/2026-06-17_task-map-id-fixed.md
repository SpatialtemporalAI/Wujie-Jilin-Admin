# 任务固化场景地图字段

## 需求描述

任务列表的"场景"显示原先从机器人 map_name 实时推导，导致地图编辑器修改机器人关联场景后，任务显示的场景跟着变化。需要给任务增加独立的 map_id 字段固话场景，机器人改绑不再影响任务场景配置。

## 状态

已完成

## 涉及范围

### 后端

- Task 模型新增 map_id 列（外键 scene_map.id，SET NULL）
- 新增 alembic 迁移 0020
- TaskCreate/TaskUpdate/TaskResponseData 增加 map_id/map_name
- 任务列表筛选 map_id 改为直接查 Task.map_id
- 任务列表/详情响应补充 map_name

### 前端

- Task 类型与 TaskCreate 增加 map_id/map_name
- 新增/编辑任务提交时携带 map_id
- 编辑回显优先读 task.map_id
- 任务列表"场景"列改为读 task.map_name

## 约束与备注

- 存量任务 map_id 为空，编辑时会回填。
- 执行记录的 map 信息仍从 robot 推导（执行记录为历史快照）。

## 相关文件

- backend/database/models/business/task.py
- backend/alembic/versions/0020_task_map_id.py
- backend/modules/task/schemas/task.py
- backend/modules/task/services/task_service.py
- backend/modules/task/endpoints/task.py
- frontend/src/typings/api/task.d.ts
- frontend/src/views/task/modules/task-operate-drawer.vue
- frontend/src/views/task/modules/task-list-tab.vue

## 记录日期

2026-06-17
