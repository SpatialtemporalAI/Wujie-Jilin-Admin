#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
字典管理服务
处理字典相关的业务逻辑
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.models.sys.dict import SysDict, SysDictItem
from core.exception.errors import NotFoundError


class DictService:
    """
    字典管理服务类
    """
    
    @staticmethod
    async def get_dict_list(
        db: AsyncSession,
        status: Optional[bool] = None
    ) -> List[SysDict]:
        """
        获取字典列表
        
        Args:
            db: 数据库会话
            status: 状态
            
        Returns:
            字典列表
        """
        query = select(SysDict)
        if status is not None:
            query = query.where(SysDict.status == status)
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_dict(
        db: AsyncSession,
        dict_id: int
    ) -> SysDict:
        """
        获取单个字典
        
        Args:
            db: 数据库会话
            dict_id: 字典ID
            
        Returns:
            字典对象
            
        Raises:
            NotFoundError: 字典不存在
        """
        result = await db.execute(select(SysDict).where(SysDict.id == dict_id))
        dict_obj = result.scalar_one_or_none()
        if not dict_obj:
            raise NotFoundError(f"字典 {dict_id} 不存在")
        return dict_obj
    
    @staticmethod
    async def create_dict(
        db: AsyncSession,
        dict_obj: SysDict
    ) -> SysDict:
        """
        创建字典
        
        Args:
            db: 数据库会话
            dict_obj: 字典对象
            
        Returns:
            创建后的字典对象
        """
        # 检查字典编码是否已存在
        result = await db.execute(select(SysDict).where(SysDict.code == dict_obj.code))
        if result.scalar_one_or_none():
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="字典编码已存在")
        
        db.add(dict_obj)
        await db.commit()
        await db.refresh(dict_obj)
        return dict_obj
    
    @staticmethod
    async def update_dict(
        db: AsyncSession,
        dict_id: int,
        dict_obj: SysDict
    ) -> SysDict:
        """
        更新字典
        
        Args:
            db: 数据库会话
            dict_id: 字典ID
            dict_obj: 字典对象
            
        Returns:
            更新后的字典对象
            
        Raises:
            NotFoundError: 字典不存在
        """
        result = await db.execute(select(SysDict).where(SysDict.id == dict_id))
        existing_dict = result.scalar_one_or_none()
        if not existing_dict:
            raise NotFoundError(f"字典 {dict_id} 不存在")
        
        # 更新字典
        for key, value in dict_obj.__dict__.items():
            if key not in ["id", "created_at", "updated_at"] and hasattr(existing_dict, key):
                setattr(existing_dict, key, value)
        
        await db.commit()
        await db.refresh(existing_dict)
        return existing_dict
    
    @staticmethod
    async def delete_dict(
        db: AsyncSession,
        dict_id: int
    ) -> bool:
        """
        删除字典
        
        Args:
            db: 数据库会话
            dict_id: 字典ID
            
        Returns:
            是否删除成功
            
        Raises:
            NotFoundError: 字典不存在
        """
        result = await db.execute(select(SysDict).where(SysDict.id == dict_id))
        dict_obj = result.scalar_one_or_none()
        if not dict_obj:
            raise NotFoundError(f"字典 {dict_id} 不存在")
        
        await db.delete(dict_obj)
        await db.commit()
        return True
    
    @staticmethod
    async def get_dict_item_list(
        db: AsyncSession,
        dict_id: int
    ) -> List[SysDictItem]:
        """
        获取字典项列表
        
        Args:
            db: 数据库会话
            dict_id: 字典ID
            
        Returns:
            字典项列表
        """
        result = await db.execute(
            select(SysDictItem).where(SysDictItem.dict_id == dict_id)
        )
        return result.scalars().all()
    
    @staticmethod
    async def create_dict_item(
        db: AsyncSession,
        dict_item: SysDictItem
    ) -> SysDictItem:
        """
        创建字典项
        
        Args:
            db: 数据库会话
            dict_item: 字典项对象
            
        Returns:
            创建后的字典项对象
            
        Raises:
            NotFoundError: 字典不存在
        """
        # 检查字典是否存在
        result = await db.execute(select(SysDict).where(SysDict.id == dict_item.dict_id))
        if not result.scalar_one_or_none():
            raise NotFoundError(f"字典 {dict_item.dict_id} 不存在")
        
        db.add(dict_item)
        await db.commit()
        await db.refresh(dict_item)
        return dict_item
    
    @staticmethod
    async def update_dict_item(
        db: AsyncSession,
        item_id: int,
        dict_item: SysDictItem
    ) -> SysDictItem:
        """
        更新字典项
        
        Args:
            db: 数据库会话
            item_id: 字典项ID
            dict_item: 字典项对象
            
        Returns:
            更新后的字典项对象
            
        Raises:
            NotFoundError: 字典项不存在
        """
        result = await db.execute(select(SysDictItem).where(SysDictItem.id == item_id))
        existing_item = result.scalar_one_or_none()
        if not existing_item:
            raise NotFoundError(f"字典项 {item_id} 不存在")
        
        # 更新字典项
        for key, value in dict_item.__dict__.items():
            if key not in ["id", "created_at", "updated_at"] and hasattr(existing_item, key):
                setattr(existing_item, key, value)
        
        await db.commit()
        await db.refresh(existing_item)
        return existing_item
    
    @staticmethod
    async def delete_dict_item(
        db: AsyncSession,
        item_id: int
    ) -> bool:
        """
        删除字典项
        
        Args:
            db: 数据库会话
            item_id: 字典项ID
            
        Returns:
            是否删除成功
            
        Raises:
            NotFoundError: 字典项不存在
        """
        result = await db.execute(select(SysDictItem).where(SysDictItem.id == item_id))
        dict_item = result.scalar_one_or_none()
        if not dict_item:
            raise NotFoundError(f"字典项 {item_id} 不存在")
        
        await db.delete(dict_item)
        await db.commit()
        return True
