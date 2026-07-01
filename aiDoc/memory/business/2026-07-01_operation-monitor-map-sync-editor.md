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
- **滚轮缩放定位**：`zoomToPoint` 需传入画布相对坐标；画布嵌在卡片内（有头部/内边距偏移），必须用 `evt.offsetX/offsetY`，不能用 `clientX/clientY`（视口坐标会让缩放定点漂移）。地图编辑器 `canvas-editor.vue` 同此问题，已一并改为 `offsetX/offsetY`。
- **标记固定屏幕大小**：缩放时点位标记（圆点/方向箭头/名称）与机器人标记保持固定屏幕尺寸（不随地图变大变小，像地图大头针），而底图/障碍物/路径仍随视口缩放。实现：新增 `applyMarkerZoom()`（**无参，内部读 `fabricCanvas.getZoom()` 视口真实 zoom**，避免与 `currentZoom` 状态不同步）——对每个标记对象做 `scaleX=scaleY=1/zoom` 反向缩放（与视口 zoom 相消→屏幕尺寸恒定），`left/top` 仍为场景坐标（位置随地图走）；箭头位置用 `getAnnotationArrowTransform(...,zoom)` 把屏幕半径换算成 `半径/zoom` 的场景距离、文字 `top` 用 `ann.y + ANN_LABEL_OFFSET/zoom`，保证屏幕间距恒定。在 `renderElements` 末尾、`renderRobotMarker` 创建后（初始缩放也用 `getZoom()`）、以及 `handleMouseWheel/zoomIn/zoomOut/zoomReset/handleSliderZoom` 五处缩放入口调用。`getAnnotationArrowTransform` 新增 `zoom=1` 形参。
- **切换地图标记大小跳变修复**：`loadMapData` 在 `clearMapState` 后显式 `fabricCanvas.setZoom(1)` 并重置 `currentZoom/sliderZoomValue`（无图分支补 `centerContent()`）。原因：原 `loadBackgroundImage` 只重置 `currentZoom.value=1` 而未重置视口真实 zoom，导致缩放下切图时状态(1)与视口(旧 zoom)不同步，点位按错误 zoom 反向缩放→大小跳变；改用 `getZoom()` + 切图时重置视口双重兜底。

## 后续：地图编辑器同步同一套缩放逻辑（2026-07-01）

用户要求"将地图编辑器的缩放逻辑同步这里的"，即把上述固定屏幕大小标记 + 切图跳变修复也应用到编辑器 `frontend/src/views/scene/map-editor/modules/canvas-editor.vue`：

- `getAnnotationArrowTransform` 新增 `zoom=1` 形参（与监控页同）。
- 新增 `applyMarkerZoom()`（无参，读 `fabricCanvas.getZoom()`）：对 annotation circle（**可交互**，仅设 `scaleX=scaleY=1/zoom`，不影响位置/角度/数据模型/保存）+ 其角度箭头/名称（`annotationDecorations`）+ 机器人标记（`robotMarkers` 的 circle/arrow/label，箭头位置由 `arrow.angle` 反推 ROS 弧度后按 zoom 重算）做反向缩放。
- 调用点：`updatePositions` 末尾、`renderRobots` 末尾（覆盖 renderElements/拖动提交/robotLocations 轮询）、`handleMouseWheel/zoomIn/zoomOut/zoomReset/handleSliderZoom` 五个缩放入口。
- 实时拖动/旋转路径（`handleObjectMoved`/`handleObjectRotating` 的 annotation 分支）改为 zoom 感知：文字 `top` 用 `ANN_LABEL_OFFSET*inv`、箭头 `getAnnotationArrowTransform(...,zoom)`，避免缩放下拖动时箭头漂浮（提交后由 `updatePositions→applyMarkerZoom` 兜底）。
- 切图跳变修复：`loadBackgroundImage` 在 `centerContent()` 前 `fabricCanvas.setZoom(1)`（编辑器原本同样只重置 `currentZoom=1` 未重置视口）。
- 验证：`pnpm typecheck`（canvas-editor.vue 0 错误；另有与本次无关的 `findAnnotationAtPoint`/`seq` 未使用 hint）。
- 验证：`pnpm typecheck`（本次编辑文件 0 错误，仅余与本次无关的 `scene/map/*` 历史 NaiveUI 类型报错）。

## 后续：机器人标记朝向角度修复（2026-07-01）

**现象**：运行监控地图上机器人方向箭头的朝向始终不变（角度无变化）。

**根因**：机器人标记 `robotMarker` 是 fabric `Group([body, arrow, label])`，其 `angle` 此前直接写 `props.location.angle || 0`。但 `props.location.angle` 与 annotation 同为 **ROS 弧度**（0 朝东、π/2 朝北、逆时针为正），被 Fabric 当作「度」直接旋转——弧度取值 0~6.28 仅对应 0~6.28°，肉眼几乎不可见，故表现为角度不变。上次同步编辑器时 annotation 箭头已用 `getAnnotationArrowTransform` 做弧度→度转换，但机器人标记 Group 的 angle 漏了。

**修复**（`position-map-panel.vue` 的 `renderRobotMarker` 内 Group 构造）：`angle` 改为 `-radToDeg(props.location.angle || 0) + 90`，与 annotation 方向箭头同一公式——arrow 在 Group 内默认顶点朝上（北）、Fabric 顺时针为正，ROS 弧度→Fabric 度的换算同为 `-radToDeg(rad)+90`。`radToDeg` 早已从 `@/utils/coordinate` 引入，无需新增依赖。

**验证**：`pnpm typecheck`（本次编辑文件 0 错误，仅余与本次无关的 `scene/map/*` 历史 NaiveUI 类型报错）。

## 相关文件

- `frontend/src/views/operation-monitor/modules/position-map-panel.vue`
- 参考来源：`frontend/src/views/scene/map-editor/modules/canvas-editor.vue`（图例 / 缩放滑块 / `getAnnotationArrowTransform`）
- `frontend/src/utils/coordinate.ts`（`radToDeg`）

## 相关历史记忆

- [2026-06-18 运行监控页面滚动 + 登录后底部栏隐藏](./2026-06-18_operation-monitor-scroll-and-footer-hidden.md)
- [2026-06-30 地图编辑器显示机器人实时位置 + 修复定位](./2026-06-30_map-editor-robot-position.md)（编辑器机器人标记/角度箭头的原始实现，本次监控页与之对齐）

## 记录日期

2026-07-01
