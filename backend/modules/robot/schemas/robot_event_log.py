#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Optional

from pydantic import Field

from app.models.common.base import BaseEntity, BaseRespEntity


class RobotEventLogQueryParams(BaseEntity):
    """机器人事件日志查询参数

    注意：查询参数统一使用基础 Optional[str]（FastAPI 对 Annotated query 模型字段在部分
    版本存在兼容性问题，可能漏收集请求参数导致模型构造缺键报 missing）。
    """

    robot_id: Optional[str] = Field(None, description="机器人ID")
    event_type: Optional[str] = Field(None, description="事件类型：task/alarm")
    event_status: Optional[str] = Field(None, description="事件状态：info/warning/critical")
    start_time: Optional[str] = Field(None, description="开始时间")
    end_time: Optional[str] = Field(None, description="结束时间")


class RobotEventLogResponse(BaseRespEntity):
    """机器人事件日志列表响应"""

    id: int
    robot_id: int
    robot_name: str | None = Field(None, description="机器人名称")
    event_type: str
    event_status: str
    event_content: str | None
    created_at: datetime | None
    updated_at: datetime | None


class RobotEventLogDetailResponse(RobotEventLogResponse):
    """机器人事件日志详情响应"""

    pass
