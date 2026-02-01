#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
角色管理服务
处理角色相关的业务逻辑
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.models.sys.role import SysRole
from app.models.sys.menu import SysMenu
from core.exception.errors import NotFoundError


class RoleService:
    """
    角色管理服务类
    """
    
    @staticmethod
    async def get_role_list(
        db: AsyncSession,
        status: Optional[bool] = None
    ) -> List[SysRole]:
        """
        获取角色列表
        
        Args:
            db: 数据库会话
            status: 状态
            
        Returns:
            角色列表
        """
        query = select(SysRole)
        if status is not None:
            query = query.where(SysRole.status == status)
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_role(
        db: AsyncSession,
        role_id: int
    ) -> SysRole:
        """
        获取单个角色
        
        Args:
            db: 数据库会话
            role_id: 角色ID
            
        Returns:
            角色对象
            
        Raises:
            NotFoundError: 角色不存在
        """
        result = await db.execute(select(SysRole).where(SysRole.id == role_id))
        role = result.scalar_one_or_none()
        if not role:
            raise NotFoundError(f"角色 {role_id} 不存在")
        return role
    
    @staticmethod
    async def create_role(
        db: AsyncSession,
        role: SysRole
    ) -> SysRole:
        """
        创建角色
        
        Args:
            db: 数据库会话
            role: 角色对象
            
        Returns:
            创建后的角色对象
        """
        # 检查角色编码是否已存在
        result = await db.execute(select(SysRole).where(SysRole.code == role.code))
        if result.scalar_one_or_none():
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="角色编码已存在")
        
        db.add(role)
        await db.commit()
        await db.refresh(role)
        return role
    
    @staticmethod
    async def update_role(
        db: AsyncSession,
        role_id: int,
        role: SysRole
    ) -> SysRole:
        """
        更新角色
        
        Args:
            db: 数据库会话
            role_id: 角色ID
            role: 角色对象
            
        Returns:
            更新后的角色对象
            
        Raises:
            NotFoundError: 角色不存在
        """
        result = await db.execute(select(SysRole).where(SysRole.id == role_id))
        existing_role = result.scalar_one_or_none()
        if not existing_role:
            raise NotFoundError(f"角色 {role_id} 不存在")
        
        # 更新角色
        for key, value in role.__dict__.items():
            if key not in ["id", "created_at", "updated_at"] and hasattr(existing_role, key):
                setattr(existing_role, key, value)
        
        await db.commit()
        await db.refresh(existing_role)
        return existing_role
    
    @staticmethod
    async def assign_menu_to_role(
        db: AsyncSession,
        role_id: int,
        menu_ids: List[int]
    ) -> bool:
        """
        为角色分配菜单权限
        
        Args:
            db: 数据库会话
            role_id: 角色ID
            menu_ids: 菜单ID列表
            
        Returns:
            是否分配成功
            
        Raises:
            NotFoundError: 角色不存在
        """
        # 获取角色
        result = await db.execute(select(SysRole).where(SysRole.id == role_id))
        role = result.scalar_one_or_none()
        if not role:
            raise NotFoundError(f"角色 {role_id} 不存在")
        
        # 获取菜单
        result = await db.execute(select(SysMenu).where(SysMenu.id.in_(menu_ids)))
        menus = result.scalars().all()
        
        # 分配菜单
        role.menus = menus
        await db.commit()
        return True
    
    @staticmethod
    async def delete_role(
        db: AsyncSession,
        role_id: int
    ) -> bool:
        """
        删除角色
        
        Args:
            db: 数据库会话
            role_id: 角色ID
            
        Returns:
            是否删除成功
            
        Raises:
            NotFoundError: 角色不存在
        """
        result = await db.execute(select(SysRole).where(SysRole.id == role_id))
        role = result.scalar_one_or_none()
        if not role:
            raise NotFoundError(f"角色 {role_id} 不存在")
        
        await db.delete(role)
        await db.commit()
        return True
