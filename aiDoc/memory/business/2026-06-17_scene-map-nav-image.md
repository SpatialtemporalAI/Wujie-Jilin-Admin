# 场景地图新增导航地图图片

## 需求描述

场景地图/地图编辑器增加导航地图图片字段，将障碍物/禁行区域绘制到原图副本上供机器人导航使用，原图不动。

1. `scene_map` 新增 `nav_image_id` 字段，创建地图时默认与 `image_id` 同值
2. 地图编辑器保存时，触发异步任务把 `obstacle-*` 和 `restricted` 物体以纯黑色实心填充绘制到原图副本，保存为新文件并更新 `nav_image_id`
3. 更新地图主图（`image_id` 变化）时也触发同样的异步任务
4. 场景地图详情中增加导航地图图片预览

## 状态

已完成

## 涉及范围

### 后端

- 模型：`database/models/business/scene_map.py` 新增 `nav_image_id` + relationship
- 迁移：`alembic/versions/0018_scene_map_nav_image.py`
- Schema：`modules/scene/schemas/scene_map.py` Create/Update/Response 加字段
- 服务：
  - `modules/scene/services/scene_map_service.py` create 时复用 image_id
  - 新建 `modules/scene/services/scene_map_nav_image_service.py` 用 PIL 绘制并异步上传
- 端点：
  - `modules/scene/endpoints/scene_map_editor.py` save 后触发
  - `modules/scene/endpoints/scene_map.py` update image_id 变化时触发

### 前端

- `frontend/src/typings/api/scene.d.ts` SceneMap/SceneMapCreate 类型加 `nav_image_id`
- `frontend/src/views/scene/map/modules/scene-map-detail-drawer.vue` 详情中并排预览地图图片与导航地图图片

## 约束与备注

- 绘制样式：所有障碍物和禁区均纯黑色实心填充（占用栅格风格）
- 异步实现：`asyncio.create_task` 即发即忘，参考 `export_task_service`，不引入新表
- 物体坐标 x/y/width/height 已是原图像素坐标，无需坐标转换
- 异常时仅 logger.error，不影响主保存流程

## 相关文件

- backend/database/models/business/scene_map.py
- backend/modules/scene/schemas/scene_map.py
- backend/modules/scene/services/scene_map_service.py
- backend/modules/scene/services/scene_map_nav_image_service.py（新建）
- backend/modules/scene/endpoints/scene_map_editor.py
- backend/modules/scene/endpoints/scene_map.py
- backend/alembic/versions/0018_scene_map_nav_image.py（新建）
- frontend/src/typings/api/scene.d.ts

## 记录日期

2026-06-17
