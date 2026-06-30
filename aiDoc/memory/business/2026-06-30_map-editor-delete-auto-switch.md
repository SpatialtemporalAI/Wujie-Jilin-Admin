# 地图编辑器删除地图后自动切换到第一个

## 需求描述

地图编辑器中，删除当前正在查看的地图后，画布会变空白。应改为**自动切换到列表第一个地图**，避免编辑器空载。

## 状态

已完成

## 涉及范围

### 后端

无改动。

### 前端

- `useMapEditor.deleteScene`：删除后若删除的正是当前选中地图（`selectedMapId === id`）且刷新后列表仍有地图，则自动 `loadMap(sceneList[0].id)`。

## 约束与备注

- 仅当删除的是当前选中地图时才自动切换；删除非当前地图时不影响当前画布。
- 列表为空（最后一张被删）时仍清空选中，不报错。
- 复用 `onMounted` 中"取列表第一项加载"的既有模式。

## 相关文件

- `frontend/src/views/scene/map-editor/composables/useMapEditor.ts`（`deleteScene`）

## 记录日期

2026-06-30
