# 分页参数脏值防御性收敛 + OptionalIntField 错误中文化

## 需求描述

任务管理列表报 `Input should be a valid integer, unable to parse string as an integer`（Pydantic `int_parsing`）。排查结论与修复方向：

- `page` / `page_size` 收到无法解析为整数的字符串（空串 / `"null"` / `"undefined"` / `"NaN"` / 非数字）时，不再 422 报错，而是**收敛到默认值**（page=1，page_size 上限 2000）。
- `OptionalIntField`（robot_id / map_id 等查询字段）收到非数字字符串时，错误提示由英文 `invalid literal for int() with base 10: 'xxx'` 统一为纯中文**「必须为整数」**。

## 状态

已完成

## 涉及范围

### 后端

- `app/models/common/base.py`
  - 新增 `parse_positive_int(default, *, max_value=None)`：生成 `BeforeValidator`，空值/非法值收敛为 default，`<1` 取 1，`>max_value` 截断。
  - `parse_optional_int` 内部 `int()` 失败时改为抛 `ValueError("必须为整数")`，借 `errors_handler` 的 `value_error` 分支透传为纯中文（之前透传的是 Python 默认英文 `invalid literal...`）。
- `app/models/common/page.py`
  - `PageRequest.page` / `page_size` 改用 `Annotated[int, BeforeValidator(parse_positive_int(...))]`（`PageField` / `PageSizeField`），删除原 `field_validator`（边界已由 `parse_positive_int` 覆盖）。
  - `get_page_params` 的 `page` / `page_size` 改为 `Optional[str] = Query(...)`，脏值交由 `PageRequest` 字段的 `BeforeValidator` 收敛。

### 前端

无（前端 `searchParams.page/page_size` 本身是 number，脏值主要来自 URL 残留 / `NaN`；后端收敛后无需配合改动）。

## 约束与备注

- **FastAPI 关键限制**：`Depends` 函数参数上的标量 `int`（`page: int = Query(...)`）会先于 `BeforeValidator` 做类型解析，因此 `Annotated[int, BeforeValidator]` 在 `get_page_params` 函数参数位置**不生效**（脏值仍 `int_parsing`）。`BeforeValidator` 只在 **`BaseModel` 字段** 或 **`Annotated[WholeModel, Query()]`** 上生效。故本方案让 `get_page_params` 以 `Optional[str]` 接收、由 `PageRequest` 模型字段收敛。
- **Swagger 文档 trade-off**：`page` / `page_size` 的文档类型由 `integer` 变为 `string|null`（FastAPI 上述限制所致，`WithJsonSchema` / `openapi_extra` 均无法在 Query 上覆盖类型）。功能无影响（query 本身按字符串传输），description 已注明「非正整数回退到默认值」。若后续要恢复 `integer` 文档，需把所有列表端点（25 文件 52 处 `Depends(get_page_params)`）改为 `Annotated[PageRequest, Query()]`——属大改，未采用。
- `int_parsing`（page/page_size）本就被 `PYDANTIC_ERROR_ZH` 翻译为「必须为整数」；若线上仍看到英文原文，是**后端进程未重启**（翻译逻辑在 `df8a3bb` 提交），重启即可。
- 行为变化：`PageRequest(page=0)` 等越界值由「抛错」改为「收敛」（`page=0 → 1`、`page_size=99999 → 2000`），与「防御性收敛」目标一致。

## 相关文件

- `backend/app/models/common/base.py`
- `backend/app/models/common/page.py`
- 前置：`aiDoc/memory/business/2026-07-06_validation-error-message-pure-chinese.md`（`PYDANTIC_ERROR_ZH` + `_translate_validation_error`）

## 记录日期

2026-07-07
