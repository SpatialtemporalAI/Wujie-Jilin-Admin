#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
菜单管理相关接口
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from core.database.asyncio.database_manager import get_async_db
from core.response.response_schema import BaseResponse

from app.models.sys.menu import SysMenu, MenuType
from modules.admin.services.sys import MenuService

# 创建菜单管理路由器
menu_router = APIRouter(
    prefix="/menu",
    tags=["菜单管理"]
)

@menu_router.get("/list", response_model=BaseResponse[List[SysMenu]])
async def get_menu_list(
    status: Optional[bool] = Query(None, description="状态"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    获取菜单列表
    """
    menus = await MenuService.get_menu_list(db, status)
    return BaseResponse(data=menus)

@menu_router.get("/tree", response_model=BaseResponse[List[SysMenu]])
async def get_menu_tree(
    db: AsyncSession = Depends(get_async_db)
):
    """
    获取菜单树结构
    """
    root_menus = await MenuService.get_menu_tree(db)
    return BaseResponse(data=root_menus)

@menu_router.get("/{menu_id}", response_model=BaseResponse[SysMenu])
async def get_menu(
    menu_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """
    获取单个菜单
    """
    menu = await MenuService.get_menu(db, menu_id)
    return BaseResponse(data=menu)

@menu_router.post("", response_model=BaseResponse[SysMenu])
async def create_menu(
    menu: SysMenu,
    db: AsyncSession = Depends(get_async_db)
):
    """
    创建菜单
    """
    menu = await MenuService.create_menu(db, menu)
    return BaseResponse(data=menu)

@menu_router.put("/{menu_id}", response_model=BaseResponse[SysMenu])
async def update_menu(
    menu_id: int,
    menu: SysMenu,
    db: AsyncSession = Depends(get_async_db)
):
    """
    更新菜单
    """
    menu = await MenuService.update_menu(db, menu_id, menu)
    return BaseResponse(data=menu)

@menu_router.delete("/{menu_id}", response_model=BaseResponse)
async def delete_menu(
    menu_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """
    删除菜单
    """
    await MenuService.delete_menu(db, menu_id)
    return BaseResponse(msg="删除成功")
