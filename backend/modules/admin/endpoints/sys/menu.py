#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
菜单管理相关接口
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from database.db_manager import get_session
from core.response.response_schema import ResponseModel

from app.models.sys.menu import SysMenu, MenuType
from modules.admin.services.sys import MenuService

# 创建菜单管理路由
menu_router = APIRouter(prefix="/menu", tags=["菜单管理"])


@menu_router.get("/list", response_model=ResponseModel[List[dict]])
async def get_menu_list(
    status: Optional[bool] = Query(None, description="状态"),
    db: AsyncSession = Depends(get_session),
):
    """
    获取菜单列表
    """
    menus = await MenuService.get_menu_list(db, status)
    return ResponseModel(data=menus)


@menu_router.get("/tree", response_model=ResponseModel[List[dict]])
async def get_menu_tree(db: AsyncSession = Depends(get_session)):
    """
    获取菜单树结�?"""
    root_menus = await MenuService.get_menu_tree(db)
    return ResponseModel(data=root_menus)


@menu_router.get("/pages", response_model=ResponseModel[List[str]])
async def get_all_pages(db: AsyncSession = Depends(get_session)):
    """
    获取所有页面
    """
    pages = await MenuService.get_all_pages(db)
    return ResponseModel(data=pages)


@menu_router.get("/{menu_id}", response_model=ResponseModel[SysMenu])
async def get_menu(menu_id: int, db: AsyncSession = Depends(get_session)):
    """
    获取单个菜单
    """
    menu = await MenuService.get_menu(db, menu_id)
    return ResponseModel(data=menu)


@menu_router.post("", response_model=ResponseModel[SysMenu])
async def create_menu(menu: SysMenu, db: AsyncSession = Depends(get_session)):
    """
    创建菜单
    """
    menu = await MenuService.create_menu(db, menu)
    return ResponseModel(data=menu)


@menu_router.put("/{menu_id}", response_model=ResponseModel[SysMenu])
async def update_menu(
    menu_id: int, menu: SysMenu, db: AsyncSession = Depends(get_session)
):
    """
    更新菜单
    """
    menu = await MenuService.update_menu(db, menu_id, menu)
    return ResponseModel(data=menu)


@menu_router.delete("/{menu_id}", response_model=ResponseModel)
async def delete_menu(menu_id: int, db: AsyncSession = Depends(get_session)):
    """
    删除菜单
    """
    await MenuService.delete_menu(db, menu_id)
    return ResponseModel(msg="删除成功")
