---
date: 2026-07-10
type: business
---

# 商户开放 API 动作类接口增加机器人在线校验

## 需求

商户开放 API（`/openapi/v1`）中所有需要实时下发到机器人的动作类接口，在执行前必须校验目标机器人是否在线（`Robot.status == ONLINE`），离线时返回 `409 Conflict`。

## 涉及接口

- `POST /openapi/v1/goto_point` — 单点导航
- `POST /openapi/v1/navigate_route` — 多点导航
- `POST /openapi/v1/execute_task` — 执行任务
- `POST /openapi/v1/pause_task` — 暂停任务
- `POST /openapi/v1/resume_task` — 恢复任务
- `POST /openapi/v1/stop_task` — 停止任务
- `POST /openapi/v1/speak` — 语音播报

## 实现

- `backend/modules/merchant/services/openapi_service.py`
  - 导入 `RobotService`
  - 在上述 7 个接口的 `resolve_robot` 之后、`NavigationClient` / `TaskExecutionRecordService` / `VoiceConfigClient` 调用之前，统一增加 `await RobotService.ensure_robots_online(db, [robot.id])`
  - `execute_task` 原已通过 `TaskExecutionRecordService.start_execution` 内部校验；为保持调用点一致、便于阅读，在 service 层再次显式校验

## 影响范围

- 仅动作类接口行为变更：离线机器人现在会提前返回 `409`，不再调用 gRPC/任务服务。
- 查询类接口（`scenes` / `points` / `tasks`）不涉及实时下发，保持原行为。
- 错误消息沿用 `RobotService.ensure_robots_online` 的既有实现："机器人 {name} 不在线"。

## 相关文件

- `backend/modules/merchant/services/openapi_service.py`
- `backend/modules/robot/services/robot_service.py`（复用 `ensure_robots_online`）
