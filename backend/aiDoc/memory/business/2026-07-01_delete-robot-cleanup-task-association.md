# 删除机器人时清理任务关联

## 需求描述

删除机器人时，需要将其从所有关联的任务列表中移除——即清理 `task_robot` 多对多关联表中该机器人的全部关联记录，避免删除机器人后任务侧仍残留对该机器人的引用（孤儿关联）。

## 状态

已完成

## 涉及范围

### 后端

- `RobotService.delete`：在软删除 robot、并联动软删除 `RobotStatusRecord` / `RobotVoiceConfig` / `RobotEventLog` 之后、`commit` 之前，新增一步物理删除 `task_robot_association` 中 `robot_id == robot_id` 的全部行。
- 新增 import：`from database.models.business.task import task_robot_association`（与 `task_service.py` 同一导入路径，无循环引用）。

### 前端

无。任务列表为动态查询，删除机器人后该机器人不再出现在关联任务中，无需改动。

## 约束与备注

- `task_robot` 是纯多对多物理关联表（仅 `task_id` / `robot_id` 两列，无 `deleted_at`），无法软删除，只能物理删除。
- robot 采用软删除（置 `deleted_at`），不会触发外键 `ondelete=CASCADE`，因此关联行不会被数据库自动清理，必须由应用层显式删除，否则留下孤儿关联。
- 删除关联**不下发 gRPC 通知**：任务变更通知方向为 task → robot（推送到关联 robot 的 agent），被删除的 robot 无需再接收任务变更；`task.proto` 也无对应 operation。任务的其他关联 robot 不受影响（任务定义未变，仅少一个参与 robot）。
- 接口契约与返回结构不变，endpoint 层无需改动。

## 相关文件

- backend/modules/robot/services/robot_service.py
- backend/database/models/business/task.py（`task_robot_association` 定义）

## 记录日期

2026-07-01
