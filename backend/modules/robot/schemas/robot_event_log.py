#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Annotated

from pydantic import Field, BeforeValidator

from app.models.common.base import BaseEntity, BaseRespEntity, OptionalIntField, parse_optional_enum

EventTypeField = Annotated[str | None, BeforeValidator(parse_optional_enum({"task", "alarm"}))]
EventStatusField = Annotated[str | None, BeforeValidator(parse_optional_enum({"normal", "abnormal"}))]


class RobotEventLogQueryParams(BaseEntity):
    """机器人事件日志查询参数"""

    robot_id: OptionalIntField = Field(None, description="机器人ID")
    event_type: EventTypeField = Field(None, description="事件类型：task/alarm")
    event_status: EventStatusField = Field(None, description="事件状态：normal/abnormal")
    start_time: str | None = Field(None, description="开始时间")
    end_time: str | None = Field(None, description="结束时间")


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
