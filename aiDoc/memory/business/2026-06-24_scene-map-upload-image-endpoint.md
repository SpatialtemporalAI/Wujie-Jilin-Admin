# 场景地图主图上传接口独立权限化

## 需求描述

新增/编辑场景地图时上传主图原先复用 `/admin/sys/file/upload`，要求用户额外具备系统级 `sys:file:upload` 权限，对只需管理场景地图的运营/场景管理员过重。改为 scene 模块自己的上传接口，底层仍走统一的 `FileService.upload_file`，但权限改为 `scene:map:add` 或 `scene:map:edit`。

同时修复地图编辑器保存时若关联 task 已被软删除，导致整个保存事务 500 的问题，改为静默删除点位。

## 状态

已完成

## 涉及范围

### 后端

- `backend/modules/scene/endpoints/scene_map.py`：新增 `POST /scene/map/upload-image`
  - 权限 `require_any_permission("scene:map:add", "scene:map:edit")`
  - 复用 `FileService.upload_file` + `FileService.get_image_dimensions`
  - 支持 `include_image_info=true` 返回图片宽高
  - 返回类型 `SysFileUploadResponse`，与 `/admin/sys/file/upload` 一致
- `backend/modules/task/services/task_service.py`：`delete_points_by_annotation_ids` 在"task 所有点位都被删除"分支改用 `db.get(Task, task_id)` 绕过 `TaskService.get` 的 `deleted_at` 过滤
  - task 已软删或不存在时跳过 `soft_delete()`，但 TaskPoint 仍物理删除
  - 修复编辑器保存因关联 task 已软删而整体 500 的问题

### 前端

- `frontend/src/service/api/scene.ts`：新增 `fetchUploadSceneMapImage(file, options?)`
- `frontend/src/views/scene/map/modules/scene-map-operate-drawer.vue`：上传调用从 `fetchUploadFile` 切换到 `fetchUploadSceneMapImage`

### 未改动

- 地图编辑器 `map-editor/index.vue` 仍使用 `fetchUploadFile`
- `nav_image_id` 流程未改动
- 文件管理页 `fetchUploadFile` 保留

## 约束与备注

- 不新增独立权限点 `scene:map:upload`，复用已有 `scene:map:add` / `scene:map:edit`
- 不新增 alembic 迁移
- 前端只做 typecheck（项目约定），不动 UI 测试
- TaskPoint 软删除字段保留但不主动使用，仍维持 `db.delete()` 物理删除语义

## 相关文件

- `backend/modules/scene/endpoints/scene_map.py`
- `backend/modules/task/services/task_service.py`
- `frontend/src/service/api/scene.ts`
- `frontend/src/views/scene/map/modules/scene-map-operate-drawer.vue`

## 记录日期

2026-06-24
