#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional
from pydantic import ConfigDict, Field
from datetime import datetime
from app.models.common.base import BaseRespEntity


# 系统用户响应数据模型
class SysUserResponseData(BaseRespEntity):
    """系统用户接口返回的数据模型"""

    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    nickname: str = Field(..., description="昵称")
    email: Optional[str] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, description="手机号")
    avatar: Optional[str] = Field(None, description="头像URL")
    is_superuser: bool = Field(..., description="是否为超级管理员")
    status: bool = Field(..., description="用户状态")
    last_login_at: Optional[datetime] = Field(None, description="最后登录时间")
    last_login_ip: Optional[str] = Field(None, description="最后登录IP")
