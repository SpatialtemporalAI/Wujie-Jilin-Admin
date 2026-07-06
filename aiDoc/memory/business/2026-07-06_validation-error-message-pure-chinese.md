# 校验错误提示词去中英文混合（用字段中文描述指代）

## 需求描述

接口类型校验抛出的错误提示词禁止中英文混合（如 `page_size必须为整数`、`username参数不合法`），尽量使用纯中文。要求：

- 有字段中文描述（`Field(description=...)`）时，提示以描述指代字段，如「用户名必须为整数」「年龄必须大于 0」
- 无描述时回退为「该参数 + 中文片段」，如「该参数必须为整数」，不再出现英文字段名
- 数值/长度边界优先用 ctx 生成精确提示（如「必须大于 0」「长度不能超过 5」）
- 补全 Pydantic v2 错误类型中文映射，减少「不合法」兜底

延续 `2026-07-06_global-required-validation.md` 建立的 `PYDANTIC_ERROR_ZH` + `_translate_validation_error` 机制（旧实现用英文字段名拼接到中文前，产生 `page_size必须为整数` 这类混合），本次消除字段名混合。

## 状态

已完成

## 涉及范围

### 后端

- `core/exception/errors_handler.py`：
  - 新增 `_resolve_field_label(request, loc)`：从 `request.scope["route"].dependant` 反射字段中文描述——body 沿 `loc` 递归钻取请求体 model 的 `model_fields` 取 `description`（支持嵌套 model、穿透 list/Union/Optional）；query/path/header/cookie 按参数名匹配 `FieldInfo.description`；全程 try/except，反射失败返回 None
  - 新增辅助函数 `_model_from_annotation`（穿透 list/Union/Optional 找 BaseModel）、`_description_in_model`（递归取最深层 description，回退 title）、`_ctx_fragment`（用 ctx 生成精确片段）
  - `_translate_validation_error` 签名改为 `(request, error)`，优先级：自定义 validator 中文 `ValueError`/`AssertionError` 原样透传 → `{description}{片段}` → `该参数{片段}` → `该参数不合法`
  - `PYDANTIC_ERROR_ZH` 由约 30 项扩充到约 90 项，覆盖 Pydantic v2 常见类型（int/string/float/bool/date/time/uuid/url/enum/model/extra/json/union/recursion 等）
  - `validation_exception_handler` 与 `pydantic_validation_error_handler` 调用时传入 `request`（后者传 None，仅用纯中文翻译）

### 前端

无（统一响应结构不变，仅 `msg` 文案不再混入英文字段名）。

## 约束与备注

- 描述反射依赖 schema 字段填写 `description`（项目覆盖率约 99.7%：1035/1038 个 `Field()` 有 description），未填写的字段回退「该参数」
- 反射只读 `description`/`title`，不读英文字段名；`uuid_type`/`json_type` 等保留国际通用术语（UUID/JSON），不算中英混合
- `_resolve_field_label` 全程吞异常，确保校验错误处理本身不会因反射失败再次抛错
- 兜底「不合法」：映射表未覆盖的 Pydantic 类型走 `{label}不合法` / `该参数不合法`
- 端到端验证覆盖 7 类场景：body 类型错/必填缺失/长度超限/数值边界/无描述回退/嵌套 model/query 参数，msg 均为纯中文

## 相关文件

- `backend/core/exception/errors_handler.py`
- 前置需求：`aiDoc/memory/business/2026-07-06_global-required-validation.md`
- 规则沉淀：`aiDoc/modules/backend-layer-rules.md`（「校验失败信息中文化」小节）

## 记录日期

2026-07-06
