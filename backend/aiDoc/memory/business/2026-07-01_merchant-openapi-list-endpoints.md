# 商户开放 API 新增场景/任务/点位列表接口

## 需求描述

现有商户开放 API（`/openapi/v1`，HMAC 签名鉴权）只有 7 个动作类接口（导航/任务控制/语音），第三方商户无法查询自己能操作哪些场景、任务、点位。新增 3 个列表查询接口，补齐"发现可用资源"能力：列出可访问场景 → 取场景下点位 → 列出可执行任务。

## 状态

已完成

## 涉及范围

### 后端

- `backend/modules/merchant/schemas/openapi.py`：新增 `ScenesRequest` / `PointsRequest` / `TasksRequest` 三个请求 Schema（继承 `BaseEntity`）。
- `backend/modules/merchant/services/openapi_service.py`：
  - 新增 helper `_merchant_robot_ids` / `_merchant_scene_ids`（取商户绑定的机器人ID集合、及其 `map_id` 去重去 NULL 的场景ID集合）。
  - 新增 `list_scenes` / `list_points` / `list_tasks` 三个 public 方法，返回 `OpenApiResult`。
  - `list_points` 复用 `SceneMapAnnotationService.get_list(db, map_id)`。
- `backend/modules/merchant/endpoints/openapi.py`：新增 3 个 POST 路由 `/openapi/v1/scenes`、`/points`、`/tasks`。

### 前端

无。开放 API 面向第三方商户，不涉及 admin 前端，未同步 `aiDoc/frontend-backend/`。

## 接口契约

| 方法 | 路径 | 请求体 | 返回 data |
|---|---|---|---|
| POST | `/openapi/v1/scenes` | `{robot_sn?: str}` | `{scenes: [{id,name,width,height,status,version}]}` |
| POST | `/openapi/v1/points` | `{map_id: int}` | `{points: [{id,name,type,x,y,angle}]}` |
| POST | `/openapi/v1/tasks` | `{robot_sn?,map_id?,task_type?,status?}` | `{tasks: [{id,name,task_type,status,enabled,map_id,last_run_at,next_run_at}]}` |

## 约束与备注

- **必须用 POST + body 参数**：`ApiKeyService.build_string_to_sign` 的签名串 `path` 不含 query string（仅 `method/path/timestamp/nonce/body_sha256`），GET 的查询参数不会被签名覆盖，存在篡改风险；与现有 7 个接口保持一致全用 POST。
- **不分页**：与现有开放接口风格一致，列表直接放进 `OpenApiResult.data` 的语义键。
- **任务可见范围 = 按机器人归属**：经 `task_robot` 关联到该商户机器人的任务（与 `execute_task(robot_sn+task_id)` 的 robot 驱动语义一致）；可选 `map_id/task_type/status` 过滤。
- **点位可见性校验**：`map_id` 必须在商户可访问场景集合内，否则 `ForbiddenError`。
- **场景/任务过滤软删除**（`deleted_at is null`）；点位沿用 `SceneMapAnnotationService.get_list`（不过滤 `deleted_at`，与后台列表行为一致）。
- 时间字段（`last_run_at`/`next_run_at`）在 service 内转 ISO 字符串后再放入 `data`。

## 相关文件

- backend/modules/merchant/endpoints/openapi.py
- backend/modules/merchant/services/openapi_service.py
- backend/modules/merchant/schemas/openapi.py

## 记录日期

2026-07-01
