#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
菜单管理服务
处理菜单相关的业务逻辑
"""
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional

from app.models.sys.menu import SysMenu, MenuType
from core.exception.errors import NotFoundError, ConflictError
from modules.admin.schemas.sys.menu import (
    SysMenuCreate,
    SysMenuUpdate,
    SysMenuQueryParams,
    SysMenuTreeResponse,
)

logger = logging.getLogger(__name__)


class MenuService:
    """
    菜单管理服务类
    """

    @staticmethod
    async def get_menu_list(
        db: AsyncSession,
        query_params: SysMenuQueryParams,
    ) -> List[SysMenu]:
        """
        获取菜单列表（带查询条件）

        Args:
            db: 数据库会话
            query_params: 查询参数

        Returns:
            菜单列表
        """
        logger.info(f"获取菜单列表，查询参数: {query_params}")

        # 构建基础查询
        base_query = select(SysMenu)

        # 添加查询条件
        conditions = []
        if query_params.status is not None:
            conditions.append(SysMenu.status == query_params.status)
        if query_params.name:
            conditions.append(SysMenu.name.like(f"%{query_params.name}%"))
        if query_params.type:
            conditions.append(SysMenu.type == query_params.type)

        if conditions:
            base_query = base_query.where(and_(*conditions))

        # 添加排序
        base_query = base_query.order_by(SysMenu.sort, SysMenu.id)

        # 执行查询
        result = await db.execute(base_query)
        menus = result.scalars().all()

        logger.info(f"获取菜单列表成功，共 {len(menus)} 条记录")
        return menus

    @staticmethod
    async def get_menu_tree(
        db: AsyncSession,
        status: Optional[bool] = None,
    ) -> List[SysMenuTreeResponse]:
        """
        获取菜单树结构

        Args:
            db: 数据库会话
            status: 状态筛选

        Returns:
            菜单树结构
        """
        logger.info(f"获取菜单树结构，状态: {status}")

        # 先获取所有菜单
        base_query = select(SysMenu).order_by(SysMenu.sort, SysMenu.id)
        if status is not None:
            base_query = base_query.where(SysMenu.status == status)

        result = await db.execute(base_query)
        menus = result.scalars().all()

        # 构建菜单字典映射
        menu_map = {}
        root_menus = []

        # 首先创建所有菜单的响应模型实例
        for menu in menus:
            menu_response = SysMenuTreeResponse(
                id=menu.id,
                parent_id=menu.parent_id,
                name=menu.name,
                path=menu.path,
                component=menu.component,
                redirect=menu.redirect,
                permission=menu.permission,
                meta_title=menu.meta_title,
                meta_icon=menu.meta_icon,
                meta_hidden=menu.meta_hidden,
                meta_affix=menu.meta_affix,
                meta_breadcrumb=menu.meta_breadcrumb,
                status=menu.status,
                type=menu.type,
                sort=menu.sort,
                children=[],
            )
            menu_map[menu.id] = menu_response

        # 构建树结构
        for menu in menus:
            menu_response = menu_map[menu.id]
            if not menu.parent_id:
                root_menus.append(menu_response)
            else:
                parent = menu_map.get(menu.parent_id)
                if parent:
                    parent.children.append(menu_response)

        logger.info(f"获取菜单树结构成功，共 {len(root_menus)} 个根菜单")
        return root_menus

    @staticmethod
    async def get_menu(db: AsyncSession, menu_id: int) -> SysMenu:
        """
        获取单个菜单

        Args:
            db: 数据库会话
            menu_id: 菜单ID

        Returns:
            菜单对象

        Raises:
            NotFoundError: 菜单不存在
        """
        logger.info(f"获取菜单信息，菜单ID: {menu_id}")

        result = await db.execute(select(SysMenu).where(SysMenu.id == menu_id))
        menu = result.scalar_one_or_none()

        if not menu:
            logger.warning(f"菜单不存在，菜单ID: {menu_id}")
            raise NotFoundError(msg=f"菜单 {menu_id} 不存在")

        logger.info(f"获取菜单信息成功，菜单名称: {menu.name}")
        return menu

    @staticmethod
    async def create_menu(db: AsyncSession, menu_create: SysMenuCreate) -> SysMenu:
        """
        创建菜单

        Args:
            db: 数据库会话
            menu_create: 菜单创建请求模型

        Returns:
            创建后的菜单对象

        Raises:
            NotFoundError: 父菜单不存在
            ConflictError: 菜单名称已存在
        """
        logger.info(f"创建菜单，菜单名称: {menu_create.name}")

        # 检查父菜单是否存在
        if menu_create.parent_id:
            result = await db.execute(
                select(SysMenu).where(SysMenu.id == menu_create.parent_id)
            )
            if not result.scalar_one_or_none():
                logger.warning(f"创建菜单失败，父菜单不存在: {menu_create.parent_id}")
                raise NotFoundError(msg=f"父菜单 {menu_create.parent_id} 不存在")

        # 创建菜单对象
        menu = SysMenu(
            parent_id=menu_create.parent_id,
            name=menu_create.name,
            path=menu_create.path,
            component=menu_create.component,
            redirect=menu_create.redirect,
            permission=menu_create.permission,
            meta_title=menu_create.meta_title,
            meta_icon=menu_create.meta_icon,
            meta_hidden=menu_create.meta_hidden,
            meta_affix=menu_create.meta_affix,
            meta_breadcrumb=menu_create.meta_breadcrumb,
            status=menu_create.status,
            type=menu_create.type,
            sort=menu_create.sort,
        )

        db.add(menu)
        await db.commit()
        await db.refresh(menu)

        logger.info(f"创建菜单成功，菜单ID: {menu.id}")
        return menu

    @staticmethod
    async def update_menu(
        db: AsyncSession, menu_id: int, menu_update: SysMenuUpdate
    ) -> SysMenu:
        """
        更新菜单

        Args:
            db: 数据库会话
            menu_id: 菜单ID
            menu_update: 菜单更新请求模型

        Returns:
            更新后的菜单对象

        Raises:
            NotFoundError: 菜单不存在或父菜单不存在
            ConflictError: 不能将自己设置为父菜单
        """
        logger.info(f"更新菜单信息，菜单ID: {menu_id}")

        # 获取菜单
        menu = await MenuService.get_menu(db, menu_id)

        # 检查父菜单
        if menu_update.parent_id is not None:
            # 不能将自己设置为父菜单
            if menu_update.parent_id == menu_id:
                logger.warning(f"更新菜单失败，不能将自己设置为父菜单: {menu_id}")
                raise ConflictError(msg="不能将自己设置为父菜单")

            # 检查父菜单是否存在
            if menu_update.parent_id:
                result = await db.execute(
                    select(SysMenu).where(SysMenu.id == menu_update.parent_id)
                )
                if not result.scalar_one_or_none():
                    logger.warning(
                        f"更新菜单失败，父菜单不存在: {menu_update.parent_id}"
                    )
                    raise NotFoundError(msg=f"父菜单 {menu_update.parent_id} 不存在")

        # 更新菜单信息
        update_data = menu_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(menu, key):
                setattr(menu, key, value)

        await db.commit()
        await db.refresh(menu)

        logger.info(f"更新菜单信息成功，菜单ID: {menu_id}")
        return menu

    @staticmethod
    async def delete_menu(db: AsyncSession, menu_id: int) -> bool:
        """
        删除菜单

        Args:
            db: 数据库会话
            menu_id: 菜单ID

        Returns:
            是否删除成功

        Raises:
            NotFoundError: 菜单不存在
        """
        logger.info(f"删除菜单，菜单ID: {menu_id}")

        # 获取菜单
        menu = await MenuService.get_menu(db, menu_id)

        await db.delete(menu)
        await db.commit()

        logger.info(f"删除菜单成功，菜单ID: {menu_id}")
        return True

    @staticmethod
    async def batch_update_menus_status(
        db: AsyncSession, menu_ids: List[int], status: bool
    ) -> int:
        """
        批量更新菜单状态

        Args:
            db: 数据库会话
            menu_ids: 菜单ID列表
            status: 要设置的状态

        Returns:
            更新的菜单数量
        """
        logger.info(f"批量更新菜单状态，菜单ID列表: {menu_ids}, 状态: {status}")

        # 获取菜单
        result = await db.execute(select(SysMenu).where(SysMenu.id.in_(menu_ids)))
        menus = result.scalars().all()

        # 更新状态
        update_count = 0
        for menu in menus:
            menu.status = status
            update_count += 1

        await db.commit()

        logger.info(f"批量更新菜单状态成功，共更新 {update_count} 个菜单")
        return update_count
