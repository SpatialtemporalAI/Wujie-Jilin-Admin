#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Annotated, ClassVar

from pydantic import Field, BeforeValidator

from app.models.common.base import BaseEntity, OptionalIntField, parse_optional_enum

TaskLogStatusField = Annotated[
    str | None, BeforeValidator(parse_optional_enum({"running", "success", "timeout", "failed"}))
]


class TaskLogQueryParams(BaseEntity):
    """任务执行日志查询参数"""

    task_id: OptionalIntField = Field(None, description="任务ID")
    task_name: str | None = Field(None, description="任务名称")
    task_key: str | None = Field(None, description="任务标识")
    status: TaskLogStatusField = Field(None, description="执行状态")
    start_time: str | None = Field(None, description="开始时间")
    end_time: str | None = Field(None, description="结束时间")


class TaskLogResponse(BaseEntity):
    """任务执行日志响应"""

    # status 为 running/success/... 字符串状态，不能走 BaseRespEntity 序列化，故仅跳过非空校验
    _skip_required_check: ClassVar[bool] = True

    id: int
    task_id: int
    task_name: str
    task_key: str
    status: str
    start_time: datetime | None
    end_time: datetime | None
    duration_ms: float | None
    result: str | None
    error_message: str | None
    retry_count: int
    triggered_by: str
    created_at: datetime | None


class TaskLogDetailResponse(BaseEntity):
    """任务执行日志详情（含完整错误信息和结果）"""

    # 同 TaskLogResponse：status 为字符串状态，仅跳过非空校验
    _skip_required_check: ClassVar[bool] = True

    id: int
    task_id: int
    task_name: str
    task_key: str
    status: str
    start_time: datetime | None
    end_time: datetime | None
    duration_ms: float | None
    result: str | None
    error_message: str | None
    retry_count: int
    triggered_by: str
    created_at: datetime | None
