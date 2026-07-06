# 全局必填字段非空校验 + 校验信息中文化

## 需求描述

统一所有接口的参数校验：必填字段必须做非空校验（字符串过滤纯空格、集合拒绝空集合），且校验失败信息统一为中文返回。

## 状态

已完成

## 涉及范围

### 后端

- `app/models/common/base.py`：`BaseEntity` 新增全局 `model_validator(mode="after")`，对必填字段统一校验——`str` 去 strip 非空并回写（自动 trim）、`list/tuple/dict/set` 拒绝空集合、错误消息 `f"{description}不能为空"`；`BaseRespEntity` 设 `_skip_required_check: ClassVar[bool] = True` 跳过
- `core/exception/errors_handler.py`：`validation_exception_handler` 按 Pydantic 错误 `type` 映射中文（`PYDANTIC_ERROR_ZH` + `_translate_validation_error`），自定义 validator 抛出的中文 `ValueError` 原样透传
- 约 18 个原生 `BaseModel` 纯请求体迁移到 `BaseReqEntity`（登录/验证码/人脸库/导出模板/权限/编辑器 Item 等）
- 约 16 个直接继承 `BaseEntity` 的响应类：
  - 无 `status`/`is_system` 字段的 → 改 `BaseRespEntity`（如 OperationLog/OnlineUser/Monitor/IpBlacklist/RobotEventLog/OpenApiResult/McpToolInfo/CronPreviewResponse）
  - 有 `status`/`is_system` 且语义非启用/禁用的（LoginLog/TaskLog/McpServerStatus/TaskResponseData/TaskExecutionRecordResponseData/RegistryTaskResponse）→ 保持 `BaseEntity`，类内加 `_skip_required_check: ClassVar[bool] = True`
- 约 40 个直接继承 `BaseEntity` 的请求类（Create/Update/Batch/Request 等）零改动自动覆盖

### 前端

无（统一响应结构不变，仅 `msg` 文案由英文/默认改为中文）。

## 约束与备注

- 响应模型不应被非空校验（避免 ORM 数据空值导致序列化 500），统一通过 `BaseRespEntity` 或 `_skip_required_check` ClassVar 跳过
- 有 `status`/`is_system` 字段但语义非启用/禁用（日志 success bool、执行状态字符串等）的响应类**不能**改 `BaseRespEntity`（其字段序列化器会把 bool 转 "1"/"2"、把非空字符串状态转 "1"），只能用 ClassVar 跳过校验、保持原序列化
- 自动 trim 仅作用于必填 `str`（去首尾空格并回写对象）
- `UserInfoUpdateModel.id` 顺带修正一处 `(Field(...),)` 元组笔误为正常 `Field(...)`

## 相关文件

- `backend/app/models/common/base.py`
- `backend/core/exception/errors_handler.py`
- `backend/modules/**/schemas/*.py`（约 21 个文件，详见 git diff）
- `aiDoc/modules/backend-layer-rules.md`（Schema 层新增"必填字段非空校验（全局）"小节）

## 记录日期

2026-07-06
