# 地图编辑器显示机器人实时位置 + 修复定位

**日期**: 2026-06-30
**提出者**: 用户

## 需求描述

1. 地图编辑器画布上显示当前地图所绑定机器人的实时位置。
2. 修复右侧「机器人总览」的「定位」按钮（此前恒提示「机器人暂无定位信息」）。

## 背景（关键）

- 机器人位置存在 `robot_status_record` 表的两个字段：`location_info`(JSON `{x,y,angle,update_at}`) 与 `location`(Text，历史 JSON 字符串)。
- **位置数据由外部方式直接写入 DB**（不在本仓库代码内）；平台代码此前**从未**写入这两个字段（只有创建机器人时初始化 `location_info={}`）——这是定位失效、画布无位置可显示的根因。
- 经与用户确认：本次**只做平台侧**（读取/展示/定位），不实现机器人端上报。

## 状态

已完成

## 涉及范围

### 后端（纯只读新增，无写入改动、无 DB 迁移、无 proto 变更）

- `backend/modules/robot/schemas/robot_status_record.py`：新增 `RobotLocationItem{id,name,status,map_id,location_info,location}`（`location_info` 复用 `LocationInfoData` 并带脏数据归一化）。
- `backend/modules/robot/services/robot_status_record_service.py`：新增 `get_map_robot_locations(db, map_id)`，`robot` JOIN `status_record`（`selectinload(Robot.status_record)`）按 `map_id` 取机器人，透传两个字段。
- `backend/modules/robot/endpoints/robot_status_record.py`：新增 `GET /robot/manage/map/{map_id}/robot-locations`，权限 `robot:manage:list`（与右侧机器人总览 `fetchGetRobotList` 一致）。

### 前端

- `frontend/src/typings/api/robot.d.ts`：新增 `RobotLocationItem` 类型（复用既有 `LocationInfo`）。
- `frontend/src/service/api/robot.ts`：新增 `fetchGetMapRobotLocations(mapId)`。
- `frontend/src/views/scene/map-editor/utils/robot-location.ts`（新文件）：`extractRobotPoint(src)` 统一解析坐标——`location_info.x/y` 优先，为空则 `JSON.parse(location)`，再失败则从字符串提取前两个数字；失败返回 `null`。**「定位」与「画布显示」共用**，消除两处分歧。
- `frontend/src/views/scene/map-editor/modules/property-panel.vue`：`locateRobot` 改用 `extractRobotPoint`（修复定位——此前直接读 `location_info.x/y`，外部若写到 `location` 文本则失效）。
- `frontend/src/views/scene/map-editor/modules/canvas-editor.vue`：
  - 新增 prop `robotLocations`；模块级 `robotMarkers: Map<number, Group>`。
  - `renderRobots()`：世界坐标(米)→像素（与 `worldToPixelCoords` 同公式：`px=(x-start_x)/res`、`py=height-(y-start_y)/res`），创建/更新蓝色 `Group`（圆+名称），`selectable/evented/hasControls=false`、`excludeFromExport=true`、不进 `elementMap` → **不参与选中/保存/导出**。
  - `renderElements()` 末尾调 `renderRobots()` 保证置于顶层；`watch(robotLocations)` 触发刷新；地图切换 watcher 与 `onBeforeUnmount` 调 `clearRobotMarkers`。
- `frontend/src/views/scene/map-editor/index.vue`：新增 `robotLocations` ref + `loadRobotLocations` + 5s 轮询（常量 `ROBOT_LOCATION_POLL_MS=5000`）；`watch(editor.selectedMapId)` 集中处理「初始加载/选地图/新建场景」时的轮询启停与清空；`onBeforeUnmount` 清理；传 `:robot-locations` 给 `<CanvasEditor>`。

## 关键业务规则

- 位置坐标系：机器人上报的 x/y 假定为与点位 annotation 同的世界坐标系（米，原点 `map.start_point_x/y`，Y 轴向上）。若机器人上报帧不一致，画布位置会偏移——属标定问题，需核对机器人端帧定义。
- 「定位」与「画布显示」均先读 `location_info` 再兜底 `location` 文本，兼容外部写入任一字段。
- 机器人标记是纯视觉装饰层：不进 `editorData`、不落库、不进导出图、不影响点位/障碍物保存。

## 约束与备注

- 不实现机器人端上报（数据由外部写入）。
- 轮询固定 5s；切换地图/卸载即停。
- 验证：`pnpm typecheck`（编辑的文件 0 错误，仅余与本次无关的 `map-editor` 路由 i18n key 历史报错）、`python -m py_compile` 三个后端文件通过。

## 相关文件

- `backend/modules/robot/schemas/robot_status_record.py`
- `backend/modules/robot/services/robot_status_record_service.py`
- `backend/modules/robot/endpoints/robot_status_record.py`
- `frontend/src/typings/api/robot.d.ts`
- `frontend/src/service/api/robot.ts`
- `frontend/src/views/scene/map-editor/utils/robot-location.ts`
- `frontend/src/views/scene/map-editor/modules/property-panel.vue`
- `frontend/src/views/scene/map-editor/modules/canvas-editor.vue`
- `frontend/src/views/scene/map-editor/index.vue`

## 相关历史记忆

- [2026-06-11 地图编辑器机器人定位与绑定场景](./2026-06-11_map-editor-robot-location-binding.md)（初版定位逻辑读 `location` 文本；本次改为 `location_info` 优先 + `location` 兜底，并新增画布显示）

## 记录日期

2026-06-30
