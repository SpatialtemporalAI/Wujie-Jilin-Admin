#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
用户管理相关接口
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from core.database.asyncio.database_manager import get_async_db
from core.response.response_schema import BaseResponse

from app.models.sys.user import SysUser
from modules.admin.services.sys import UserService

# 创建用户管理路由器
user_router = APIRouter(
    prefix="/user",
    tags=["用户管理"]
)

@user_router.get("/list", response_model=BaseResponse[List[SysUser]])
async def get_user_list(
    status: Optional[bool] = Query(None, description="状态"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    获取用户列表
    """
    users = await UserService.get_user_list(db, status)
    return BaseResponse(data=users)

@user_router.get("/{user_id}", response_model=BaseResponse[SysUser])
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """
    获取单个用户
    """
    user = await UserService.get_user(db, user_id)
    return BaseResponse(data=user)

@user_router.post("", response_model=BaseResponse[SysUser])
async def create_user(
    user: SysUser,
    db: AsyncSession = Depends(get_async_db)
):
    """
    创建用户
    """
    user = await UserService.create_user(db, user)
    return BaseResponse(data=user)

@user_router.put("/{user_id}", response_model=BaseResponse[SysUser])
async def update_user(
    user_id: int,
    user: SysUser,
    db: AsyncSession = Depends(get_async_db)
):
    """
    更新用户
    """
    user = await UserService.update_user(db, user_id, user)
    return BaseResponse(data=user)

@user_router.post("/{user_id}/roles", response_model=BaseResponse)
async def assign_role_to_user(
    user_id: int,
    role_ids: List[int],
    db: AsyncSession = Depends(get_async_db)
):
    """
    为用户分配角色
    """
    await UserService.assign_role_to_user(db, user_id, role_ids)
    return BaseResponse(msg="分配成功")

@user_router.delete("/{user_id}", response_model=BaseResponse)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """
    删除用户
    """
    await UserService.delete_user(db, user_id)
    return BaseResponse(msg="删除成功")
