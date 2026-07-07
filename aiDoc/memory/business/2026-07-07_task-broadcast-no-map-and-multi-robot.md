---
name: task-broadcast-no-map-and-multi-robot
description: 播报任务隐藏场景地图输入框与提示，机器人改多选；巡逻任务不动
metadata:
  type: project
---

## 需求描述

任务管理新增/编辑任务抽屉，按任务类型差异化表单：

1. **播报任务（broadcast）**：
   - 隐藏「场景地图」输入框，不需要选择场景地图
   - 隐藏场景地图上方的「机器人不在场景下则无法执行」NAlert 提示框
   - 绑定机器人由单选改为**多选**
2. **巡逻任务（patrol）**：完全不动，保持单选机器人 + 必选场景地图

承接 [[task-robot-single-select]]（2026-07-02 把多选改单选的变更），本次仅对播报任务恢复多选。

## 状态

已完成

## 涉及范围

### 后端

- `backend/modules/task/schemas/task.py`
  - `TaskCreate.robot_ids` / `TaskUpdate.robot_ids`：移除 `max_length=1`，仅保留 `min_length=1`
  - 新增 `field_validator('robot_ids')`：`task_type == 'patrol'` 且长度 > 1 时抛错「巡逻任务仅支持绑定一台机器人」；播报任务不限
  - `TaskUpdate` 中 `task_type` 缺省时不限制（前端编辑始终带 task_type）
  - `map_id` 本就是 `Optional[int]`，播报任务传 null 落库无问题

### 前端

- `frontend/src/views/task/modules/task-operate-drawer.vue`
  - 场景约束 NAlert 与「场景地图」NFormItem 加 `v-if="isPatrol"`，仅巡逻显示
  - 「绑定机器人」NFormItem 拆分：patrol 单选（`robotId` computed，受 map_id 约束）/ broadcast 多选（直接绑 `model.robot_ids`，不受场景约束）
  - `rules`：map_id 仅巡逻 required；robot_ids patrol `max:1` / broadcast 不限
  - `handleSubmit`：map_id 必填校验仅巡逻；submitData 归一化——播报 map_id 强制 null、robot_ids 全提交，巡逻 robot_ids 截断 `slice(0,1)`
  - 编辑回填保持不变（`fetchGetTask` 后 robot_ids 取全部，播报任务可正确回显多选）

## 约束与备注

- 数据库 `task_robot` 关联表与 `Task.robots` relationship 不变（本就支持多对多）
- 播报任务提交时 map_id 强制为 null，避免从回填的机器人 map_id 残留脏数据
- 巡逻任务行为完全保持，包括「先选场景地图 → 同场景机器人可选 → 单选」的级联约束
- 前端仅用 `pnpm typecheck` 验证（用户偏好，不做界面测试）

## 相关文件

- `backend/modules/task/schemas/task.py`
- `frontend/src/views/task/modules/task-operate-drawer.vue`
- `aiDoc/frontend-backend/boundary.md`（任务管理 · 机器人绑定契约 已更新）

## 记录日期

2026-07-07
