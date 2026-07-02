---
name: task-robot-single-select
description: 任务新增/编辑机器人绑定由多选改为单选，通过接口层 Schema 校验限制
metadata:
  type: project
---

## 需求描述

任务管理的新增/编辑任务时，机器人绑定由多选改为单选。限制仅在接口层实现，不修改数据库表结构与关联表，便于后续快速恢复多选。

## 状态

已完成

## 涉及范围

### 后端

- `backend/modules/task/schemas/task.py`
  - `TaskCreate.robot_ids`: `min_length=1, max_length=1`
  - `TaskUpdate.robot_ids`: `max_length=1`
  - 描述更新为"绑定的机器人ID列表（当前仅支持单选）"

### 前端

- `frontend/src/views/task/modules/task-operate-drawer.vue`
  - 机器人 `NSelect` 移除 `multiple`，改为单选
  - 新增 `robotId` 计算属性，与 `model.robot_ids`（数组）双向转换
  - 表单校验规则 `robot_ids` 增加 `max: 1`
  - 编辑回显仅取第一台机器人 `.slice(0, 1)`

## 约束与备注

- API 字段名保持 `robot_ids: number[]` 不变，未来恢复多选时只需调整后端 `max_length` 与前端的 `multiple` 属性。
- 数据库 `task_robot` 关联表与 `Task.robots` relationship 不变。
- 现有含多台机器人的任务，编辑时只展示第一台，保存后变为单选。

## 相关文件

- `backend/modules/task/schemas/task.py`
- `frontend/src/views/task/modules/task-operate-drawer.vue`
- `aiDoc/frontend-backend/boundary.md`

## 记录日期

2026-07-02
