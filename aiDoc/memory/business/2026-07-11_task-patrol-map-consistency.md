# 巡逻任务启动校验任务地图与机器人地图一致

**日期**: 2026-07-11
**提出者**: 用户

## 需求描述

任务管理启动巡逻任务（`patrol`）时，必须校验任务关联的场景地图（`task.map_id`）与执行机器人们关联的场景地图（`robot.map_id`）是否为同一张地图。若不一致，禁止启动并给出明确提示。

## 状态

已完成

## 涉及范围

### 后端

- `backend/modules/robot/services/robot_service.py`：新增 `ensure_robots_match_map` 辅助方法，统一校验机器人地图是否与目标地图一致。
- `backend/modules/task/services/task_execution_record_service.py`：`start_execution` 中，当 `task.task_type == "patrol"` 时调用上述校验，覆盖 `/execution-record/{task_id}/start`、`/execution-record/start-or-resume/{task_id}` 以及 OpenAPI `execute_task` 三条入口。

### 前端

无需改动。任务列表点击「立即启动」后，后端返回的 `ConflictError` 会经统一请求拦截器展示为错误提示。

## 约束与备注

- 仅对 `patrol` 任务生效；`broadcast` / `instant` 任务不受影响。
- `task.map_id` 与 `robot.map_id` 同时为 `None` 时视为一致。
- 已删除机器人不参与校验（与 `ensure_robots_online` 保持一致）。
- 校验在在线状态校验之前执行：先保证地图匹配，再检查在线。

## 关键决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 校验位置 | Service 层 `start_execution` | 覆盖所有启动入口，避免在每个 endpoint / OpenAPI 重复写 |
| 校验实现 | 在 `RobotService` 新增 `ensure_robots_match_map` | 与现有 `ensure_robots_online` 风格一致，便于复用 |
| 错误类型 | `ConflictError` (HTTP 409) | 业务冲突，非参数校验或资源不存在 |

## 相关文件

- [backend/modules/robot/services/robot_service.py](backend/modules/robot/services/robot_service.py)
- [backend/modules/task/services/task_execution_record_service.py](backend/modules/task/services/task_execution_record_service.py)
- [backend/database/models/business/task.py](backend/database/models/business/task.py)
- [backend/database/models/business/robot.py](backend/database/models/business/robot.py)

## 相关历史记忆

- [2026-07-01 任务绑定机器人与场景一致性提示](./2026-07-01_task-bind-robot-scene-tip.md) — 前端警示文案
- [2026-07-08 实时下发接口增加机器人在线前置校验](./2026-07-08_robot-online-check-before-dispatch.md) — 同 service 的 `ensure_robots_online` 模式
