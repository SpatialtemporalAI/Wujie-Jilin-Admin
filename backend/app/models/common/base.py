from pydantic import (
    BaseModel,
    ConfigDict,
    model_validator,
    field_validator,
    field_serializer,
    BeforeValidator,
)
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import ClassVar, Type, TypeVar, Optional, Annotated

T = TypeVar("T")


class BaseEntity(BaseModel):
    """基础实体模型"""

    # 响应模型（BaseRespEntity）置 True 以跳过必填非空校验，避免响应序列化误报错
    _skip_required_check: ClassVar[bool] = False

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.astimezone(ZoneInfo("Asia/Shanghai")).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        },
    )

    @model_validator(mode="after")
    def _check_required_non_empty(self):
        """
        统一必填字段非空校验：
        - 必填 str：去除首尾空格，纯空格视为空；通过后回写 trim 后的值
        - 必填 list/tuple/dict/set：拒绝空集合
        - 其他类型（int/float/bool 等）：Pydantic 已保证非 None，跳过

        响应模型通过 ``_skip_required_check=True`` 跳过本校验。
        """
        if type(self)._skip_required_check:
            return self
        for name, field_info in type(self).model_fields.items():
            if not field_info.is_required():
                continue
            value = getattr(self, name)
            label = field_info.description or name
            if isinstance(value, str):
                stripped = value.strip()
                if not stripped:
                    raise ValueError(f"{label}不能为空")
                if stripped != value:
                    setattr(self, name, stripped)
            elif isinstance(value, (list, tuple, dict, set)) and len(value) == 0:
                raise ValueError(f"{label}不能为空")
        return self


class BaseReqEntity(BaseEntity):
    """基础请求实体模型"""

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.astimezone(ZoneInfo("Asia/Shanghai")).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        },
    )


class BaseRespEntity(BaseEntity):
    """基础响应实体模型"""

    # 响应模型跳过必填非空校验，避免 ORM 数据空值导致序列化失败
    _skip_required_check: ClassVar[bool] = True

    # 处理输出转换：True→"1"，False→"2"
    @field_serializer("status", check_fields=False)
    def serialize_status_output(self, value: bool):
        return "1" if value else "2"

    @field_serializer("is_system", check_fields=False)
    def serialize_is_system_output(self, value: bool):
        return "1" if value else "2"

    JS_MAX_SAFE_INTEGER: ClassVar[int] = 9007199254740992  # 2^53

    @field_serializer("id", check_fields=False)
    def serialize_id_output(self, value: int):
        if isinstance(value, int) and value >= self.JS_MAX_SAFE_INTEGER:
            raise ValueError(f"ID {value} 超出JavaScript安全整数范围，请运行迁移修复")
        return value


EMPTY_VALUES = {"", " ", "null", "undefined", None}


def parse_bool(value):
    # 统一转字符串处理
    if isinstance(value, str):
        value = value.strip().lower()

    if value in EMPTY_VALUES:
        return None

    true_set = {"1", "true", "yes", "y"}
    false_set = {"2", "false", "no", "n"}

    if value in true_set:
        return True
    if value in false_set:
        return False

    if isinstance(value, bool):
        return value

    raise ValueError(f"非法值: {value}，只能是 1/true 或 2/false 或为空")


BoolField = Annotated[Optional[bool], BeforeValidator(parse_bool)]


def parse_optional_int(value):
    if isinstance(value, str):
        value = value.strip()
    if value in EMPTY_VALUES:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        # 抛中文消息：errors_handler 的 value_error 分支会原样透传为纯中文提示，
        # 避免 robot_id/map_id 等字段收到非数字字符串时返回英文 "invalid literal for int()..."
        raise ValueError("必须为整数") from None


OptionalIntField = Annotated[Optional[int], BeforeValidator(parse_optional_int)]


def parse_positive_int(default: int, *, max_value: Optional[int] = None):
    """生成分页整数的 BeforeValidator：空值/非法值收敛为 default，<1 取 1，超过 max_value 截断。

    用于 PageRequest 的 page/page_size 字段（BaseModel 字段验证），可收敛前端传入的脏值
    （空字符串 / "null" / "undefined" / "NaN" / 非数字字符串），避免触发 Pydantic int_parsing 错误。
    """
    def parser(value):
        if isinstance(value, str):
            value = value.strip()
        if value in EMPTY_VALUES:
            return default
        try:
            v = int(value)
        except (ValueError, TypeError):
            return default
        if v < 1:
            return 1
        if max_value is not None and v > max_value:
            return max_value
        return v
    return parser


def parse_optional_enum(allowed):
    """生成可选枚举校验器：空值收敛为 None，合法值原样返回，非法值抛错。

    与 OptionalIntField 同款 BeforeValidator + EMPTY_VALUES 模式，
    供查询参数中"文档已写明取值"的字段收敛空值并强约束枚举。
    """
    allowed_set = {str(v) for v in allowed}

    def parser(value):
        if isinstance(value, str):
            value = value.strip()
        if value in EMPTY_VALUES:
            return None
        if value in allowed_set:
            return value
        raise ValueError(f"非法值: {value}，允许: {sorted(allowed_set)}")

    return parser
