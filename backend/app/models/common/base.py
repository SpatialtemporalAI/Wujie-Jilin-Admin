from pydantic import BaseModel, ConfigDict
from datetime import datetime
from zoneinfo import ZoneInfo


class BaseEntity(BaseModel):
    """基础实体模型"""

    model_config = ConfigDict(from_attributes=True)


class BaseRespEntity(BaseEntity):
    """基础响应实体模型"""

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.astimezone(ZoneInfo("Asia/Shanghai")).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        },
    )
