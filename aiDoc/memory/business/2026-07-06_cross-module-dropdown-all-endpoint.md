# 跨模块下拉改调 /all 轻量接口（避免权限不足）

## 需求描述

多个页面的下拉框调用**其他模块的列表接口**（`/list`，带 `require_permission`）作为数据源。
当前端用户没有该模块列表权限时，下拉加载收到 `code=403 "没有操作权限: xxx"`，
下拉为空并弹错误提示，阻断业务（如任务管理新建任务时无法选择机器人）。

项目已有 `/all` 轻量下拉接口模式（`/robot/model/all`、`/sys/role/all` 等）：
路由级仅 `Depends(current_user)`、无 `require_permission`、返回 `SimpleResponse` 简化字段。
本次为剩余两个热点接口补齐 `/all`，前端 6 处下拉统一改调。

## 状态

已完成

## 涉及范围

### 后端

新增两个 `/all` 端点（仅登录认证，无 require_permission）：

- `GET /robot/manage/all` → `List[RobotSimpleResponse]`
  - `backend/modules/robot/endpoints/robot.py`：在 `/list` 与 `/{robot_id}` 之间注册（避免被路径参数吞掉）
  - `backend/modules/robot/schemas/robot.py`：新增 `RobotSimpleResponse`（id/name/serial_number/map_id/status）
  - `backend/modules/robot/services/robot_service.py`：新增 `RobotService.get_all`（仅过滤 deleted_at，不过滤 status）

- `GET /scene/group/all` → `List[SceneGroupSimpleResponse]`
  - `backend/modules/scene/endpoints/scene_group.py`：在 `/tree` 与 `/{group_id}` 之间注册
  - `backend/modules/scene/schemas/scene_group.py`：新增 `SceneGroupSimpleResponse`（id/name）
  - `backend/modules/scene/services/scene_group_service.py`：新增 `SceneGroupService.get_all`

### 前端

- `frontend/src/typings/api/robot.d.ts`：新增 `AllRobot`
- `frontend/src/typings/api/scene.d.ts`：新增 `AllSceneGroup`
- `frontend/src/service/api/robot.ts`：新增 `fetchGetAllRobots`
- `frontend/src/service/api/scene.ts`：新增 `fetchGetAllSceneGroups`
- 6 处下拉由 `fetchGetRobotList({page_size:999})` / `fetchGetSceneGroupList({page_size:1000})` 改调 `/all`：
  - task-search / task-history-search / task-operate-drawer
  - merchant-operate-drawer（label 用 serial_number，故 SimpleResponse 保留该字段）
  - log/robot-log/robot-event-log-search
  - scene/map/scene-map-search

## 关键决策

### 沿用 /all 模式而非 require_any_permission

- 与 [[2026-06-26_task-scene-map-list-and-grpc-retry-dedup]] /
  [[2026-06-26_task-scene-map-annotation-list-permission]] 的 `require_any_permission` 修法不同：
  本次改用 `/all` 轻量接口
- 原因：robot 下拉被 5 处下游复用（任务/商户/日志），若给 `/robot/manage/list` 累加
  `task:list`/`merchant:list` 等权限码，列表接口语义被污染、权限码随复用膨胀；
  且 list 返回重字段（grpc_config 等）作下拉性能差
- `/all` 模式：消费方零权限耦合，返回仅必要字段，符合最小暴露原则

### RobotSimpleResponse 字段权衡

- 取 `id/name/serial_number/map_id/status`（均为 Robot 表原生列，无关联查询开销）
- `map_id`：task-search/history/drawer 的地图→机器人联动过滤依赖
- `serial_number`：merchant-operate-drawer 的 label `name（serial_number）`
- `status`：task-operate-drawer 的 label 在线/离线/未激活标签
- 仍去掉 `grpc_config`/`battery_threshold`/`speed_level` 等敏感或无关字段
- task-operate-drawer 顺带删除存而未用的 `map_name` 字段

### 已解决的不再动

- `/scene/map/list`、`/scene/map/{id}/annotation/list` 已用 `require_any_permission` 含 `task:list`，本次不动

## 约束与备注

- `/all` 复用与 list 相同的可见性过滤（deleted_at），不做 status 过滤（inactive 也是有效下拉项）
- 不引入前端统一 `useOptions` 封装，沿用各页面现有 loadOptions 模式
- 不改 `/robot/manage/list`、`/scene/group/list` 本身的权限（仍保留给各自列表页）

## 验证方案

- 后端：Swagger 直调 `/robot/manage/all`、`/scene/group/all`，普通用户 token（无 list 权限）应返回 200 + 数据
- 前端：`pnpm typecheck` 通过（仅余 2 个与本次无关的 i18n `map-editor` 既有错误）
- 端到端：仅 `task:list` 无 `robot:manage:list` 的账号打开任务管理，机器人下拉正常、无权限不足弹窗

## 相关文件

后端：
- `backend/modules/robot/endpoints/robot.py`
- `backend/modules/robot/schemas/robot.py`
- `backend/modules/robot/services/robot_service.py`
- `backend/modules/scene/endpoints/scene_group.py`
- `backend/modules/scene/schemas/scene_group.py`
- `backend/modules/scene/services/scene_group_service.py`

前端：
- `frontend/src/typings/api/robot.d.ts`
- `frontend/src/typings/api/scene.d.ts`
- `frontend/src/service/api/robot.ts`
- `frontend/src/service/api/scene.ts`
- `frontend/src/views/task/modules/task-search.vue`
- `frontend/src/views/task/modules/task-history-search.vue`
- `frontend/src/views/task/modules/task-operate-drawer.vue`
- `frontend/src/views/merchant/modules/merchant-operate-drawer.vue`
- `frontend/src/views/log/robot-log/modules/robot-event-log-search.vue`
- `frontend/src/views/scene/map/modules/scene-map-search.vue`

## 记录日期

2026-07-06
