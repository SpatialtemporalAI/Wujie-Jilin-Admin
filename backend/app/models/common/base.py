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

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.astimezone(ZoneInfo("Asia/Shanghai")).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        },
    )


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
