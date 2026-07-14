---
name: scene-map-create-builtin-return-point
description: 新增地图时「扫图起始点」返回点改由后端 scene/map/add 直接创建，去掉前端 /editor/save 调用
metadata:
  type: business
---

# 2026-07-14 新增地图返回点创建下沉到后端

## 需求 / 背景

新增地图（`POST /admin/scene/map/add`）后，前端原先需要再调一次 `POST /admin/scene/map/{id}/editor/save`，目的是把固定的「扫图起始点」返回点（世界坐标 (0,0)，`type=navigation`）写入并让 `version` 自增。本次优化将该逻辑下沉到后端创建接口，省去一次 HTTP 往返与「空地图（无导航点）」中间态。

## 原链路

前端 `map-editor/index.vue` `confirmSceneSubmit` 新增分支：

```
fetchCreateSceneMap → switchMap(loadMap) → editor.addAnnotation(扫图起始点, 世界0,0) → editor.saveMap({silent:true})
```

`saveMap` 对应后端 `SceneMapEditorService.save_editor_data`：
- 插入「扫图起始点」标注
- `map_obj.version += 1`

而后端 `SceneMapService.create` 只建 `SceneMap` 元数据行，`version` 默认 0，**不建任何标注**——返回点完全靠前端那次 save 补。

## 实现

### 后端

`SceneMapService.create`（`backend/modules/scene/services/scene_map_service.py`）：`flush` 拿到 `map_obj.id` 后追加：

- `db.add(SceneMapAnnotation(map_id=map_obj.id, x=0, y=0, name="扫图起始点", type="navigation"))`
- `map_obj.version = 1`（等价于「已保存一次内容」）

### 前端

`frontend/src/views/map-editor/index.vue` `confirmSceneSubmit` 新增分支：删除 `addAnnotation(...)` + `saveMap({ silent: true })`；`switchMap → loadMap` 会自动载入后端建好的返回点。

## 约束与备注

- `annotation.x/y` 存**世界坐标**，后端写死 (0,0) 与前端原 `worldToPixelCoords(0,0)→画布→pixelToWorldCoords 回 (0,0)` 完全等价
- `save_editor_data` 本身**不触发 `NotifyMapSaved`**（广播在 `scene_map_nav_image_service`）→ 去掉 save 不影响 gRPC 广播
- `SceneMapService.create` 全仓仅 `scene/map/add` 一个调用方（Grep 确认，无 openapi/导入/迁移入口）→ 改 create 影响面可控
- 仅影响**未来新建**的地图；存量地图已有返回点，不受影响
- 符合既有决策：返回点固定世界坐标 (0,0)，与 `start_point` 无关（见 [2026-06-30 返回点与 start_point 解耦](./2026-06-30_map-editor-start-point-decouple-return-point.md)）

## 相关文件

- `backend/modules/scene/services/scene_map_service.py`（`create`）
- `frontend/src/views/map-editor/index.vue`（`confirmSceneSubmit` 新增分支）
- 模型：`backend/database/models/business/scene_map_annotation.py`（必填 map_id/x/y/name/type，angle 默认 0）

## 记录日期

2026-07-14
