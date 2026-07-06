#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional, List
from pydantic import BaseModel, Field

from app.models.common.base import BaseReqEntity


class LoginPwdModel(BaseReqEntity):
    """登录密码模型"""

    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    captcha_token: str | None = Field(None, description="滑块验证码令牌")


class TenantBrief(BaseModel):
    """租户简要信息（登录响应中使用）"""

    id: int
    name: str
    code: str


class LoginResponseData(BaseModel):
    """登录接口返回的数据模型"""

    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(..., description="令牌类型")
    expires_in: int = Field(..., description="令牌过期时间（秒）")
    refresh_token: str = Field(..., description="刷新令牌")
    tenant_id: Optional[int] = Field(None, description="当前租户ID")
    tenants: Optional[List[TenantBrief]] = Field(None, description="用户可用租户列表")


# 用户信息响应数据模型
class UserInfoResponseData(BaseModel):
    """用户信息接口返回的数据模型"""

    id: int
    username: str
    nickname: str
    email: str | None
    phone: str | None
    avatar: str | None
    is_superuser: bool
    status: bool
    last_login_at: str | None
    last_login_ip: str | None
    roles: list[str] = []
