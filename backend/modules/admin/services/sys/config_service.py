#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
系统配置服务
处理系统配置相关的业务逻辑
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.models.sys.config import SysConfig, ConfigType, ConfigGroup
from core.exception.errors import NotFoundError


class ConfigService:
    """
    系统配置服务类
    """
    
    @staticmethod
    async def get_config_list(
        db: AsyncSession,
        group: Optional[ConfigGroup] = None
    ) -> List[SysConfig]:
        """
        获取配置列表
        
        Args:
            db: 数据库会话
            group: 配置分组
            
        Returns:
            配置列表
        """
        query = select(SysConfig)
        if group:
            query = query.where(SysConfig.group == group)
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_config(
        db: AsyncSession,
        config_key: str
    ) -> SysConfig:
        """
        获取单个配置
        
        Args:
            db: 数据库会话
            config_key: 配置键名
            
        Returns:
            配置对象
            
        Raises:
            NotFoundError: 配置不存在
        """
        result = await db.execute(select(SysConfig).where(SysConfig.key == config_key))
        config = result.scalar_one_or_none()
        if not config:
            raise NotFoundError(f"配置 {config_key} 不存在")
        return config
    
    @staticmethod
    async def create_config(
        db: AsyncSession,
        config: SysConfig
    ) -> SysConfig:
        """
        创建配置
        
        Args:
            db: 数据库会话
            config: 配置对象
            
        Returns:
            创建后的配置对象
        """
        # 检查配置键是否已存在
        result = await db.execute(select(SysConfig).where(SysConfig.key == config.key))
        if result.scalar_one_or_none():
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="配置键已存在")
        
        db.add(config)
        await db.commit()
        await db.refresh(config)
        return config
    
    @staticmethod
    async def update_config(
        db: AsyncSession,
        config_key: str,
        config: SysConfig
    ) -> SysConfig:
        """
        更新配置
        
        Args:
            db: 数据库会话
            config_key: 配置键名
            config: 配置对象
            
        Returns:
            更新后的配置对象
            
        Raises:
            NotFoundError: 配置不存在
        """
        result = await db.execute(select(SysConfig).where(SysConfig.key == config_key))
        existing_config = result.scalar_one_or_none()
        if not existing_config:
            raise NotFoundError(f"配置 {config_key} 不存在")
        
        # 更新配置
        for key, value in config.__dict__.items():
            if key not in ["id", "created_at", "updated_at"] and hasattr(existing_config, key):
                setattr(existing_config, key, value)
        
        await db.commit()
        await db.refresh(existing_config)
        return existing_config
    
    @staticmethod
    async def delete_config(
        db: AsyncSession,
        config_key: str
    ) -> bool:
        """
        删除配置
        
        Args:
            db: 数据库会话
            config_key: 配置键名
            
        Returns:
            是否删除成功
            
        Raises:
            NotFoundError: 配置不存在
        """
        result = await db.execute(select(SysConfig).where(SysConfig.key == config_key))
        config = result.scalar_one_or_none()
        if not config:
            raise NotFoundError(f"配置 {config_key} 不存在")
        
        await db.delete(config)
        await db.commit()
        return True
