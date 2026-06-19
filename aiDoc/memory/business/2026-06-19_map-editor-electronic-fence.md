# 地图编辑器电子围栏（Geofence）

## 需求描述

地图编辑器右键菜单新增「电子围栏」对象，语义与「禁行区域」相反：

- 禁行区域：内部涂黑（不可通行）
- 电子围栏：外部涂黑（围栏内可通行，围栏外全部不可通行）

1. 右键菜单在「禁行区域」之后追加「电子围栏」项
2. 点击后在点击位置出现红色矩形框（区别于蓝色障碍物、灰色禁行区域）
3. 允许添加多个电子围栏，采用 OR 语义——位于任一围栏矩形内即视为可通行，所有围栏并集之外区域涂黑
4. 保存后由后端 nav_image 生成器在生成导航地图时执行反向涂黑

## 状态

已完成

## 涉及范围

### 后端

- `modules/scene/services/scene_map_nav_image_service.py`
  - 新增 `FENCE_TYPES = {"fence", "电子围栏"}` 常量
  - `_regenerate` 中 `drawable` 过滤扩展为 `OBSTACLE_TYPES | RESTRICTED_TYPES | FENCE_TYPES`，确保只有 fence 时也触发重新生成
  - `_render` 在 `ImageDraw.Draw` 之前拆分 fences 与 others，先调用 `_apply_fence_mask` 反向遮罩
  - 新增 `_apply_fence_mask(img, fences)` 静态方法：构造 L 模式 mask，fence 矩形内填白，`Image.composite(img, black, mask)` 把并集外涂黑；越界自动裁剪到 `[0, W-1]/[0, H-1]`
  - obstacles/restricted 仍按原逻辑在合成后的图像上画黑（围栏内若有障碍物仍能被涂黑）

### 前端

- `frontend/src/views/scene/map-editor/index.vue`
  - `baseContextMenuOptions` 末尾追加 `{ label: '电子围栏', key: 'add-fence' }`
  - `handleContextMenuSelect` 加 `add-fence` 分支，默认创建 10×10 像素 fence
  - `hoverInfo` 增加 `isFence` 分支，显示 kind「电子围栏」、类型「围栏」
- `frontend/src/views/scene/map-editor/modules/canvas-editor.vue`
  - 新增颜色常量 `FENCE_FILL = 'rgba(239, 68, 68, 0.15)'`、`FENCE_STROKE = '#ef4444'`
  - `syncStructure` 加 `isFence` 判定，fillColor/strokeColor/strokeWidth 走红色分支，形状为 `Rect`（默认 width/height 10×10，非强制等边）
  - 图例在「禁行区域」后追加红色方块条目「电子围栏」

## 约束与备注

- **多围栏 OR 语义**：位于任一围栏矩形内即视为可通行，所有围栏并集之外全部涂黑（用户确认采用此方案，2026-06-19）
- 无需改 schema 与迁移：完全复用 `SceneMapObject` 数据模型，`type='fence'` 直接写入；`EditorObjectItem.type` 为字符串，无 union 约束
- fence 矩形越界时按 `min(W-1, ...)` 裁剪，不会报错；越界为 0/负尺寸时跳过
- 围栏 mask 优先于 obstacles/restricted：先合成围栏遮罩，再画障碍物，保证围栏内障碍物仍为黑色块
- 仅在围栏存在时调用 `_apply_fence_mask`，无围栏时与原有行为完全一致
- 前端验证只需 `pnpm typecheck`（参见长期偏好）
- 编辑器内 fence 可拖动、可调整大小、可删除，与现有障碍物操作一致

## 相关文件

- backend/modules/scene/services/scene_map_nav_image_service.py
- frontend/src/views/scene/map-editor/index.vue
- frontend/src/views/scene/map-editor/modules/canvas-editor.vue

## 记录日期

2026-06-19
