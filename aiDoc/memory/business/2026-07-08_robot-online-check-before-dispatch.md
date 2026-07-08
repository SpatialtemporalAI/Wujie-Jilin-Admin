# 实时下发接口增加机器人在线前置校验

**日期**: 2026-07-08
**提出者**: 用户

## 需求描述

以下三个需要实时下发到机器人的接口，在执行下发前增加「机器人在线」判断：若目标机器人不在线（`Robot.status != online`），直接拦截并提示「机器人不在线」，不再徒劳下发 gRPC。

1. 参数配置-唤醒词测试（`POST /robot/config/voice/test-wake-word`）
2. 参数配置-语音合成测试（`POST /robot/config/voice/test-tts`）
3. 任务管理-任务列表-启动任务（`POST /task/execution-record/{task_id}/start` 与 `/start-or-resume/{task_id}`）

## 状态

已完成

## 涉及范围

### 后端

- `backend/modules/robot/services/robot_service.py`：新增静态方法 `RobotService.ensure_robots_online(db, robot_ids)`。
  - 一次 `select(Robot.id, Robot.name, Robot.status).where(id.in_(robot_ids), deleted_at IS NULL)` 取回，凡 `status != RobotStatus.ONLINE` 收集其 `name`；非空则抛 `ConflictError(msg="机器人 {name1、name2} 不在线，请确保机器人已在线")`。
  - `robot_ids` 为空直接 return（保持「不校验空选择」的既有约定）；查不到（已删除/不存在）的 robot 不计入，沿用各调用方「不校验存在性」约定。
- `backend/modules/robot/endpoints/robot_config.py`：
  - 新增 `from modules.robot.services.robot_service import RobotService`。
  - `test_wake_word` / `test_tts` 在 `logger.info` 之后、调 `VoiceConfigClient.test_*` 之前各加一行 `await RobotService.ensure_robots_online(db, [body.robot_id])`。
- `backend/modules/task/services/task_execution_record_service.py`：
  - 新增 `from modules.robot.services.robot_service import RobotService`。
  - `start_execution` 在任务存在性校验（404）之后、`TaskConfigClient.broadcast_task_changed` 之前加 `await RobotService.ensure_robots_online(db, list(robot_ids))`。该 service 同时被 `/{task_id}/start` 与 `/start-or-resume/{task_id}` 两个端点复用，一处覆盖两个入口。

### 前端

- 零改动。离线提示由后端抛 `ConflictError`（HTTP 409，body `{code, msg}`）→ 前端 `request` 拦截器 `onError` 读 `responseData.msg` 自动 toast，与现有 `NotFoundError`（任务不存在）路径一致。

## 关键决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 在线判定来源 | `Robot.status == RobotStatus.ONLINE` | 项目唯一的在线状态字段（online/offline/inactive，默认 inactive），由机器人侧上报维护 |
| 失败方式 | service 抛 `ConflictError`，三处统一让冒泡 | 与同 service 既有 `NotFoundError`/`ConflictError`（如「只有运行中…才能暂停」）状态前置校验模式一致；全局 `base_exception_handler` 转 `{code:409, msg}`，前端 onError 自动 toast |
| 测试端点失败路径 | 由原 `return response_base.fail`（code 500）改为离线时 ConflictError（409） | 离线是确定性前置拦截，需更明确的「机器人不在线」文案，而非笼统的「测试失败，请确保机器人在线」；gRPC 瞬时失败的旧文案保留不变 |
| 共享 helper 位置 | `RobotService.ensure_robots_online` | 机器人状态归属 robot 模块；避免三处重复查询逻辑；task 模块单向依赖 robot 模块（robot_service 仅 import `task_robot_association` 模型，无 service 级循环） |
| 多机器人语义 | 任一离线即整体拦截并列出名字 | 启动任务支持多选机器人；用户需知道具体哪个/哪些不在线以便剔除或上线 |

## 范围外 / 影响

- 仅拦截「非 online」状态；`inactive`（未激活）同样被拦，符合「不在线」语义。
- OpenAPI（`execute_task` / `goto_point` / `navigate_route`）等其他下发入口本次不在范围；如需统一可后续扩展（它们也调 `start_execution` 或类似路径）。
- 暂停/恢复/停止等控制接口不在范围（用户只点了启动与两个测试）。

## 相关文件

- [backend/modules/robot/services/robot_service.py](backend/modules/robot/services/robot_service.py)
- [backend/modules/robot/endpoints/robot_config.py](backend/modules/robot/endpoints/robot_config.py)
- [backend/modules/task/services/task_execution_record_service.py](backend/modules/task/services/task_execution_record_service.py)

## 相关历史记忆

- [2026-06-29 移除本服务定时调度 + 启动任务改为纯 gRPC](./2026-06-29_task-schedule-removed-and-start-grpc-only.md)（本次在其 `start_execution` 纯 gRPC 路径前加在线校验）
- [2026-06-24 唤醒词测试显示模拟回应话术 + proto 新增测试 RPC](./2026-06-24_voice-test-wakeword-response.md)（本次为 test-wake-word / test-tts 加前置在线校验）
