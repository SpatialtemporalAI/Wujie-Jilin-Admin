#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
权限管理服务
处理权限相关的业务逻辑
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.models.sys.permission import SysPermission
from core.exception.errors import NotFoundError


class PermissionService:
    """
    权限管理服务类
    """
    
    @staticmethod
    async def get_permission_list(
        db: AsyncSession,
        category: Optional[str] = None,
        status: Optional[bool] = None
    ) -> List[SysPermission]:
        """
        获取权限列表
        
        Args:
            db: 数据库会话
            category: 权限分类
            status: 状态
            
        Returns:
            权限列表
        """
        query = select(SysPermission)
        if category:
            query = query.where(SysPermission.category == category)
        if status is not None:
            query = query.where(SysPermission.status == status)
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def create_permission(
        db: AsyncSession,
        permission: SysPermission
    ) -> SysPermission:
        """
        创建权限
        
        Args:
            db: 数据库会话
            permission: 权限对象
            
        Returns:
            创建后的权限对象
        """
        # 检查权限编码是否已存在
        result = await db.execute(select(SysPermission).where(SysPermission.code == permission.code))
        if result.scalar_one_or_none():
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="权限编码已存在")
        
        db.add(permission)
        await db.commit()
        await db.refresh(permission)
        return permission
    
    @staticmethod
    async def update_permission(
        db: AsyncSession,
        permission_id: int,
        permission: SysPermission
    ) -> SysPermission:
        """
        更新权限
        
        Args:
            db: 数据库会话
            permission_id: 权限ID
            permission: 权限对象
            
        Returns:
            更新后的权限对象
            
        Raises:
            NotFoundError: 权限不存在
        """
        result = await db.execute(select(SysPermission).where(SysPermission.id == permission_id))
        existing_permission = result.scalar_one_or_none()
        if not existing_permission:
            raise NotFoundError(f"权限 {permission_id} 不存在")
        
        # 更新权限
        for key, value in permission.__dict__.items():
            if key not in ["id", "created_at", "updated_at"] and hasattr(existing_permission, key):
                setattr(existing_permission, key, value)
        
        await db.commit()
        await db.refresh(existing_permission)
        return existing_permission
    
    @staticmethod
    async def delete_permission(
        db: AsyncSession,
        permission_id: int
    ) -> bool:
        """
        删除权限
        
        Args:
            db: 数据库会话
            permission_id: 权限ID
            
        Returns:
            是否删除成功
            
        Raises:
            NotFoundError: 权限不存在
        """
        result = await db.execute(select(SysPermission).where(SysPermission.id == permission_id))
        permission = result.scalar_one_or_none()
        if not permission:
            raise NotFoundError(f"权限 {permission_id} 不存在")
        
        await db.delete(permission)
        await db.commit()
        return True
