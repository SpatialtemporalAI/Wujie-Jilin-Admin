#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
角色管理相关接口
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from core.database.asyncio.database_manager import get_async_db
from core.response.response_schema import BaseResponse

from app.models.sys.role import SysRole
from modules.admin.services.sys import RoleService

# 创建角色管理路由器
role_router = APIRouter(
    prefix="/role",
    tags=["角色管理"]
)

@role_router.get("/list", response_model=BaseResponse[List[SysRole]])
async def get_role_list(
    status: Optional[bool] = Query(None, description="状态"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    获取角色列表
    """
    roles = await RoleService.get_role_list(db, status)
    return BaseResponse(data=roles)

@role_router.get("/{role_id}", response_model=BaseResponse[SysRole])
async def get_role(
    role_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """
    获取单个角色
    """
    role = await RoleService.get_role(db, role_id)
    return BaseResponse(data=role)

@role_router.post("", response_model=BaseResponse[SysRole])
async def create_role(
    role: SysRole,
    db: AsyncSession = Depends(get_async_db)
):
    """
    创建角色
    """
    role = await RoleService.create_role(db, role)
    return BaseResponse(data=role)

@role_router.put("/{role_id}", response_model=BaseResponse[SysRole])
async def update_role(
    role_id: int,
    role: SysRole,
    db: AsyncSession = Depends(get_async_db)
):
    """
    更新角色
    """
    role = await RoleService.update_role(db, role_id, role)
    return BaseResponse(data=role)

@role_router.post("/{role_id}/menus", response_model=BaseResponse)
async def assign_menu_to_role(
    role_id: int,
    menu_ids: List[int],
    db: AsyncSession = Depends(get_async_db)
):
    """
    为角色分配菜单权限
    """
    await RoleService.assign_menu_to_role(db, role_id, menu_ids)
    return BaseResponse(msg="分配成功")

@role_router.delete("/{role_id}", response_model=BaseResponse)
async def delete_role(
    role_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """
    删除角色
    """
    await RoleService.delete_role(db, role_id)
    return BaseResponse(msg="删除成功")
