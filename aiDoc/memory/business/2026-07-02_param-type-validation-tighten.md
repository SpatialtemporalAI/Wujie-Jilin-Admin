# 接口传参类型校验收紧

## 需求描述

全面审计前后端接口传参类型校验，并在 `OptionalIntField` 机制基础上统一收敛：
1. 文档已写明取值、但 schema 未强约束的查询字段补枚举校验（非法值直接 422）
2. 仍裸 `int | None` / `Optional[int]` 的查询参数 ID 字段统一为 `OptionalIntField`（空值友好）
3. 前端提交时 `undefined`/`null` 类型坏味道收敛
4. 前端枚举选项与后端取值对齐（接口契约一致）

## 状态

已完成

## 涉及范围

### 后端

- `app/models/common/base.py`：新增 `parse_optional_enum(allowed)` 工厂（沿用 `OptionalIntField` 的 `BeforeValidator` + `EMPTY_VALUES` 模式），空值→None、命中允许集→原值、非法值→422
- `modules/robot/schemas/robot.py`：新增 `RobotStatusField`(online/offline/inactive)、`SpeedLevelField`(normal/slow/low)；`RobotQueryParams.status/model_id/map_id`、`RobotCreate/Update.status/speed_level` 改用枚举字段；`model_id/map_id` 查询参数改 `OptionalIntField`
- `modules/robot/schemas/robot_event_log.py`：`event_type`(task/alarm)、`event_status`(normal/abnormal) 改枚举字段
- `modules/task/schemas/task_execution_record.py`：新增 `ExecutionStatusField`(pending/running/paused/cancelled/completed/failed)、`ExecutionSourceField`(platform_schedule/voice_trigger/manual)；查询参数 `status/source` 收紧；`TaskExecutionRecordStartIn.source` 改 `Literal`
- `modules/scheduler/schemas/task_log.py`：新增 `TaskLogStatusField`(running/success/timeout/failed)；查询参数 `status` 收紧
- `modules/scene/schemas/scene_map.py`：`SceneMapQueryParams.group_id` 改 `OptionalIntField`

### 前端

- `views/robots/modules/robot-operate-drawer.vue`：去掉 `model_id: undefined as unknown as number` 类型谎言，本地 model 改 `RobotOperateModel`（`model_id: number | null`，默认 `null`），提交前 `model.value.model_id!` 收敛（`validate()` 已保证非空）

## 约束与备注

- `OptionalIntField` / 枚举字段**仅用于 query 参数**（URL 编码成字符串、空值形态多）；请求体（body）走 JSON、前端给带类型值，保持 `Optional[int]` / `Optional[str]`
- 时间范围筛选字段 `start_time`/`end_time`（事件日志/执行记录/调度日志）本次**不动**——强转 `datetime` 有 `"YYYY-MM-DD HH:mm:ss"` 非 ISO 导致 422 的风险，单独评估
- 机器人 `status` 是字符串枚举（online/offline/inactive），**不走** `"1"/"2"` bool 桥接；前端 `RobotStatusEnum` 须与后端取值一致
- 响应（Response）字段不加枚举 `BeforeValidator`，避免脏数据让整页 list 422（参考 `RobotResponseData.grpc_config` 的降级处理）

## 相关文件

- 后端：`backend/app/models/common/base.py`、`backend/modules/robot/schemas/robot.py`、`backend/modules/robot/schemas/robot_event_log.py`、`backend/modules/task/schemas/task_execution_record.py`、`backend/modules/scheduler/schemas/task_log.py`、`backend/modules/scene/schemas/scene_map.py`
- 前端：`frontend/src/views/robots/modules/robot-operate-drawer.vue`
- 契约文档：`aiDoc/frontend-backend/boundary.md`（新增「枚举字段与可选 ID 查询参数」一节）

## 记录日期

2026-07-02
