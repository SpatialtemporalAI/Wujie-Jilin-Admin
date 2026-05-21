#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pydantic import BaseModel, Field


class LoginLogQueryParams(BaseModel):
    """登录日志查询参数"""

    username: str | None = Field(None, description="登录用户名")
    ip: str | None = Field(None, description="客户端IP")
    status: bool | None = Field(None, description="登录状态")
    start_time: str | None = Field(None, description="开始时间")
    end_time: str | None = Field(None, description="结束时间")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(10, ge=1, le=100, description="每页条数")


class LoginLogResponse(BaseModel):
    """登录日志列表响应"""

    id: int
    username: str
    ip: str | None
    status: bool
    detail: str | None
    user_agent: str | None
    login_time: str | None
    created_at: str | None


class LoginLogDetailResponse(LoginLogResponse):
    """登录日志详情响应"""

    pass
