---
name: scene-map-form-required-validation
description: 场景地图新增/编辑表单所有选项必填校验
metadata:
  type: business
---

# 2026-07-03 场景地图新增/编辑所有选项必填

## 需求

地图编辑器（场景地图）新增/编辑抽屉中，所有选项均必填，不允许为空。校验同时在前端表单与后端接口层实现。

## 涉及字段

| 字段 | 说明 | 前端控件 |
|------|------|----------|
| `name` | 地图名称 | NInput |
| `group_id` / `group_name` | 所属分组（选择已有分组或输入新分组名） | NSelect(filterable+tag) |
| `image_id` | 地图图片 | NUpload |
| `width` | 地图宽度（像素） | 图片上传后自动回填 |
| `height` | 地图高度（像素） | 图片上传后自动回填 |
| `resolution` | 映射比例 | NInputNumber |
| `start_point_x` | 扫图起始点X | NInputNumber |
| `start_point_y` | 扫图起始点Y | NInputNumber |
| `status` | 状态 | NRadioGroup |

## 实现位置

- 前端表单校验：`frontend/src/views/scene/map/modules/scene-map-operate-drawer.vue`
- 前端类型：`frontend/src/typings/api/scene.d.ts`
- 后端接口校验：`backend/modules/scene/schemas/scene_map.py`
- 边界文档：`aiDoc/frontend-backend/boundary.md`

## 后端分组特殊规则

创建接口（`POST /scene/map/add`）中 `group_id` 与 `group_name` 二选一：
- 选择已有分组 → 传 `group_id`
- 输入新分组名 → 传 `group_name`（后端自动创建分组）
- 两者不能同时为空

更新接口（`PUT /scene/map/{id}`）中 `group_id` 必填，不再支持用 `group_name` 创建新分组。

## 状态字段桥接

- 前端展示/编辑：`"1"`（启用） / `"2"`（禁用）
- 后端请求体：`bool`（`true` / `false`）
- 转换由 `src/utils/status.ts` 的 `enableStatusToBoolean()` 在 API 层统一处理

**Why:** 避免用户提交空字段导致数据不完整，同时通过前后端双重校验防止绕过前端校验。

**How to apply:** 新增/编辑场景地图时，所有字段均需在表单和 Schema 中标记为必填；图片上传失败或未上传时禁止提交；分组二选一逻辑保持并加后端校验。
