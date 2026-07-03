---
name: scene-map-form-required-validation
description: 场景地图新增/编辑核心字段必填校验
metadata:
  type: business
---

# 2026-07-03 场景地图新增/编辑核心字段必填

## 需求

场景地图新增/编辑时，核心基础信息字段必填，不允许为空。前后端均做校验。`状态` 与 `所属分组` 不在新增/编辑表单中填写，由后端默认值管理。

## 必填字段

| 字段 | 说明 | 前端控件 |
|------|------|----------|
| `name` | 地图/场景名称 | NInput |
| `image_id` | 地图/场景图片 | NUpload |
| `width` | 地图宽度（像素） | 图片上传后自动回填 |
| `height` | 地图高度（像素） | 图片上传后自动回填 |
| `resolution` | 映射比例 | NInputNumber |
| `start_point_x` | 扫图起始点X | NInputNumber |
| `start_point_y` | 扫图起始点Y | NInputNumber |

## 不在表单中填写的字段

| 字段 | 后端行为 |
|------|----------|
| `status` | 创建默认 `True`（启用），更新时不传则保持原值 |
| `group_id` / `group_name` | 不传则保持 `null`（未分组） |

## 涉及文件

- 前端地图管理抽屉：`frontend/src/views/scene/map/modules/scene-map-operate-drawer.vue`
- 前端地图编辑器：`frontend/src/views/scene/map-editor/index.vue`
- 前端类型：`frontend/src/typings/api/scene.d.ts`
- 后端接口校验：`backend/modules/scene/schemas/scene_map.py`
- 边界文档：`aiDoc/frontend-backend/boundary.md`

**Why:** 保证场景地图基础信息完整，同时简化表单，将状态和分组交由后端默认值或其他入口管理。

**How to apply:** 新增/编辑场景地图时，前端仅提交核心字段；后端 `SceneMapCreate` / `SceneMapUpdate` 核心字段必填，`status` 与分组字段可选。
