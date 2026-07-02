# 运行监控：机器人未绑定场景地图时不显示机器人点位

**日期**: 2026-07-02
**提出者**: 用户

## 需求描述

运行监控页（operation-monitor）「实时位置」地图：当机器人未绑定场景地图（`map_id` 为空）时，不应显示机器人实时点位（红色圆点 + 方向箭头 + 名称），仅保留「该机器人未绑定场景地图」的空状态占位。

## 状态

已完成

## 涉及范围

### 后端

无改动（纯前端）。

### 前端

仅改 `frontend/src/views/operation-monitor/modules/position-map-panel.vue` 的 `renderRobotMarker()`：在移除旧标记后、渲染新标记前，新增 `if (!mapData.value) return;` 守卫（位于 `if (!props.location) return;` 之前）。

## 约束与备注

- **根因**：原 `renderRobotMarker()` 只判断 `if (!props.location) return;`（机器人是否上报位置），未判断是否绑定场景地图。未绑定时 `mapData` 为 null，但只要 `parsedLocation` 有值，`watch(location)` 仍会触发渲染——`worldToCanvasPoint` 在 `mapData?.map` 为空时退化为默认坐标系（start_point=0、resolution=0.2、height=canvasHeight），在空白画布上画出一个无意义的红点（NEmpty 占位层背景透明，红点透出可见）。
- **用 `mapData.value` 而非 `props.mapId` 作判断**：`mapData` 只在地图数据成功加载后才非空，能同时覆盖「未绑定（mapId 为 null）」与「绑定了但加载失败」两种情况，比单独判 mapId 更稳妥。
- 切换机器人时 `watch(mapId)` 走 `clearMapState()` 已清除 robotMarker 并置 `mapData=null`；加守卫后，后续 `location` 变化触发 `renderRobotMarker` 不会在无图状态下重画点位。
- 地图加载完成后 `loadMapData` 末尾会显式调用 `renderRobotMarker()`，故加守卫不影响正常已绑定地图的点位显示。
- 验证：`pnpm typecheck`。

## 相关文件

- `frontend/src/views/operation-monitor/modules/position-map-panel.vue`（`renderRobotMarker`）
- `frontend/src/views/operation-monitor/composables/useRobotMonitor.ts`（`parsedLocation` / `selectedRobot.map_id`）

## 相关历史记忆

- [2026-07-01 运行监控地图同步地图编辑器效果](./2026-07-01_operation-monitor-map-sync-editor.md)（机器人标记三件套 body/arrow/label 的来源，本次在它入口加守卫）

## 记录日期

2026-07-02
