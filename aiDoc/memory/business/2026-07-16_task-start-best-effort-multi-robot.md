# 播报任务多机器人启动改为尽力下发（无需全部在线）

**日期**: 2026-07-16
**提出者**: 用户

## 需求描述

播报任务关联多台机器人时，启动不再要求"所有机器人都在线"，改为：

1. 无需所有机器人在线即可启动；
2. 在线机器人逐个（分开）下发 gRPC `run_now`，离线机器人跳过；
3. 接口返回成功启动的机器人明细；
4. 若无任何机器人成功启动，则提示"任务执行失败"。

承接 [[2026-07-08 实时下发增加在线前置校验]](./2026-07-08_robot-online-check-before-dispatch.md)：那次给启动任务加了"任一离线即整体拦截"的硬校验；本次仅对**任务启动**路径放宽为尽力下发（唤醒词/语音合成测试两处仍保留硬校验）。

## 状态

已完成

## 涉及范围

### 后端

- `backend/modules/grpc/task_client.py`
  - `TaskConfigClient.broadcast_task_changed` 返回值由 `{total, success_count, failed_count}` 扩展为同时带 `success_robot_ids` / `failed_robot_ids`（新增字段，向后兼容；其余仅记日志的调用方不受影响）。
- `backend/modules/robot/services/robot_service.py`
  - 新增非抛错的 `RobotService.get_online_robot_ids(db, robot_ids) -> List[int]`：一次查询返回 `status == ONLINE` 的子集，用于启动任务前过滤离线机器人，避免对离线机器人发起无谓的 gRPC 超时等待。
  - 既有的 `ensure_robots_online`（硬校验、抛 ConflictError）保留，唤醒词/语音合成测试仍用它。
- `backend/modules/task/services/task_execution_record_service.py`
  - 重写 `start_execution`：移除"全部在线"硬校验；
    - 巡逻任务仍保留 `ensure_robots_match_map`（配置正确性硬校验）；
    - 用 `get_online_robot_ids` 过滤，仅向在线机器人 `broadcast_task_changed(operation="run_now")`；
    - `failed = gRPC 失败 + 离线未下发`；
    - **`success_robot_ids` 为空 → 抛 `ConflictError`**：有在线但 gRPC 全失败 → "任务执行失败：未能成功启动任何机器人"；无在线 → "任务执行失败：关联的机器人均不在线"；
    - 否则返回 `{total, success_count, failed_count, success_robot_ids, failed_robot_ids}`。
- `backend/modules/task/schemas/task_execution_record.py`
  - 新增 `TaskStartResultData`（total/success_count/failed_count/success_robot_ids/failed_robot_ids）。
- `backend/modules/task/endpoints/task_execution_record.py`
  - `/{task_id}/start` 与 `/start-or-resume/{task_id}` 两个端点 `response_model` 改为 `ResponseModel[TaskStartResultData]`，返回明细 + 文案 `任务已启动，成功 N 台[, 失败 M 台]`。
  - 新增 `_build_start_msg(result)` 拼装提示文案。

### 前端

- `frontend/src/typings/api/task.d.ts`：新增 `Api.Task.TaskStartResult` 类型。
- `frontend/src/service/api/task.ts`：`fetchStartExecutionRecord` / `fetchStartOrResumeExecution` 返回类型由 `void` 改为 `Api.Task.TaskStartResult`。
- `frontend/src/views/task/modules/task-list-tab.vue`：`handleStart` 读取 `data`，按 `success_count` / `failed_count` 提示——全成功 `message.success("任务已启动，成功 N 台")`，有失败 `message.warning("任务已启动，成功 N 台，失败 M 台")`；无一成功时后端抛错，由 `request` 拦截器自动 toast "任务执行失败…"。

## 关键决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 在线过滤方式 | DB 查询 `Robot.status == ONLINE` 预过滤，离线不发 gRPC | 与既有在线判定来源一致；避免对离线机器人触发 `GRPC.TIMEOUT_SECONDS` 级等待 |
| "无一成功"反馈 | service 抛 `ConflictError` | 复用 `request` 拦截器自动 toast；与 07-08 在线校验失败路径同构 |
| 失败聚合 | failed = gRPC 下发失败 + 离线 | 让前端/用户清楚"哪些没起来" |
| 巡逻任务 | 保留 map 一致性硬校验，在线改尽力 | 巡逻单机器人，离线→0 成功→"任务执行失败"，行为等价且统一 |
| 测试端点 | 不动，仍用 `ensure_robots_online` 硬校验 | 本次需求仅涉及任务启动；测试仍应明确提示"机器人不在线" |

## 约束与备注

- `broadcast_task_changed` 返回新增字段为**增量**改动，task_service 的 create/update/delete 等仅记日志的调用方不受影响。
- 前端仅用 `pnpm typecheck` 验证（用户偏好，不做界面测试）；后端 `py_compile` 通过。
- 在线判定以 `Robot.status` 为准（由机器人侧上报）；DB 标记在线但实际不可达时，gRPC 仍会失败并计入 failed，符合预期。

## 相关文件

- [backend/modules/grpc/task_client.py](backend/modules/grpc/task_client.py)
- [backend/modules/robot/services/robot_service.py](backend/modules/robot/services/robot_service.py)
- [backend/modules/task/services/task_execution_record_service.py](backend/modules/task/services/task_execution_record_service.py)
- [backend/modules/task/schemas/task_execution_record.py](backend/modules/task/schemas/task_execution_record.py)
- [backend/modules/task/endpoints/task_execution_record.py](backend/modules/task/endpoints/task_execution_record.py)
- [frontend/src/views/task/modules/task-list-tab.vue](frontend/src/views/task/modules/task-list-tab.vue)

## 相关历史记忆

- [2026-07-08 实时下发增加在线前置校验](./2026-07-08_robot-online-check-before-dispatch.md)（本次放宽其任务启动路径的硬校验）
- [2026-07-07 播报任务无场景地图 + 机器人多选](./2026-07-07_task-broadcast-no-map-and-multi-robot.md)（播报任务多机器人语义的来源）
- [2026-06-29 移除定时调度 + 启动改为纯 gRPC](./2026-06-29_task-schedule-removed-and-start-grpc-only.md)
