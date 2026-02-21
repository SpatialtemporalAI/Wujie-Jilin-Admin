#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
菜单管理相关接口
"""
import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from database.db_manager import get_session
from core.response.response_schema import (
    ResponseModel,
    ResponsePageModel,
    ResponsePageDataModel,
    response_base,
)
from app.models.common.page import PageRequest, get_page_params, get_paginated_results

from modules.admin.services.sys import MenuService
from modules.admin.schemas.sys.menu import (
    SysMenuResponseData,
    SysMenuTreeResponse,
    SysMenuCreate,
    SysMenuUpdate,
    SysMenuQueryParams,
    SysMenuBatchUpdateStatus,
)
from app.models.sys.menu import MenuType

logger = logging.getLogger(__name__)

# 页面组件列表（模拟前端的视图组件）
PAGE_COMPONENTS = [
    "403",
    "404",
    "500",
    "iframe-page",
    "login",
    "home",
    "manage_config",
    "manage_dict",
    "manage_menu",
    "manage_role",
    "manage_user-detail",
    "manage_user",
]


def parse_bool_param(value: Optional[str]) -> Optional[bool]:
    """
    解析布尔类型参数

    Args:
        value: 参数字符串

    Returns:
        布尔值或None
    """
    if value is None or value == "":
        return None
    if value.lower() in ("true", "1", "yes", "y"):
        return True
    if value.lower() in ("false", "0", "no", "n"):
        return False
    return None


def parse_menu_type_param(value: Optional[str]) -> Optional[MenuType]:
    """
    解析菜单类型参数

    Args:
        value: 参数字符串

    Returns:
        MenuType枚举或None
    """
    if value is None or value == "":
        return None
    try:
        return MenuType(value)
    except ValueError:
        return None


# 创建菜单管理路由
menu_router = APIRouter(prefix="/menu", tags=["菜单管理"])


@menu_router.get("/pages", response_model=ResponseModel[List[str]])
async def get_all_pages():
    """
    获取所有页面组件列表
    """
    logger.info("获取所有页面组件列表")
    return ResponseModel(data=PAGE_COMPONENTS)


@menu_router.get("/list", response_model=ResponsePageModel[SysMenuResponseData])
async def get_menu_list(
    name: Optional[str] = Query(None, description="菜单名称，支持模糊查询"),
    status: Optional[str] = Query(None, description="菜单状态"),
    type: Optional[str] = Query(None, description="菜单类型"),
    page_params: PageRequest = Depends(get_page_params),
    db: AsyncSession = Depends(get_session),
):
    """
    获取菜单列表（分页）
    """
    logger.info("获取菜单列表请求")

    # 构建查询参数
    query_params = SysMenuQueryParams(
        name=name,
        status=parse_bool_param(status),
        type=parse_menu_type_param(type),
    )

    # 构建查询对象
    query = MenuService.build_menu_query(query_params)

    # 使用通用分页方法
    page_data = await get_paginated_results(
        db=db,
        page_params=page_params,
        query=query,
        schema=SysMenuResponseData,
    )

    logger.info(f"获取菜单列表成功，共 {page_data.total} 条记录")
    return response_base.page(data=page_data)


@menu_router.get("/tree", response_model=ResponseModel[List[SysMenuTreeResponse]])
async def get_menu_tree(
    status: Optional[str] = Query(None, description="状态筛选"),
    db: AsyncSession = Depends(get_session),
):
    """
    获取菜单树结构
    """
    logger.info("获取菜单树结构请求")

    menu_tree = await MenuService.get_menu_tree(db, status=parse_bool_param(status))

    logger.info(f"获取菜单树结构成功，共 {len(menu_tree)} 个根菜单")
    return ResponseModel(data=menu_tree)


@menu_router.get("/{menu_id}", response_model=ResponseModel[SysMenuResponseData])
async def get_menu(
    menu_id: int,
    db: AsyncSession = Depends(get_session),
):
    """
    获取单个菜单
    """
    logger.info(f"获取单个菜单请求，菜单ID: {menu_id}")

    menu = await MenuService.get_menu(db, menu_id)
    menu_response = SysMenuResponseData.model_validate(menu)

    logger.info(f"获取单个菜单成功，菜单ID: {menu_id}")
    return ResponseModel(data=menu_response)


@menu_router.post("/add", response_model=ResponseModel[SysMenuResponseData])
async def create_menu(
    menu_create: SysMenuCreate,
    db: AsyncSession = Depends(get_session),
):
    """
    创建菜单
    """
    logger.info(f"创建菜单请求，菜单名称: {menu_create.name}")

    menu = await MenuService.create_menu(db, menu_create)
    menu_response = SysMenuResponseData.model_validate(menu)

    logger.info(f"创建菜单成功，菜单ID: {menu.id}")
    return ResponseModel(data=menu_response, msg="创建菜单成功")


@menu_router.put("/{menu_id}", response_model=ResponseModel[SysMenuResponseData])
async def update_menu(
    menu_id: int,
    menu_update: SysMenuUpdate,
    db: AsyncSession = Depends(get_session),
):
    """
    更新菜单
    """
    logger.info(f"更新菜单请求，菜单ID: {menu_id}")

    menu = await MenuService.update_menu(db, menu_id, menu_update)
    menu_response = SysMenuResponseData.model_validate(menu)

    logger.info(f"更新菜单成功，菜单ID: {menu_id}")
    return ResponseModel(data=menu_response, msg="更新菜单成功")


@menu_router.delete("/{menu_id}", response_model=ResponseModel)
async def delete_menu(
    menu_id: int,
    db: AsyncSession = Depends(get_session),
):
    """
    删除菜单
    """
    logger.info(f"删除菜单请求，菜单ID: {menu_id}")

    await MenuService.delete_menu(db, menu_id)

    logger.info(f"删除菜单成功，菜单ID: {menu_id}")
    return ResponseModel(msg="删除菜单成功")


@menu_router.put("/batch/status", response_model=ResponseModel)
async def batch_update_menus_status(
    batch_update: SysMenuBatchUpdateStatus,
    db: AsyncSession = Depends(get_session),
):
    """
    批量更新菜单状态
    """
    logger.info(
        f"批量更新菜单状态请求，菜单ID: {batch_update.menu_ids}, 状态: {batch_update.status}"
    )

    update_count = await MenuService.batch_update_menus_status(
        db, batch_update.menu_ids, batch_update.status
    )

    status_text = "启用" if batch_update.status else "禁用"
    logger.info(f"批量更新菜单状态成功，共 {update_count} 个菜单被{status_text}")
    return ResponseModel(
        msg=f"批量{status_text}成功，共 {update_count} 个菜单",
        data={"update_count": update_count},
    )


@menu_router.delete("/batch/delete", response_model=ResponseModel)
async def batch_delete_menus(
    menu_ids: List[int],
    db: AsyncSession = Depends(get_session),
):
    """
    批量删除菜单
    """
    logger.info(f"批量删除菜单请求，菜单ID: {menu_ids}")

    delete_count = await MenuService.batch_delete_menus(db, menu_ids)

    logger.info(f"批量删除菜单成功，共删除 {delete_count} 个菜单")
    return ResponseModel(
        msg=f"批量删除成功，共删除 {delete_count} 个菜单",
        data={"delete_count": delete_count},
    )
