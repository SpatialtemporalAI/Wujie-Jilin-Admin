# 运行监控地图同步地图编辑器效果（图例 + 缩放 + 点位角度）

**日期**: 2026-07-01
**提出者**: 用户

## 需求描述

运行监控页（operation-monitor）的「实时位置」地图需同步地图编辑器（map-editor）的地图效果：

1. 左上角增加图例标注（地图名 + 颜色图例，与编辑器一致）。
2. 缩放控件改为编辑器样式（右上角竖向滑块 + +/- 按钮 + 百分比）。
3. 点位（annotation）需显示角度方向箭头（此前只画圆点 + 名称，未画朝向）。

## 状态

已完成

## 涉及范围

### 后端

无改动（纯前端，复用既有 `fetchGetEditorMapData`，annotation 已含 `angle` 字段）。

### 前端

仅改 `frontend/src/views/operation-monitor/modules/position-map-panel.vue`：

- **图例**：模板新增左上角图例浮层（`v-if="mapData"`），逐项复制编辑器 `canvas-editor.vue` 的图例（地图名 / 可行·不可行区域 / 接待点 / 返回点 / 机器人位置 / 障碍物 / 禁行区域·虚拟墙 / 电子围栏），地图名取 `mapData.map.name`。
- **缩放**：
  - `currentZoom` 由 `let` 改为 `ref` 以驱动模板百分比；新增 `sliderZoomValue` ref + `sliderThemeOverrides`。
  - 新增对数刻度换算 `sliderToZoom` / `zoomToSlider`（滑块 0-100 ↔ 倍率，与编辑器同算法）。
  - 模板将原右下角 +/-/重置 三按钮替换为编辑器同款右上角竖向 `NSlider` + 圆形 +/- 按钮；百分比文字可点击触发 `zoomReset`（保留重置能力，编辑器本身无重置按钮）。
  - `zoomIn/zoomOut/zoomReset/handleMouseWheel/loadBackgroundImage` 全部改为读写 `currentZoom.value` 并同步 `sliderZoomValue`。
- **点位角度**：`renderElements()` 的 annotation 渲染由「Group([circle,text])」改为**三个独立 fabric 对象**（circle / arrow / text，分别进 `elementMap`，key 为 `ann-${id}` / `ann-arrow-${id}` / `ann-text-${id}`），与编辑器同一做法——避免 Group bbox 重算导致圆点与 (ann.x,ann.y) 错位、进而使箭头基点偏移。箭头复用编辑器同款 `getAnnotationArrowTransform(ann.x, ann.y, ann.angle||0, ANN_RADIUS)`（ROS 弧度→Fabric：`x+dist*cos`、`y-dist*sin`、`angle=-radToDeg+90`），从 `@/utils/coordinate` 引入 `radToDeg`。
- **机器人标记配色**：圆点与名称由蓝 `#2080f0` 改为红 `#ef4444`（提取 `ROBOT_FILL` / `ROBOT_STROKE` 常量），与编辑器机器人标记及图例「机器人位置」红色项一致。

## 约束与备注

- 缩放范围保留监控页原 `MIN_ZOOM=0.5 / MAX_ZOOM=5`（未沿用编辑器的 1-5）：监控页无小地图，需允许缩小到 0.5 以纵览全图；滑块/对数换算对任意 MIN/MAX 均成立。
- annotation 坐标已在 `loadMapData` 内统一做世界→像素转换（`ann.y = height - p.y`，Y 向下），角度保持 ROS 弧度不变，故箭头换算与编辑器完全同约定。
- 机器人改红是为与新拷贝的图例（红项）保持一致；如需保留蓝色，改回 `#2080f0` 并相应改图例该项颜色即可。
- 验证：`pnpm typecheck`（本次编辑文件 0 错误，仅余与本次无关的 `scene/map/*` 历史 NaiveUI 类型报错）。

## 相关文件

- `frontend/src/views/operation-monitor/modules/position-map-panel.vue`
- 参考来源：`frontend/src/views/scene/map-editor/modules/canvas-editor.vue`（图例 / 缩放滑块 / `getAnnotationArrowTransform`）
- `frontend/src/utils/coordinate.ts`（`radToDeg`）

## 相关历史记忆

- [2026-06-18 运行监控页面滚动 + 登录后底部栏隐藏](./2026-06-18_operation-monitor-scroll-and-footer-hidden.md)
- [2026-06-30 地图编辑器显示机器人实时位置 + 修复定位](./2026-06-30_map-editor-robot-position.md)（编辑器机器人标记/角度箭头的原始实现，本次监控页与之对齐）

## 记录日期

2026-07-01
