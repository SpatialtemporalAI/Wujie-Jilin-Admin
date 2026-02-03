#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
角色管理相关接口
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from database.db_manager import get_session
from core.response.response_schema import ResponseModel

from app.models.sys.role import SysRole
from modules.admin.services.sys import RoleService

# 创建角色管理路由
role_router = APIRouter(prefix="/role", tags=["角色管理"])


@role_router.get("/list", response_model=ResponseModel[List[SysRole]])
async def get_role_list(
    status: Optional[bool] = Query(None, description="状态"),
    db: AsyncSession = Depends(get_session),
):
    """
    获取角色列表
    """
    roles = await RoleService.get_role_list(db, status)
    return ResponseModel(data=roles)


@role_router.get("/{role_id}", response_model=ResponseModel[SysRole])
async def get_role(role_id: int, db: AsyncSession = Depends(get_session)):
    """
    获取单个角色
    """
    role = await RoleService.get_role(db, role_id)
    return ResponseModel(data=role)


@role_router.post("", response_model=ResponseModel[SysRole])
async def create_role(role: SysRole, db: AsyncSession = Depends(get_session)):
    """
    创建角色
    """
    role = await RoleService.create_role(db, role)
    return ResponseModel(data=role)


@role_router.put("/{role_id}", response_model=ResponseModel[SysRole])
async def update_role(
    role_id: int, role: SysRole, db: AsyncSession = Depends(get_session)
):
    """
    更新角色
    """
    role = await RoleService.update_role(db, role_id, role)
    return ResponseModel(data=role)


@role_router.post("/{role_id}/menus", response_model=ResponseModel)
async def assign_menu_to_role(
    role_id: int, menu_ids: List[int], db: AsyncSession = Depends(get_session)
):
    """
    为角色分配菜单权�?"""
    await RoleService.assign_menu_to_role(db, role_id, menu_ids)
    return ResponseModel(msg="分配成功")


@role_router.delete("/{role_id}", response_model=ResponseModel)
async def delete_role(role_id: int, db: AsyncSession = Depends(get_session)):
    """
    删除角色
    """
    await RoleService.delete_role(db, role_id)
    return ResponseModel(msg="删除成功")
