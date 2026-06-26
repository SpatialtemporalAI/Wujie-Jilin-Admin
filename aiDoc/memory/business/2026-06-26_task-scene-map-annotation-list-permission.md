# 任务管理选地图后加载点位 403

## 需求描述

任务管理-任务列表，新增/编辑任务时进入抽屉，前端为「场景地图」下拉拉起
`GET /scene/map/list`（已修复，详见
[[2026-06-26_task-scene-map-list-and-grpc-retry-dedup]]）后，
紧接着为已选地图拉取点位 `GET /scene/map/{map_id}/annotation/list`，
axios 拦截器再次冒出红色提示「没有操作权限: scene:map:list」，
点位列表为空导致后续巡逻点位无法选择。

根因：`scene_map_annotation.py` 的 `/list` 端点权限仍是
`require_permission("scene:map:list")` 单权限，只持有 `task:list` 的用户被挡。

## 状态

已完成

## 涉及范围

- `backend/modules/scene/endpoints/scene_map_annotation.py`
  - import 增加 `require_any_permission`
  - `GET /scene/map/{map_id}/annotation/list` 权限从 `scene:map:list` 扩展为
    `require_any_permission(scene:map:list, scene:map-editor:list, task:list)`
  - 仅放宽 annotation 只读 list；add/edit/delete 仍保持 `scene:map:edit` 不变
  - `scene_map_object.py` / `scene_map_path.py` 的 `/list` 端点暂未放宽：
    任务管理抽屉不调用 object/path，按最小授权不一起动

## 关键决策

### 复用 task:list，沿用上次策略

- 与 [[2026-06-26_task-scene-map-list-and-grpc-retry-dedup]] 中
  `/scene/map/list` 的修法一致：「后端权限 OR」根治，避免前端容错兜底
- 不引入新权限点，避免菜单/权限点膨胀
- 持有 `task:list` 的任务模块用户即可正常加载巡逻点位

### 不放宽 object / path

- 任务管理抽屉（`task-operate-drawer.vue`）只调用 `fetchGetMapAnnotations`
- `fetchGetMapObjects` / `fetchGetMapPaths` 仅在场景管理详情抽屉使用，
  该场景本就有 `scene:map:list`
- 按最小授权原则不动它们；如未来其他模块复用，再单独放宽

## 验证方案

- 仅 `task:list` 权限的用户 → 任务管理 → 编辑已有任务（带 map_id）
  - 期望：抽屉打开后点位列表正常加载，无 403 提示
- 仅 `task:list` 权限的用户 → 任务管理 → 新增任务 → 选择场景地图
  - 期望：触发 `handleMapChange` 后点位列表（如已选地图）可正常加载
- 仅 `scene:map:list` 权限的用户 → 行为不变

### 静态检查

- `python -m py_compile modules/scene/endpoints/scene_map_annotation.py` 通过

## 相关文件

后端：
- `backend/modules/scene/endpoints/scene_map_annotation.py`

## 记录日期

2026-06-26
