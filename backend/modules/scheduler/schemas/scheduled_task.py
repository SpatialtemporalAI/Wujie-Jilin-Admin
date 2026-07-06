#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import ClassVar

from pydantic import Field

from app.models.common.base import BaseEntity, BaseRespEntity, BoolField


class ScheduledTaskCreate(BaseEntity):
    """创建定时任务"""

    name: str = Field(..., description="任务名称")
    task_key: str = Field(..., description="任务唯一标识")
    description: str | None = Field(None, description="任务描述")
    cron_expression: str = Field(..., description="Cron 表达式")
    trigger_type: str = Field("cron", description="触发类型: cron/interval/date")
    trigger_params: str | None = Field(None, description="触发参数 JSON")
    timeout: int = Field(300, description="超时时间(秒)")
    max_retries: int = Field(0, description="最大重试次数")
    concurrent_policy: str = Field("skip", description="并发策略: skip/replace/run")


class ScheduledTaskUpdate(BaseEntity):
    """更新定时任务"""

    name: str | None = Field(None, description="任务名称")
    description: str | None = Field(None, description="任务描述")
    cron_expression: str | None = Field(None, description="Cron 表达式")
    trigger_type: str | None = Field(None, description="触发类型")
    trigger_params: str | None = Field(None, description="触发参数 JSON")
    timeout: int | None = Field(None, description="超时时间(秒)")
    max_retries: int | None = Field(None, description="最大重试次数")
    concurrent_policy: str | None = Field(None, description="并发策略")


class ScheduledTaskQueryParams(BaseEntity):
    """定时任务查询参数"""

    name: str | None = Field(None, description="任务名称")
    task_key: str | None = Field(None, description="任务标识")
    status: BoolField = Field(None, description="状态")
    trigger_type: str | None = Field(None, description="触发类型")


class ScheduledTaskResponse(BaseRespEntity):
    """定时任务响应"""

    id: int
    name: str
    task_key: str
    description: str | None
    cron_expression: str
    trigger_type: str
    trigger_params: str | None
    status: bool
    module: str | None
    function_path: str | None
    is_system: bool
    last_run_at: datetime | None
    next_run_at: datetime | None
    last_status: str | None
    timeout: int
    max_retries: int
    concurrent_policy: str
    created_at: datetime | None
    updated_at: datetime | None


class CronPreviewRequest(BaseEntity):
    """Cron 表达式预览请求"""

    cron_expression: str = Field(..., description="Cron 表达式")


class CronPreviewResponse(BaseRespEntity):
    """Cron 表达式预览响应"""

    next_run_times: list[str] = Field(default_factory=list, description="接下来 N 次执行时间")


class RegistryTaskResponse(BaseEntity):
    """装饰器注册的任务信息"""

    # is_system 为 bool 但语义非启用/禁用，不能走 BaseRespEntity 序列化，故仅跳过非空校验
    _skip_required_check: ClassVar[bool] = True

    task_key: str
    name: str
    description: str
    cron_expression: str
    trigger_type: str
    trigger_params: dict | None
    module: str | None
    function_path: str | None
    is_system: bool
    timeout: int
    max_retries: int
    concurrent_policy: str
