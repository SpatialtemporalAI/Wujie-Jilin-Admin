#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import APIRouter, Depends, Request, Response, Body

# from fastapi_users import BaseUserManager, FastAPIUsers
from pydantic import BaseModel, Field
from redis import Redis
from app.models.sys.user import SysUser
from core.config import settings
from core.response import (
    ResponseModel,
    response_base,
)
from modules.admin.deps.auth.user_manager import (
    UserManager,
    get_user_manager,
    current_user,
)
from modules.admin.schemas.auth import (
    LoginPwdModel,
    LoginResponseData,
    UserInfoResponseData,
)
from core.security.rate_limit import limit_by_ip
from core.decorators.operation_log import log_operation

# 创建认证路由
router = APIRouter(prefix="/auth", tags=["admin接口/认证"])


# 登录路由
@router.post(
    "/login",
    response_model=ResponseModel[LoginResponseData],
    summary="后台用户登录接口",
    description="通过用户名和密码登录系统，获取访问令牌和刷新令牌",
)
@log_operation(module="auth", action="login", description="用户登录")
async def login(
    request: Request,
    login_pwd: LoginPwdModel = Body(..., description="登录请求参数"),
    user_manager: UserManager = Depends(get_user_manager),
):
    """
    用户登录接口
    接收用户名和密码，返回JWT令牌
    Args:
        request: 请求对象
        response: 响应对象
        user_manager: 用户管理器
    Returns:
        ResponseModel: 包含访问令牌和刷新令牌的响应
    Examples:
        {
            "username": "testuser",
            "password": "BlockChain"
        }
    """
    username = login_pwd.username
    await limit_by_ip(
        request=request,
        action="admin_login",
        limit=10,
        window_seconds=60,
        scope="admin",
        extra_suffix=username.lower(),
    )
    password = login_pwd.password
    tokens = await user_manager.login_by_password(
        username=username,
        password=password,
    )
    return response_base.success(
        data=tokens,
        msg="登录成功",
    )


@router.get(
    "/users/me",
    response_model=ResponseModel[UserInfoResponseData],
    summary="获取当前后台用户信息",
    description="获取当前登录后台用户的详细信息",
)
async def get_current_info(
    user: SysUser = Depends(current_user),
    user_manager: UserManager = Depends(get_user_manager),
):
    user_info = await user_manager.get_user_info(user.id)
    return response_base.success(
        data=user_info,
        msg="获取用户信息成功",
    )
