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

- `nav_image_id` 流程未改动
- 文件管理页 `fetchUploadFile` 保留

### 后续补丁（2026-06-24 当天）

- 地图编辑器 `frontend/src/views/scene/map-editor/index.vue` 的 `handleSceneUpload`（新增场景上传图片）改为独立的 `fetchUploadSceneMapEditorImage`，不再共用场景地图菜单的上传接口
  - 此前曾简单替换为 `fetchUploadSceneMapImage`，但该接口权限是 `scene:map:add/edit`，对只有"地图编辑器"菜单权限的用户仍会 403
  - **正确权限边界**：场景地图菜单和地图编辑器菜单权限严格分离
    - 场景地图菜单上传 → `POST /scene/map/upload-image`（权限 `scene:map:add/edit`），由 `scene-map-operate-drawer.vue` 调用 `fetchUploadSceneMapImage`
    - 地图编辑器菜单上传 → `POST /scene/map-editor/upload-image`（权限 `scene:map-editor:add/edit`），由 `map-editor/index.vue` 调用 `fetchUploadSceneMapEditorImage`
- 后端在 `backend/modules/scene/endpoints/scene_map_editor.py` 新增 `scene_map_editor_public_router`（prefix `/map-editor`，不依赖 map_id），承载新增场景时无 map_id 的接口
- `backend/modules/scene/router.py` 挂载新 router（`/scene/map-editor`）
- `getFilePreviewUrl` 仍从 `@/service/api/file` 导入（仅根据 file id 拼预览 URL，不走权限）

### 后续补丁 2：上传后无法重新上传（2026-06-24 当天）

- 现象：场景地图/地图编辑器弹窗里上传图片成功后，再次点击"选择图片"无响应
- 根因：`NUpload :max="1"` 在文件上传成功后保留内部文件计数，即使 `:show-file-list="false"` 不显示列表，下次选择仍被 `max` 拦截
- 修复：两处上传组件（`scene-map-operate-drawer.vue` 与 `map-editor/index.vue`）都加 `v-model:file-list`，并在 `handleUpload` / `handleSceneUpload` 的 `finally` 中清空 `uploadFileList.value = []`
- 类型：`import type { UploadFileInfo } from 'naive-ui'`

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
