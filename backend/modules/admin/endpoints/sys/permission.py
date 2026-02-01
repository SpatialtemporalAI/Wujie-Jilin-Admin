#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
权限管理相关接口
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from core.database.asyncio.database_manager import get_async_db
from core.response.response_schema import BaseResponse

from app.models.sys.permission import SysPermission
from modules.admin.services.sys import PermissionService

# 创建权限管理路由器
permission_router = APIRouter(
    prefix="/permission",
    tags=["权限管理"]
)

@permission_router.get("/list", response_model=BaseResponse[List[SysPermission]])
async def get_permission_list(
    category: Optional[str] = Query(None, description="权限分类"),
    status: Optional[bool] = Query(None, description="状态"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    获取权限列表
    """
    permissions = await PermissionService.get_permission_list(db, category, status)
    return BaseResponse(data=permissions)

@permission_router.post("", response_model=BaseResponse[SysPermission])
async def create_permission(
    permission: SysPermission,
    db: AsyncSession = Depends(get_async_db)
):
    """
    创建权限
    """
    permission = await PermissionService.create_permission(db, permission)
    return BaseResponse(data=permission)

@permission_router.put("/{permission_id}", response_model=BaseResponse[SysPermission])
async def update_permission(
    permission_id: int,
    permission: SysPermission,
    db: AsyncSession = Depends(get_async_db)
):
    """
    更新权限
    """
    permission = await PermissionService.update_permission(db, permission_id, permission)
    return BaseResponse(data=permission)

@permission_router.delete("/{permission_id}", response_model=BaseResponse)
async def delete_permission(
    permission_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """
    删除权限
    """
    await PermissionService.delete_permission(db, permission_id)
    return BaseResponse(msg="删除成功")
