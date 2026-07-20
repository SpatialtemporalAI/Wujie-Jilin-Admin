# 前后端边界与数据契约

## 责任边界

| 层面 | 后端负责 | 前端负责 |
|------|----------|----------|
| 数据验证 | 请求参数校验、业务规则验证 | 表单验证、输入格式化 |
| 业务逻辑 | 全部业务逻辑 | 仅页面交互逻辑 |
| 数据存储 | 数据库读写、缓存管理 | 本地存储（localStorage） |
| 响应结构 | 统一响应格式 | 响应解析与展示 |
| 状态管理 | 会话状态（Redis） | 页面状态（Pinia） |
| 路由 | API 路由注册 | 页面路由与守卫 |

共享行为通过明确的 API 契约实现，不依赖隐式耦合。

---

## 统一响应结构

### 普通响应

```json
{
  "code": 200,
  "msg": "成功",
  "data": { ... },
  "request_id": "uuid-string",
  "err_code": null
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | `number` | HTTP 状态码 |
| `msg` | `string` | 响应消息 |
| `data` | `T \| null` | 响应数据 |
| `request_id` | `string \| null` | 请求追踪 ID |
| `err_code` | `number \| null` | 业务错误码 |

### 分页响应

```json
{
  "code": 200,
  "msg": "成功",
  "data": {
    "records": [ ... ],
    "page": 1,
    "page_size": 10,
    "total": 100,
    "total_pages": 10
  },
  "request_id": "uuid-string",
  "err_code": null
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `records` | `T[]` | 当前页数据 |
| `page` | `number` | 当前页码（从 1 开始） |
| `page_size` | `number` | 每页条数（最大 200） |
| `total` | `number` | 总记录数 |
| `total_pages` | `number` | 总页数 |

---

## 字段命名

- API 请求和响应中字段名统一使用 `snake_case`
- 前端 TypeScript 类型定义与后端字段名保持一致
- 示例：`created_at`、`page_size`、`user_name`

---

## Status 字段桥接

这是前后端类型转换中最关键的约定。

### 转换流程

```
前端（展示/编辑）          后端（存储/逻辑）
"1" / "2"                True / False
    │                        │
    │ 前端发送请求            │ 数据库存储
    │ enableStatusToBoolean()│
    ├───────────────────────>│ bool
    │                        │
    │ 前端接收响应            │ BaseRespEntity 序列化
    │                        │ @field_serializer("status")
    │<───────────────────────┤ "1" / "2"
```

### 后端处理

- **存储类型**：`bool`（`True` = 启用，`False` = 禁用）
- **反序列化**（前端→后端）：`BoolField` 使用 `parse_bool` 处理
  - `"1"` / `"true"` / `"yes"` → `True`
  - `"2"` / `"false"` / `"no"` → `False`
  - 空值 → `None`
- **序列化**（后端→前端）：`BaseRespEntity` 的 `@field_serializer("status")`
  - `True` → `"1"`
  - `False` → `"2"`
- 定义位置：`app/models/common/base.py`

### 前端处理

- **TypeScript 类型**：`EnableStatus`（`"1" | "2"`）
- **发送请求时**：使用 `enableStatusToBoolean()` 将 `"1"`/`"2"` 转为 `boolean`
- **接收响应时**：后端已自动转换为 `"1"`/`"2"` 字符串
- **转换函数**：`src/utils/status.ts`

### `is_system` 字段

与 `status` 字段处理方式相同：`BaseRespEntity` 自动序列化 `is_system`（`True` → `"1"`，`False` → `"2"`）。

---

## 枚举字段与可选 ID 查询参数

查询参数（query）经 URL 编码后一律为字符串，空值可能以 `""`/`" "`/`"null"`/`"undefined"`/缺省等形式出现。后端在 `app/models/common/base.py` 提供两个统一收敛器，**所有可能为空的 query 字段都应使用**，避免裸 `int`/`str` 在空值时直接 422：

- `OptionalIntField`：空值 → `None`，`"123"` → `123`，非数字字符串 → 422
- `parse_optional_enum(allowed)`（工厂）：空值 → `None`，命中允许集 → 原值，非法值 → 422；用法 `Annotated[str | None, BeforeValidator(parse_optional_enum({...}))]`

> 仅用于 query 参数。请求体（body）走 JSON，前端给的是带类型值，保持 `Optional[int]`/`Optional[str]` 即可。

### 机器人状态枚举

机器人 `status` 是字符串枚举（**不走**上面的 `"1"/"2"` bool 桥接），前后端取值必须一致：

| 字段 | 取值 |
|------|------|
| `status` | `online` / `offline` / `inactive` |
| `speed_level` | `normal` / `slow` / `low` |

- 后端：`RobotStatusField` / `SpeedLevelField`（`modules/robot/schemas/robot.py`）
- 前端：`RobotStatusEnum`（`typings/api/robot.d.ts`），表单选项须与上表一致

### 其它已收敛枚举查询字段

| 模块 | 字段 | 取值 |
|------|------|------|
| 机器人事件日志 | `event_type` / `event_status` | `task,alarm` / `info,warning,critical` |
| 任务执行记录 | `status` / `source` | `pending,running,paused,cancelled,completed,failed` / `platform_schedule,voice_trigger,manual` |
| 调度任务日志 | `status` | `running,success,timeout,failed` |

---

## 时间字段桥接

### 后端 → 前端（响应序列化）

| 层面 | 类型 | 格式 |
|------|------|------|
| 后端数据库 | `datetime`（带时区） | UTC 存储 |
| 后端序列化 | `string` | `Asia/Shanghai`，`YYYY-MM-DD HH:mm:ss` |
| 前端接收 | `string` | `YYYY-MM-DD HH:mm:ss` |

序列化由 `BaseEntity` 的 `json_encoders` 自动处理（`app/models/common/base.py`）。

> **Excel 导出列**与**手动 `from_orm_with_format` 响应**（如 `ExportTaskResponse`/`ExportTemplateResponse`）都不走 Pydantic 的 `json_encoders`，时间须用 `database.utils.timezone.timezone.ftime`（同样转 `Asia/Shanghai` 再 strftime；naive 视为 UTC 兜底）。直接对 ORM datetime 调 `strftime` 会输出 UTC，比页面慢 8 小时。

### 前端 → 后端（请求参数）

| 层面 | 类型 | 格式示例 |
|------|------|----------|
| 前端选择 | `number`（时间戳） | NDatePicker 返回毫秒时间戳 |
| 前端发送 | `string` | `2026-05-21T16:39:23+08:00`（本地时间 + 时区偏移） |
| 后端解析 | `datetime` | `fromisoformat()` → `astimezone(UTC)` → UTC datetime |

**强制规则**：

1. **前端发送时间参数时，必须携带时区偏移**：使用 `dayjs(val).format()` 生成 `YYYY-MM-DDTHH:mm:ssZ` 格式（如 `+08:00`），禁止使用 `new Date(val).toISOString()` —— 后者会转为 UTC 导致与用户选择不一致
2. **后端解析时间参数时，必须区分有无时区**：
   ```python
   dt = datetime.fromisoformat(time_str)
   result = dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
   ```
   禁止直接使用 `.replace(tzinfo=timezone.utc)` —— 对带时区偏移的字符串会丢失转换

**原因**：用户在前端选择 `2026-05-21 16:39:23`，API 传参也应体现为 `16:39:23+08:00`，而非 UTC 时间 `08:39:23Z`。

---

## 变更规则

- 破坏性接口变更（字段名/类型/结构改变）必须记录变更说明
- Swagger 注释必须与真实实现保持一致
- 前端 API 封装统一放在 `src/service/api/`
- 跨栈变更必须同步更新 `aiDoc/frontend-backend/` 下的文档

## 任务管理 · 机器人绑定契约

任务新增/编辑接口（`POST /task/manage/add`、`PUT /task/manage/{task_id}`）中，`robot_ids` 字段按任务类型差异化约束：

- **巡逻任务（patrol）**：仅支持单选，数组长度必须为 1
- **播报任务（broadcast）**：支持多选，数组长度 ≥ 1

限制通过后端 Schema 的 `field_validator('robot_ids')` 实现（依据同请求体的 `task_type` 判断；`TaskUpdate` 中 `task_type` 缺省时不限制）。数据库 `task_robot` 关联表与 `Task.robots` relationship 本就是多对多，无需迁移。

- 后端：`TaskCreate.robot_ids` / `TaskUpdate.robot_ids` 仅保留 `min_length=1`，巡逻场景由 validator 校验 `len > 1` 抛错
- 前端：`task-operate-drawer.vue` 巡逻任务单选 `NSelect`（受场景地图约束），播报任务 `multiple` 多选（不受场景约束，且隐藏场景地图输入框与 NAlert 提示）
- 类型：`robot_ids` 仍为 `number[]`

## 机器人与场景绑定契约

## 场景地图新增/编辑字段契约

`POST /scene/map/add` 与 `PUT /scene/map/{map_id}` 共用同一套 Schema，前端两个入口（地图管理、地图编辑器）提交相同的核心字段集合。

### 前端提交字段（两个入口一致）

以下字段均为必填：

| 字段 | 前端类型 | 后端 Schema | 说明 |
|------|----------|-------------|------|
| `name` | `string` | `str` | 地图/场景名称 |
| `image_id` | `number` | `int` | 地图/场景图片文件ID |
| `width` | `number` | `int` | 图片宽度（像素），由上传图片自动回填 |
| `height` | `number` | `int` | 图片高度（像素），由上传图片自动回填 |
| `resolution` | `number` | `float` | 映射比例 |
| `start_point_x` | `number` | `float` | 扫图起始点X坐标 |
| `start_point_y` | `number` | `float` | 扫图起始点Y坐标 |

### 不在前端表单中填写的字段

| 字段 | 后端行为 |
|------|----------|
| `status` | 创建默认 `True`（启用），更新时不传则保持原值 |
| `group_id` / `group_name` | 不传则保持 `null`（未分组） |

### 后端 Schema 说明

- `SceneMapCreate` / `SceneMapUpdate` 中 `name`、`image_id`、`width`、`height`、`resolution`、`start_point_x`、`start_point_y` 必填。
- `group_id`、`group_name`、`status` 为可选。
- `nav_image_id` 仍可选，为空时后端保持原值或自动与 `image_id` 同步。

## 商户管理 + 商户开放 API 契约

### 数据模型

- `merchant`：`id, name, code(唯一), contact_name/phone/email, api_key(唯一,明文), api_secret_encrypted(Fernet加密), status, remark`
- `merchant_robot`：`merchant_id × robot_id` 多对多关联（商户绑定的可操作机器人）

### 后台管理接口（`/merchant`，JWT + 权限码 `merchant:list/add/edit/delete`）

- `GET /merchant/list`（分页）、`GET /merchant/{id}`（详情含 `robot_ids`）
- `POST /merchant/add` → 响应含 `api_secret` 明文（**仅本次返回**）
- `PUT /merchant/{id}`、`DELETE /merchant/{id}`、`PUT /merchant/{id}/toggle`
- `POST /merchant/{id}/reset-api-key` → 旧密钥立即失效，响应含新 `api_key`+`api_secret`（仅本次返回）
- `PUT /merchant/{id}/robots`（全量替换绑定机器人）
- 列表/详情响应**不含** `api_secret`；`status` 走 `BaseRespEntity` 的 `"1"/"2"` 桥接

### 商户开放 API（`/openapi/v1`，HMAC 签名鉴权，独立于 JWT）

请求头：`X-Api-Key` / `X-Timestamp`(秒) / `X-Nonce` / `X-Signature`
待签名串：`{METHOD}\n{path}\n{timestamp}\n{nonce}\n{sha256(raw_body 十六进制)}`
签名：`HMAC-SHA256(api_secret, 待签名串)` → 十六进制；时间戳容差 `MERCHANT__SIGN_TTL_SECONDS`；nonce 经 Redis `SET NX EX` 防重放。控制类接口请求体必须带 `robot_sn`，按 `Robot.serial_number` 解析并校验该机器人已绑定到当前商户；查询类接口 `robot_sn` 可选（`robots` 接口无参数）。

| 方法 | 路径 | 入参 | 复用实现 |
|------|------|------|----------|
| POST | `/openapi/v1/robots` | `{}` | `OpenApiService.list_robots`（返回 `id/name/sn`） |
| POST | `/openapi/v1/goto_point` | `robot_sn, point_id` | `NavigationClient.navigate_to_point`（gRPC `NavigationService.NavigateToPoint`，下发到 robot.agent；不落 Task） |
| POST | `/openapi/v1/navigate_route` | `robot_sn, point_ids[]` | `NavigationClient.navigate_route`（gRPC `NavigationService.NavigateRoute`，多点按序） |
| POST | `/openapi/v1/execute_task` | `robot_sn, task_id` | `start_execution`（仅下发 gRPC `run_now`，不写执行记录；响应 `data.action="started"`，不再返回 `record_id`/区分 resumed） |
| POST | `/openapi/v1/pause_task` | `robot_sn` | 查该 robot 活跃记录 → `pause_execution` |
| POST | `/openapi/v1/resume_task` | `robot_sn` | 查 paused 记录 → `resume_execution` |
| POST | `/openapi/v1/stop_task` | `robot_sn` | 查活跃记录 → `stop_execution` |
| POST | `/openapi/v1/speak` | `robot_sn, text, tts_params{voice,speed,volume}` | `VoiceConfigClient.test_tts`（复用 `VoiceConfigService.TestTTSConfig`，按入参即时播报） |

响应统一走 `ResponseModel`，`data` 为 `{ success, message, data? }`。鉴权/重放/超时失败 → 401（`TokenError`）；商户禁用/机器人未绑定 → 403（`ForbiddenError`）。

### 前端

- 页面 `frontend/src/views/open-merchant/merchant/`（已从 `views/merchant/` 迁入「开放商户」一级目录），样板参考 `manage/role`（NDrawer 表单 + NDataTable + TableHeaderOperation）
- API `frontend/src/service/api/merchant.ts`，类型 `frontend/src/typings/api/merchant.d.ts`
- 新增/重置成功用 `MerchantApiKeyModal` 展示 `api_key`+`api_secret`（secret 默认掩码、可切换显示、复制按钮），`NAlert` 提示"仅展示一次"

### 商户调用日志（`/merchant/call-log`，JWT + 权限码 `merchant:call-log:list/delete`）

由 `MerchantCallLogMiddleware` 自动捕获所有 `/openapi/v1/*` 调用（含鉴权失败）并落库到 `merchant_call_log` 表，**全程脱敏**：

- 数据模型 `merchant_call_log`：`merchant_id/name/code`(商户快照，api_key 无效时为空)、`api_key_masked`(脱敏)、`method/path/action`、`ip`、`request_params/response_result`(脱敏+截断 2000)、`response_code`、`success`、`elapsed_ms`、`error_msg`、`created_at`
- **脱敏边界**：`api_key` 经 `mask_api_key`(首6+`****`+尾4) 掩码；`X-Signature/X-Timestamp/X-Nonce` 绝不入库；请求/响应体经 `mask_secret_fields` 把 `secret/sign/password/token/api_key` 等键值替换 `***` 并截断；**保留** `robot_sn/point_ids/task_id/map_id/text` 等业务字段（排查必需、非凭证）。工具在 `core/security/mask.py`
- 后台接口（仿 operation-log）：`GET /merchant/call-log/list`(分页) / `/{id}`(详情含 params/result) / `/export`(同步 Excel) / `DELETE /batch/delete` / `/clear?days=` / `DELETE /{id}`；导出复用注册表 `merchant_call_log`
- 前端页面 `frontend/src/views/open-merchant/call-log/`，API `frontend/src/service/api/call-log.ts`，类型 `Api.Merchant.CallLog*`；导出按钮复用异步导出任务 `submitExport('merchant_call_log', ...)`

## 参数配置 · 人脸识别契约

「参数配置」页人脸识别（`/robot/config/face*`）**不走设备 gRPC**，增删改直接调用阿里云 facebody（`FaceService`），把每条本地记录注册为人脸库 `lvya` 的一个 entity。

- `RobotFaceRecognitionResponse` 字段：`id, person_name, photo_url, broadcast_text, entity_id?, face_id?, created_at, updated_at, grpc_status?`
- `entity_id`：阿里云实体 ID，取本地记录主键字符串 `str(id)`；`face_id`：阿里云人脸图片 ID（换图替换时用于定位旧图）
- `grpc_status` 对 face 恒为 `"synced"`（不再出现 `pending_retry`/`disabled`）；注册失败由后端抛错返回，前端按统一错误处理
- 一致性语义：create/update 阿里云注册失败 → 回滚本地（不留残桩）；delete 以本地为准，阿里云删除 best-effort
- 语音 / 速度 / 电量三类配置仍走 gRPC 推送 + 重试队列，不受影响

## 完成前检查清单

- [ ] 后端响应结构与前端类型定义匹配
- [ ] 字段名 `snake_case` 一致
- [ ] Status 字段桥接正确（`enableStatusToBoolean()` + `BaseRespEntity` 序列化）
- [ ] 时间字段格式正确（`YYYY-MM-DD HH:mm:ss`）
- [ ] Swagger 注释与实现一致
- [ ] 分页参数和返回格式符合 `ResponsePageModel` 规范
