#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pydantic import BaseModel, Field


class LoginPwdModel(BaseModel):
    """登录密码模型"""

    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class LoginResponseData(BaseModel):
    """登录接口返回的数据模型"""

    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(..., description="令牌类型")
    expires_in: int = Field(..., description="令牌过期时间（秒）")
    refresh_token: str = Field(..., description="刷新令牌")


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
