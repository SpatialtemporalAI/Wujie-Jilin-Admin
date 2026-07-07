# 修复跨权限调用 robot:manage:list 接口

## 需求描述

多个非「机器人管理」页面在加载时调用需要 `robot:manage:list` 权限的机器人接口，
当用户只有本模块权限（如 `scene:map-editor:edit`、`robot:config:edit`、`robot:monitor:list`）
而没有 `robot:manage:list` 时，接口返回 `code=403 "没有操作权限: robot:manage:list"`，
页面下拉/列表为空并弹错误提示，阻断业务。

用户明确指出两类典型场景并要求排查类似问题：
1. 地图编辑器画布调用 `GET /robot/manage/map/{id}/robot-locations` 报无 `robot:manage:list`（跨权限）
2. 参数配置页面（设置）调用 `/robot/manage/list` 报无 `robot:manage:list`

## 状态

已完成

## 涉及范围

### 后端

- `backend/modules/robot/endpoints/robot_status_record.py`
  - `GET /robot/manage/map/{map_id}/robot-locations` 权限由 `require_permission("robot:manage:list")`
    改为 `require_any_permission("robot:manage:list", "scene:map-editor:edit")`
  - 该接口为地图编辑器画布专用（docstring 已注明），与 `bind-map` 端点同一套修法：
    机器人管理与地图编辑器任一权限通过即可，避免地图编辑器用户跨权限报错
  - import 补 `require_any_permission`（`require_permission` 仍被 `/status/list` 使用，未删）

### 前端

5 处由 `fetchGetRobotList`（`/robot/manage/list`，需 `robot:manage:list`）改调
`fetchGetAllRobots`（`/robot/manage/all`，仅需登录、返回 `RobotSimpleResponse`），
`robotList` 类型同步由 `Api.Robot.Robot[]` 收窄为 `Api.Robot.AllRobot[]`：

- `frontend/src/views/scene/map-editor/modules/property-panel.vue`（机器人总览 tab）
  - `locateRobot` / `updateRobotMap` 形参类型改 `AllRobot`；`updateRobotMap` 删除
    `AllRobot` 不具备的 `target.map_name = ...` 赋值（模板用 `sceneOptions` 渲染场景名，不读 robot.map_name）
- `frontend/src/views/operation-monitor/composables/useRobotMonitor.ts`
- `frontend/src/views/operation-monitor/modules/robot-status-card.vue`（props 类型对齐 `AllRobot`）
- `frontend/src/views/settings/modules/walking-speed-tab.vue`
- `frontend/src/views/settings/modules/voice-synthesis-tab.vue`
- `frontend/src/views/settings/modules/battery-threshold-tab.vue`
  - 后三个 tab 同时删除保存成功后对 `robot.speed_level` / `robot.battery_threshold` 的本地回写
    （`AllRobot` 无此字段；表单值来自独立 ref，列表项从未被读取，属死代码）

`robots/index.vue`（机器人管理页本身）保持调用 `fetchGetRobotList`，属合法调用。

## 关键决策

### 两种修法各司其职（沿用项目既有模式）

- **跨模块「选择机器人」下拉** → 改调 `/all` 轻量接口（无权限耦合、返回最小字段）。
  本次 5 处均属此类：地图编辑器总览、运营监控选择器、参数配置 3 个 tab 的机器人下拉。
  延续 [[2026-07-06_cross-module-dropdown-all-endpoint]] 建立的 `/all` 模式，补齐其遗漏的 5 处调用方。
- **地图编辑器专属的机器人读操作** → `require_any_permission` 叠加 `scene:map-editor:edit`。
  本次 `robot-locations` 属此类，与 `bind-map`（`require_any_permission("robot:manage:edit", "scene:map-editor:edit")`）一致。

### 为何不直接放宽 `/robot/manage/list`

`/list` 返回 `grpc_config` 等重字段且语义属机器人管理页；若给它累加 `scene/robot:config/robot:monitor`
等权限码，权限码随复用膨胀、列表语义被污染。`/all` 才是跨模块选择场景的正确出口（最小暴露）。

## 约束与备注

- 仅前端 typecheck（项目约定 [[feedback-typecheck-only]]），未做 UI 测试
- `pnpm typecheck` 通过；本次改动文件无新增类型错误（仅余 2 个与本次无关的 i18n `map-editor` 路由 key 既有错误）
- 后端 `python -m py_compile modules/robot/endpoints/robot_status_record.py` 通过
- `/all` 返回 `id/name/serial_number/map_id/status`，覆盖上述 5 处全部读取字段

## 相关文件

后端：
- `backend/modules/robot/endpoints/robot_status_record.py`

前端：
- `frontend/src/views/scene/map-editor/modules/property-panel.vue`
- `frontend/src/views/operation-monitor/composables/useRobotMonitor.ts`
- `frontend/src/views/operation-monitor/modules/robot-status-card.vue`
- `frontend/src/views/settings/modules/walking-speed-tab.vue`
- `frontend/src/views/settings/modules/voice-synthesis-tab.vue`
- `frontend/src/views/settings/modules/battery-threshold-tab.vue`

## 相关历史记忆

- [[2026-07-06_cross-module-dropdown-all-endpoint]]（建立 `/robot/manage/all` 模式，迁移 6 处下拉，遗漏本次 5 处）
- [[2026-06-30_map-editor-robot-position]]（`robot-locations` 端点原始引入，当时定为 `robot:manage:list`，本次修正为 map-editor 也可访问）
- [[2026-06-29_robot-manage-button-permissions]]（机器人管理页按钮权限码体系）

## 记录日期

2026-07-07
