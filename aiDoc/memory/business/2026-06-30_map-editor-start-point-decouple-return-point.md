# 地图编辑器「扫图起始点」返回点与 start_point 解耦

## 需求描述

地图编辑器新增场景时，自动创建的名为「扫图起始点」的返回点标注（`type: 'navigation'`）应**固定默认为世界坐标 `{0,0}`**，与场景的 `start_point_x/y` 字段**完全无关**。`start_point` 表单字段仍保持必填，继续保存到 `scene_map.start_point_x/y` 并作为坐标系原点使用。

## 状态

已完成

## 涉及范围

### 后端

无改动。`scene/map/add` 请求体与返回结构不变，`start_point_x/y` 仍正常落库。

### 前端

- 地图编辑器新增场景弹窗的创建逻辑：自动创建的「扫图起始点」返回点改为定位到**世界坐标 (0,0)** 对应的画布像素位置，再保存。
- 复用 `useMapEditor` 暴露的 `worldToPixelCoords(0, 0)` 计算像素位置；`saveMap` 的 `pixelToWorldCoords` 与其互为逆运算，保证存回世界 (0,0)。

## 约束与备注

- 原行为：自动标注加在画布像素 `(0,0)`，`saveMap` 以 `start_point` 为原点换算成世界坐标保存，结果 = `(`start_point_x`, `height×分辨率 + start_point_y`)`，随 `start_point` 变化（即二者耦合）。
- 现行为：返回点世界坐标恒为 (0,0)，不再随 `start_point` 变化。
- `start_point` 仍必填，仍作为 `pixelToWorldCoords/worldToPixelCoords` 的坐标原点（这部分不动）。
- 视觉副作用：当 `start_point` 非 0 时，世界原点 (0,0) 可能落在地图图片范围外（标注仍可在编辑器中拖动调整），这是解耦的固有结果，符合「默认 (0,0)」预期。
- 标注名仍为「扫图起始点」，类型仍为 `navigation`，满足 `validateBeforeSave` 的「至少 1 个返回点」校验。

## 相关文件

- `frontend/src/views/scene/map-editor/index.vue`（`confirmSceneSubmit` 的 add 分支）
- `frontend/src/views/scene/map-editor/composables/useMapEditor.ts`（`worldToPixelCoords` / `pixelToWorldCoords` / `addAnnotation`）
- `frontend/src/utils/coordinate.ts`（`worldToPixel` / `pixelToWorld`）

## 记录日期

2026-06-30
