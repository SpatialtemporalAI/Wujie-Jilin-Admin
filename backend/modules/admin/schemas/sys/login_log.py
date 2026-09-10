#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import ClassVar

from pydantic import Field

from app.models.common.base import BaseEntity


class LoginLogQueryParams(BaseEntity):
    """登录日志查询参数

    注意：查询参数统一使用基础 Optional[str]（FastAPI 对 Annotated query 模型字段在部分
    版本存在兼容性问题，可能漏收集请求参数导致模型构造缺键报 missing）；空值/脏值收敛由 service 层完成。
    """

    username: str | None = Field(None, description="登录用户名")
    ip: str | None = Field(None, description="客户端IP")
    status: str | None = Field(None, description="登录状态")
    start_time: str | None = Field(None, description="开始时间")
    end_time: str | None = Field(None, description="结束时间")


class LoginLogResponse(BaseEntity):
    """登录日志列表响应"""

    # status 为登录成功/失败 bool，不能走 BaseRespEntity 的 "1"/"2" 序列化，故仅跳过非空校验
    _skip_required_check: ClassVar[bool] = True

    id: int
    username: str
    ip: str | None
    status: bool
    detail: str | None
    user_agent: str | None
    login_time: datetime | None
    created_at: datetime | None


class LoginLogDetailResponse(LoginLogResponse):
    """登录日志详情响应"""

    pass
