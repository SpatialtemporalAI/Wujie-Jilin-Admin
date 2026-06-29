# 地图编辑器点位落障碍物拦截

## 需求描述

地图编辑器右键添加点位时，如果点击位置落在障碍物上，则拦截添加并提示「注意：点位不能设置在障碍物上！」。

## 状态

已完成

## 涉及范围

### 后端

无变更。

### 前端

- `frontend/src/views/scene/map-editor/index.vue`
  - `handleContextMenuSelect` 的 `add-point` 分支开头新增判断：若右键 `contextMenuTarget` 是 `object` 且其 `type` 以 `obstacle-` 开头（圆形/三角形/正方形障碍物），则清空 `contextMenuTarget`、`window.$message.warning('注意：点位不能设置在障碍物上！')` 并 `return`，不执行 `addAnnotation`。
  - 复用已有的右键命中检测（canvas-editor 的 `findElementAtScenePoint` → `context-menu` 事件的 `target`），无需新增几何判断。

## 约束与备注

- 当前仅拦截障碍物（`obstacle-circle` / `obstacle-triangle` / `obstacle-square`），**不**拦截「禁行区域」(restricted) 与「电子围栏」(fence)，与提示文案「障碍物」一致。
- 判定依据是右键时已捕获的 `contextMenuTarget`（命中 object 层），与编辑器其余交互的命中口径一致。
- 前端验证只需 `pnpm typecheck`（参见长期偏好）。

## 相关文件

- frontend/src/views/scene/map-editor/index.vue

## 记录日期

2026-06-29
