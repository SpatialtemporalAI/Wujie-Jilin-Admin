#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
用户管理相关接口
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from database.db_manager import get_session
from core.response.response_schema import ResponseModel

from app.models.sys.user import SysUser
from modules.admin.services.sys import UserService
from modules.admin.models.auth import SysUserResponseData

# 创建用户管理路由
user_router = APIRouter(prefix="/user", tags=["用户管理"])


@user_router.get("/list", response_model=ResponseModel[List[SysUserResponseData]])
async def get_user_list(
    status: Optional[bool] = Query(None, description="状态"),
    db: AsyncSession = Depends(get_session),
):
    """
    获取用户列表
    """
    users = await UserService.get_user_list(db, status)

    # 转换为响应模型
    def format_datetime(dt):
        if dt:
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        return None

    user_responses = []
    for user in users:
        user_response = SysUserResponseData(
            id=user.id,
            username=user.username,
            nickname=user.nickname,
            email=user.email,
            phone=user.phone,
            avatar=user.avatar,
            is_superuser=user.is_superuser,
            status=user.status,
            last_login_at=format_datetime(user.last_login_at),
            last_login_ip=user.last_login_ip,
        )
        user_responses.append(user_response)
    return ResponseModel(data=user_responses)


@user_router.get("/{user_id}", response_model=ResponseModel[SysUserResponseData])
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_session),
):
    """
    获取单个用户
    """
    user = await UserService.get_user(db, user_id)

    # 转换为响应模型
    def format_datetime(dt):
        if dt:
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        return None

    user_response = SysUserResponseData(
        id=user.id,
        username=user.username,
        nickname=user.nickname,
        email=user.email,
        phone=user.phone,
        avatar=user.avatar,
        is_superuser=user.is_superuser,
        status=user.status,
        last_login_at=format_datetime(user.last_login_at),
        last_login_ip=user.last_login_ip,
    )
    return ResponseModel(data=user_response)


@user_router.post("", response_model=ResponseModel[SysUserResponseData])
async def create_user(
    user: SysUser,
    db: AsyncSession = Depends(get_session),
):
    """
    创建用户
    """
    user = await UserService.create_user(db, user)

    # 转换为响应模型
    def format_datetime(dt):
        if dt:
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        return None

    user_response = SysUserResponseData(
        id=user.id,
        username=user.username,
        nickname=user.nickname,
        email=user.email,
        phone=user.phone,
        avatar=user.avatar,
        is_superuser=user.is_superuser,
        status=user.status,
        last_login_at=format_datetime(user.last_login_at),
        last_login_ip=user.last_login_ip,
    )
    return ResponseModel(data=user_response)


@user_router.put("/{user_id}", response_model=ResponseModel[SysUserResponseData])
async def update_user(
    user_id: int, user: SysUser, db: AsyncSession = Depends(get_session)
):
    """
    更新用户
    """
    user = await UserService.update_user(db, user_id, user)

    # 转换为响应模型
    def format_datetime(dt):
        if dt:
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        return None

    user_response = SysUserResponseData(
        id=user.id,
        username=user.username,
        nickname=user.nickname,
        email=user.email,
        phone=user.phone,
        avatar=user.avatar,
        is_superuser=user.is_superuser,
        status=user.status,
        last_login_at=format_datetime(user.last_login_at),
        last_login_ip=user.last_login_ip,
    )
    return ResponseModel(data=user_response)


@user_router.post("/{user_id}/roles", response_model=ResponseModel)
async def assign_role_to_user(
    user_id: int, role_ids: List[int], db: AsyncSession = Depends(get_session)
):
    """
    为用户分配角�?"""
    await UserService.assign_role_to_user(db, user_id, role_ids)
    return ResponseModel(msg="分配成功")


@user_router.delete("/{user_id}", response_model=ResponseModel)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_session)):
    """
    删除用户
    """
    await UserService.delete_user(db, user_id)
    return ResponseModel(msg="删除成功")
