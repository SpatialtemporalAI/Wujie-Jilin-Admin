#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
权限管理相关接口
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from database.db_manager import get_session
from core.response.response_schema import ResponseModel

from app.models.sys.permission import SysPermission
from app.models.common.base import BoolField
from pydantic import BaseModel, Field
from modules.admin.services.sys import PermissionService


class SysPermissionQueryParams(BaseModel):
    """
    系统权限查询参数模型
    用于权限列表查询时的筛选条件
    """

    category: Optional[str] = Field(None, description="权限分类")
    status: BoolField = Field(None, description="状态：True-启用，False-禁用")


# 创建权限管理路由
permission_router = APIRouter(prefix="/permission", tags=["权限管理"])


@permission_router.get("/list", response_model=ResponseModel[List[SysPermission]])
async def get_permission_list(
    query_params: SysPermissionQueryParams = Depends(),
    db: AsyncSession = Depends(get_session),
):
    """
    获取权限列表
    """
    permissions = await PermissionService.get_permission_list(
        db, query_params.category, query_params.status
    )
    return ResponseModel(data=permissions)


@permission_router.post("", response_model=ResponseModel[SysPermission])
async def create_permission(
    permission: SysPermission, db: AsyncSession = Depends(get_session)
):
    """
    创建权限
    """
    permission = await PermissionService.create_permission(db, permission)
    return ResponseModel(data=permission)


@permission_router.put("/{permission_id}", response_model=ResponseModel[SysPermission])
async def update_permission(
    permission_id: int,
    permission: SysPermission,
    db: AsyncSession = Depends(get_session),
):
    """
    更新权限
    """
    permission = await PermissionService.update_permission(
        db, permission_id, permission
    )
    return ResponseModel(data=permission)


@permission_router.delete("/{permission_id}", response_model=ResponseModel)
async def delete_permission(
    permission_id: int, db: AsyncSession = Depends(get_session)
):
    """
    删除权限
    """
    await PermissionService.delete_permission(db, permission_id)
    return ResponseModel(msg="删除成功")
