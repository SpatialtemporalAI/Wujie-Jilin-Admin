#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging

from fastapi import APIRouter, Depends, Request, Body
from pydantic import BaseModel, Field
from redis import Redis
from app.models.sys.user import SysUser
from core.config import settings
from core.response import (
    ResponseModel,
    response_base,
)
from core.exception.errors import CustomError
from core.utils.ip_utils import get_real_client_ip
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

logger = logging.getLogger(__name__)

# 创建认证路由
router = APIRouter(prefix="/auth", tags=["admin接口/认证"])


async def _write_login_log(username: str, ip: str | None, status: bool, detail: str, user_agent: str | None):
    """异步写入登录日志"""
    try:
        from database import get_session
        from modules.admin.services.sys.login_log_service import LoginLogService

        async for db in get_session():
            await LoginLogService.create_log(
                db=db,
                username=username,
                ip=ip,
                status=status,
                detail=detail,
                user_agent=user_agent,
            )
    except Exception as e:
        logger.error(f"写入登录日志失败: {e}")


# 登录路由
@router.post(
    "/login",
    response_model=ResponseModel[LoginResponseData],
    summary="后台用户登录接口",
    description="通过用户名和密码登录系统，获取访问令牌和刷新令牌",
)
async def login(
    request: Request,
    login_pwd: LoginPwdModel = Body(..., description="登录请求参数"),
    user_manager: UserManager = Depends(get_user_manager),
):
    """
    用户登录接口
    接收用户名和密码，返回JWT令牌
    """
    username = login_pwd.username
    ip = get_real_client_ip(request)
    user_agent = request.headers.get("user-agent", "")

    await limit_by_ip(
        request=request,
        action="admin_login",
        limit=10,
        window_seconds=60,
        scope="admin",
        extra_suffix=username.lower(),
    )

    try:
        password = login_pwd.password
        tokens = await user_manager.login_by_password(
            username=username,
            password=password,
            ip=ip,
            user_agent=user_agent,
        )
        asyncio.create_task(
            _write_login_log(username, ip, True, "登录成功", user_agent)
        )
        return response_base.success(
            data=tokens,
            msg="登录成功",
        )
    except CustomError as e:
        asyncio.create_task(
            _write_login_log(username, ip, False, e.msg, user_agent)
        )
        raise


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
