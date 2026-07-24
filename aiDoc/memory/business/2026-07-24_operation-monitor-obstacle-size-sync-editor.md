# 运行监控 obstacle-square 障碍物高度被强制等于宽度（3×0.5→3×3）

**日期**: 2026-07-24
**提出者**: 用户

## 需求描述

运行监控页（operation-monitor）实时位置地图上，`obstacle-square`（正方形）类型的障碍物显示尺寸与地图编辑器不一致：同一障碍物在地图编辑器里是 3×0.5（宽 3、高 0.5 的扁矩形），在运行监控里被显示成 3×3（正方形）。要求修复运行监控，使其与编辑器一致。

## 根因分析

**核心根因**：运行监控创建障碍物时对 `obstacle-square` 强制 `height = width`，且运行监控没有「创建后再用真实尺寸覆盖」的二次更新步骤，导致真实 height 被永久丢失。

两边渲染管线不同：

| 步骤 | 地图编辑器 canvas-editor.vue | 运行监控 position-map-panel.vue |
|---|---|---|
| 创建（syncStructure / renderElements 创建分支） | Rect 对 obstacle-square 强制 `height = width` | 同样强制 `height = width` |
| 二次更新（updatePositions） | **有**：`fabricObj.set({ width: obj.width, height: obj.height })` 用真实值覆盖 | **无**：renderElements 只渲染一次（loadMapData 内 clearMapState 后调用，elementMap 始终为空，永远走创建分支） |

编辑器虽有同样的 isSquare 强制，但 `renderElements = syncStructure() + updatePositions()`，`updatePositions`（[canvas-editor.vue:587](frontend/src/views/map-editor/modules/canvas-editor.vue#L587)）立即用真实 `obj.height` 覆盖 → 编辑器显示真实 3×0.5。运行监控只创建、不覆盖 → height 被卡在 width → 显示 3×3。

数据流确认（后端 `fetchGetEditorMapData` ↔ `GET /admin/scene/map/{id}/editor/data`）：
- `objects`（障碍物）x/y/width/height 存**画布像素**，后端原样存取，前端直接使用（不做坐标转换）。
- 用户的障碍物 width/height 都有真实值（非 0），所以不是数据缺失问题，纯是渲染逻辑差异。

> 注：调查中一度误判为「width/height 缺失（DB 默认 0）时兜底默认值不一致（编辑器 5 / 运行监控 10）」，但用户反馈「编辑器 3×0.5、运行监控 3×3」表明数据有真实值，遂定位到 isSquare 强制才是真根因。默认值差异仅在 width/height 为 0 时触发，本次一并做防御性对齐（见下）。

## 修复

### 核心修复（解决 3×3 问题）

`frontend/src/views/operation-monitor/modules/position-map-panel.vue` renderElements 创建分支的 Rect 分支：去掉 `obstacle-square` 的 `isSquare ? (obj.width) : (obj.height)` 强制，直接用真实 `obj.height`：

```ts
} else {
  fabricObj = new Rect({
    ...commonOpts,
    width: obj.width || 5,
    height: obj.height || 5   // 不再 isSquare ? width : height
  });
}
```

运行监控只渲染一次、无 updatePositions 二次覆盖，必须在这里就用真实 height；编辑器 syncStructure 的 isSquare 强制是「创建即被 updatePositions 覆盖」的死逻辑，运行监控不能照搬。

### 配套防御性对齐（非本次问题主因，但消除潜在不一致）

1. `position-map-panel.vue` 创建分支兜底默认值与编辑器 syncStructure 对齐：`obstacle-triangle`、普通 Rect 由 `|| 10` 改 `|| 5`；新增 `isFence` 独立分支（`|| 10`）。
2. `position-map-panel.vue` 更新分支（elementMap 已存在对象的增量更新）补 width/height/rx/ry 同步，与编辑器 updatePositions 口径一致（此前只更新 left/top/angle）。当前不走该分支，属防御性。
3. `frontend/src/views/map-editor/modules/canvas-editor.vue` `updatePositions` 对 Rect/Triangle 的 width/height 加 `|| 5` 兜底，避免 width=0 时图形塌缩，与 syncStructure 创建口径一致。

## 验证

- `pnpm typecheck`（涉及文件 0 错误）。

## 备注

- 编辑器 syncStructure 里对 obstacle-square 的 `height=width` 强制被 updatePositions 覆盖，属冗余逻辑；本次未清理编辑器 syncStructure（编辑器最终显示正确，最小改动）。运行监控已直接用真实 height。
- `obstacle-circle`（Ellipse，rx/ry）、`fence`（电子围栏）、`restricted`（多边形，走 points）不受 isSquare 影响。

## 相关文件

- `frontend/src/views/operation-monitor/modules/position-map-panel.vue`（renderElements 创建/更新分支）
- `frontend/src/views/map-editor/modules/canvas-editor.vue`（updatePositions 兜底；syncStructure 的 isSquare 为冗余死逻辑）

## 相关历史记忆

- [2026-07-01 运行监控地图同步地图编辑器效果](./2026-07-01_operation-monitor-map-sync-editor.md)（运行监控对齐编辑器的图例/缩放/点位，本条是其延续：障碍物尺寸渲染对齐）

## 记录日期

2026-07-24
