# 场景地图新增映射比例输入

## 需求描述

场景地图管理在新增和编辑场景地图时增加映射比例 `resolution` 输入，默认值为 1。

## 状态

已完成

## 涉及范围

### 后端

- 场景地图模型 `resolution` 默认值调整为 1
- 创建场景地图 schema 的 `resolution` 默认值调整为 1
- 新增迁移调整数据库字段默认值

### 前端

- 场景地图新增/编辑抽屉表单增加“映射比例”输入项
- 新增时默认填入 1，编辑时回显已有 `resolution`
- 提交新增/编辑时携带 `resolution`

## 约束与备注

- `resolution` 字段沿用既有前后端字段名，不新增额外字段。
- 仅调整场景地图管理新增/编辑流程，不改变地图编辑器坐标逻辑。

## 相关文件

- backend/database/models/business/scene_map.py
- backend/modules/scene/schemas/scene_map.py
- backend/alembic/versions/0019_scene_map_resolution_default.py
- frontend/src/views/scene/map/modules/scene-map-operate-drawer.vue
- frontend/src/typings/api/scene.d.ts

## 记录日期

2026-06-17
