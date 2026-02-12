from pydantic import (
    BaseModel,
    ConfigDict,
    model_validator,
    field_validator,
    field_serializer,
)
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Type, TypeVar, Optional

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


class BaseRespEntity(BaseEntity):
    """基础响应实体模型"""

    # 处理输入转换：接收1→True，接收2→False（也可添加非法值校验）
    @field_validator(
        "status", mode="before", check_fields=False
    )  # mode="before" 表示先处理原始输入再验证类型
    def validate_status_input(cls, value):
        # 如果输入是1，转为True；输入是2，转为False
        if value == "1":
            return True
        elif value == "2":
            return False
        # 可选：校验非法输入（比如传3/字符串等），抛出明确异常
        elif value not in (True, False):
            raise ValueError("status参数只能是1（代表true）或2（代表false）")
        # 如果输入本身是bool（比如直接传true/false），直接返回
        return value

    # 处理输出转换：True→1，False→2
    @field_serializer("status", check_fields=False)
    def serialize_status_output(self, value: bool):
        return "1" if value else "2"
