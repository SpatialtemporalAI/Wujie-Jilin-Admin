# 地图编辑器机器人切换绑定地图时检查进行中任务

**日期**: 2026-07-11
**提出者**: 用户

## 需求描述

在地图编辑器中为机器人切换绑定地图（`PUT /admin/robot/manage/{robot_id}/bind-map`）时，若该机器人当前存在状态为 `pending` / `running` / `paused` 的任务执行记录，则禁止切换，并提示用户先停止或完成任务。

## 状态

已完成

## 涉及范围

### 后端

- `backend/database/models/business/task_execution_record.py`：新增 `ACTIVE_EXECUTION_STATUSES = ("pending", "running", "paused")` 常量，便于多处复用。
- `backend/modules/robot/services/robot_service.py`：在 `update_map_binding` 中新增校验：
  - `map_id` 无实际变化时直接返回，避免无意义查询与 gRPC 调用。
  - 查询 `TaskExecutionRecord` 活跃记录，存在时抛 `ConflictError`。
  - `ConflictError` 加入显式回滚分支，避免被记录为未预期异常。

### 前端

无需改动。`property-panel.vue` 的机器人场景 `NSelect` 使用 `:value` 受控绑定；API 失败后本地 `robot.map_id` 不变，下拉框自动回到原值，错误提示由统一请求拦截器展示。

## 约束与备注

- 仅针对地图编辑器换地图入口（`bind-map`）生效；机器人管理主表单的 `map_id` 更新暂不拦截。
- 活跃状态定义为 `pending` / `running` / `paused`。
- 解绑（`map_id=None`）同样受该校验约束。

## 关键决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 校验入口 | `PUT /admin/robot/manage/{robot_id}/bind-map` 对应的 Service | 用户明确为「地图编辑器」场景 |
| 状态常量 | 在模型层定义 `ACTIVE_EXECUTION_STATUSES` | 避免魔法字符串分散在 service/query 中 |
| 无变化短路 | `existing.map_id == payload.map_id` 直接返回 | 减少无效查询与 gRPC SwitchMap 调用 |

## 相关文件

- [backend/modules/robot/services/robot_service.py](backend/modules/robot/services/robot_service.py)
- [backend/database/models/business/task_execution_record.py](backend/database/models/business/task_execution_record.py)
- [backend/modules/robot/endpoints/robot.py](backend/modules/robot/endpoints/robot.py)
- [frontend/src/views/map-editor/modules/property-panel.vue](frontend/src/views/map-editor/modules/property-panel.vue)

## 相关历史记忆

- [2026-06-11 地图编辑器机器人定位与绑定场景](./2026-06-11_map-editor-robot-location-binding.md) — 机器人总览列表支持切换绑定场景
- [2026-06-30 map.proto 新增 SwitchMap 切换机器人当前地图](./2026-06-30_map-switch-rpc.md) — `bind-map` 成功后触发 SwitchMap
