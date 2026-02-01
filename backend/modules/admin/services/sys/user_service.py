#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
用户管理服务
处理用户相关的业务逻辑
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.models.sys.user import SysUser
from app.models.sys.role import SysRole
from core.exception.errors import NotFoundError


class UserService:
    """
    用户管理服务类
    """
    
    @staticmethod
    async def get_user_list(
        db: AsyncSession,
        status: Optional[bool] = None
    ) -> List[SysUser]:
        """
        获取用户列表
        
        Args:
            db: 数据库会话
            status: 状态
            
        Returns:
            用户列表
        """
        query = select(SysUser)
        if status is not None:
            query = query.where(SysUser.status == status)
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_user(
        db: AsyncSession,
        user_id: int
    ) -> SysUser:
        """
        获取单个用户
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            用户对象
            
        Raises:
            NotFoundError: 用户不存在
        """
        result = await db.execute(select(SysUser).where(SysUser.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError(f"用户 {user_id} 不存在")
        return user
    
    @staticmethod
    async def create_user(
        db: AsyncSession,
        user: SysUser
    ) -> SysUser:
        """
        创建用户
        
        Args:
            db: 数据库会话
            user: 用户对象
            
        Returns:
            创建后的用户对象
        """
        # 检查用户名是否已存在
        result = await db.execute(select(SysUser).where(SysUser.username == user.username))
        if result.scalar_one_or_none():
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="用户名已存在")
        
        # 检查邮箱是否已存在
        if user.email:
            result = await db.execute(select(SysUser).where(SysUser.email == user.email))
            if result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="邮箱已存在")
        
        # 检查手机号是否已存在
        if user.phone:
            result = await db.execute(select(SysUser).where(SysUser.phone == user.phone))
            if result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="手机号已存在")
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    
    @staticmethod
    async def update_user(
        db: AsyncSession,
        user_id: int,
        user: SysUser
    ) -> SysUser:
        """
        更新用户
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            user: 用户对象
            
        Returns:
            更新后的用户对象
            
        Raises:
            NotFoundError: 用户不存在
        """
        result = await db.execute(select(SysUser).where(SysUser.id == user_id))
        existing_user = result.scalar_one_or_none()
        if not existing_user:
            raise NotFoundError(f"用户 {user_id} 不存在")
        
        # 检查用户名是否已被其他用户使用
        if user.username != existing_user.username:
            result = await db.execute(
                select(SysUser).where(SysUser.username == user.username, SysUser.id != user_id)
            )
            if result.scalar_one_or_none():
                from fastapi import HTTPException
                raise HTTPException(status_code=400, detail="用户名已存在")
        
        # 检查邮箱是否已被其他用户使用
        if user.email and user.email != existing_user.email:
            result = await db.execute(
                select(SysUser).where(SysUser.email == user.email, SysUser.id != user_id)
            )
            if result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="邮箱已存在")
        
        # 检查手机号是否已被其他用户使用
        if user.phone and user.phone != existing_user.phone:
            result = await db.execute(
                select(SysUser).where(SysUser.phone == user.phone, SysUser.id != user_id)
            )
            if result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="手机号已存在")
        
        # 更新用户
        for key, value in user.__dict__.items():
            if key not in ["id", "created_at", "updated_at"] and hasattr(existing_user, key):
                setattr(existing_user, key, value)
        
        await db.commit()
        await db.refresh(existing_user)
        return existing_user
    
    @staticmethod
    async def assign_role_to_user(
        db: AsyncSession,
        user_id: int,
        role_ids: List[int]
    ) -> bool:
        """
        为用户分配角色
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            role_ids: 角色ID列表
            
        Returns:
            是否分配成功
            
        Raises:
            NotFoundError: 用户不存在
        """
        # 获取用户
        result = await db.execute(select(SysUser).where(SysUser.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError(f"用户 {user_id} 不存在")
        
        # 获取角色
        result = await db.execute(select(SysRole).where(SysRole.id.in_(role_ids)))
        roles = result.scalars().all()
        
        # 分配角色
        user.roles = roles
        await db.commit()
        return True
    
    @staticmethod
    async def delete_user(
        db: AsyncSession,
        user_id: int
    ) -> bool:
        """
        删除用户
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            是否删除成功
            
        Raises:
            NotFoundError: 用户不存在
        """
        result = await db.execute(select(SysUser).where(SysUser.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError(f"用户 {user_id} 不存在")
        
        await db.delete(user)
        await db.commit()
        return True
