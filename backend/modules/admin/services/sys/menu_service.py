#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
菜单管理服务
处理菜单相关的业务逻辑
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.models.sys.menu import SysMenu, MenuType
from core.exception.errors import NotFoundError


class MenuService:
    """
    菜单管理服务类
    """
    
    @staticmethod
    async def get_menu_list(
        db: AsyncSession,
        status: Optional[bool] = None
    ) -> List[SysMenu]:
        """
        获取菜单列表
        
        Args:
            db: 数据库会话
            status: 状态
            
        Returns:
            菜单列表
        """
        query = select(SysMenu)
        if status is not None:
            query = query.where(SysMenu.status == status)
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_menu_tree(
        db: AsyncSession
    ) -> List[SysMenu]:
        """
        获取菜单树结构
        
        Args:
            db: 数据库会话
            
        Returns:
            菜单树结构
        """
        # 先获取所有菜单
        result = await db.execute(select(SysMenu).order_by(SysMenu.sort))
        menus = result.scalars().all()
        
        # 构建树结构
        menu_map = {menu.id: menu for menu in menus}
        root_menus = []
        
        for menu in menus:
            if not menu.parent_id:
                root_menus.append(menu)
            else:
                parent = menu_map.get(menu.parent_id)
                if parent:
                    if not hasattr(parent, "children"):
                        parent.children = []
                    parent.children.append(menu)
        
        return root_menus
    
    @staticmethod
    async def get_menu(
        db: AsyncSession,
        menu_id: int
    ) -> SysMenu:
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
        result = await db.execute(select(SysMenu).where(SysMenu.id == menu_id))
        menu = result.scalar_one_or_none()
        if not menu:
            raise NotFoundError(f"菜单 {menu_id} 不存在")
        return menu
    
    @staticmethod
    async def create_menu(
        db: AsyncSession,
        menu: SysMenu
    ) -> SysMenu:
        """
        创建菜单
        
        Args:
            db: 数据库会话
            menu: 菜单对象
            
        Returns:
            创建后的菜单对象
            
        Raises:
            NotFoundError: 父菜单不存在
        """
        # 检查父菜单是否存在
        if menu.parent_id:
            result = await db.execute(select(SysMenu).where(SysMenu.id == menu.parent_id))
            if not result.scalar_one_or_none():
                raise NotFoundError(f"父菜单 {menu.parent_id} 不存在")
        
        db.add(menu)
        await db.commit()
        await db.refresh(menu)
        return menu
    
    @staticmethod
    async def update_menu(
        db: AsyncSession,
        menu_id: int,
        menu: SysMenu
    ) -> SysMenu:
        """
        更新菜单
        
        Args:
            db: 数据库会话
            menu_id: 菜单ID
            menu: 菜单对象
            
        Returns:
            更新后的菜单对象
            
        Raises:
            NotFoundError: 菜单不存在或父菜单不存在
        """
        result = await db.execute(select(SysMenu).where(SysMenu.id == menu_id))
        existing_menu = result.scalar_one_or_none()
        if not existing_menu:
            raise NotFoundError(f"菜单 {menu_id} 不存在")
        
        # 检查父菜单是否存在
        if menu.parent_id and menu.parent_id != existing_menu.id:
            result = await db.execute(select(SysMenu).where(SysMenu.id == menu.parent_id))
            if not result.scalar_one_or_none():
                raise NotFoundError(f"父菜单 {menu.parent_id} 不存在")
        
        # 更新菜单
        for key, value in menu.__dict__.items():
            if key not in ["id", "created_at", "updated_at"] and hasattr(existing_menu, key):
                setattr(existing_menu, key, value)
        
        await db.commit()
        await db.refresh(existing_menu)
        return existing_menu
    
    @staticmethod
    async def delete_menu(
        db: AsyncSession,
        menu_id: int
    ) -> bool:
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
        result = await db.execute(select(SysMenu).where(SysMenu.id == menu_id))
        menu = result.scalar_one_or_none()
        if not menu:
            raise NotFoundError(f"菜单 {menu_id} 不存在")
        
        await db.delete(menu)
        await db.commit()
        return True
