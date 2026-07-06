# 商户开放 API 接口补类型校验

## 需求描述

商户开放 API（`/openapi/v1`）接口此前仅靠全局 `BaseEntity._check_required_non_empty` 做必填非空校验，缺少**类型 / 取值范围 / 枚举**校验：

- `tasks.task_type` / `tasks.status` 文档已写明取值，但代码完全不校验，传 `xxx` 静默返回空列表。
- `speak.tts_params.speed`(0.5–2.0) / `volume`(0–100) 文档承诺范围，代码不校验，越界值直接透传 gRPC。
- `tasks.map_id` 为可选 int，未用项目统一的 `OptionalIntField` 收敛空值。

## 状态

已完成（后端 schema + 接入文档同步；无前端改动）

## 涉及范围

### 后端

- `backend/modules/merchant/schemas/openapi.py`
  - 新增 `TaskTypeField = Annotated[str|None, BeforeValidator(parse_optional_enum({"patrol","broadcast"}))]`
  - 新增 `TaskStatusField = Annotated[str|None, BeforeValidator(parse_optional_enum({"idle","running","paused"}))]`
  - `TasksRequest.task_type` → `TaskTypeField`、`status` → `TaskStatusField`、`map_id` → `OptionalIntField`
  - `TtsParams.speed: Optional[float] = Field(None, ge=0.5, le=2.0)`、`volume: Optional[int] = Field(None, ge=0, le=100)`
  - import 由 `BaseEntity, BaseRespEntity` 扩为含 `OptionalIntField, parse_optional_enum`，并补 `Annotated`、`BeforeValidator`
- 枚举取值与 `Task` 模型对齐：`task_type`=`patrol`/`broadcast`（`database/models/business/task.py`）、`status`=`idle`/`running`/`paused`

### 文档

- `商户开放API接入文档.md`：错误码表新增 **422**（参数校验失败）；4.7 tts_params 补范围越界→422；4.10 任务列表补枚举非法→422；变更记录追加 2026-07-06 条目

## 关键决策（已与用户确认的范围）

**加**：文档已写明约束、且后端有权威取值集合的字段——`task_type` / `status` 枚举、`speed` / `volume` 范围、`map_id` 可选 int 收敛。

**不加**（避免过度设计）：
- `tts_params.voice` 枚举——后端无权威音色集合（gRPC 透传，`_DEFAULT_TTS_VOICE="female"` 仅为兜底），强枚举易误伤。
- `point_id` / `task_id` / `map_id`(points) 的 `ge=1`——项目惯例不加，service 层有 `NotFoundError` 兜底。
- 可选 str（如 `robot_sn` 查询参数）的 trim——超出"类型校验"范畴，全局 validator 仅作用于必填字段。

## 约束与备注

- 校验失败经 `validation_exception_handler` 返回 **HTTP 422** + 中文 msg（`PYDANTIC_ERROR_ZH` 覆盖 `less_than_equal` / `greater_than_equal` / `value_error`，`parse_optional_enum` 抛的中文 ValueError 原样透传）。
- 参数校验在 FastAPI body 解析阶段触发，**早于** `get_current_merchant` HMAC 鉴权；同时缺签名 + 参数非法时先返回 422。
- `parse_optional_enum` 把 `"null"` / `""` / `"   "` 等空值收敛为 None（与 `OptionalIntField` / `parse_bool` 同款 EMPTY_VALUES 模式），即"传空 = 不过滤"。
- 已用项目 `.venv` 跑冒烟测试：枚举拦截、范围拦截、OptionalIntField 收敛、必填非空回归均符合预期。

## 相关文件

- `backend/modules/merchant/schemas/openapi.py`
- `商户开放API接入文档.md`

## 关联记忆

- 复用同一校验工厂与模式：[[2026-07-02_param-type-validation-tighten]]（`parse_optional_enum` 引入）
- 全局必填非空校验底座：[[2026-07-06_global-required-validation]]
- 开放 API 整体能力：[[2026-06-29_merchant-openapi]]

## 记录日期

2026-07-06
