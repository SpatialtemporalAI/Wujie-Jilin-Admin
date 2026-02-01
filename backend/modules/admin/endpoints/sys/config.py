#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
系统配置相关接口
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from core.database.asyncio.database_manager import get_async_db
from core.response.response_schema import BaseResponse

from app.models.sys.config import SysConfig, ConfigType, ConfigGroup
from modules.admin.services.sys import ConfigService

# 创建配置管理路由器
config_router = APIRouter(
    prefix="/config",
    tags=["系统配置"]
)

@config_router.get("/list", response_model=BaseResponse[List[SysConfig]])
async def get_config_list(
    group: Optional[ConfigGroup] = Query(None, description="配置分组"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    获取配置列表
    """
    configs = await ConfigService.get_config_list(db, group)
    return BaseResponse(data=configs)

@config_router.get("/{config_key}", response_model=BaseResponse[SysConfig])
async def get_config(
    config_key: str,
    db: AsyncSession = Depends(get_async_db)
):
    """
    获取单个配置
    """
    config = await ConfigService.get_config(db, config_key)
    return BaseResponse(data=config)

@config_router.post("", response_model=BaseResponse[SysConfig])
async def create_config(
    config: SysConfig,
    db: AsyncSession = Depends(get_async_db)
):
    """
    创建配置
    """
    config = await ConfigService.create_config(db, config)
    return BaseResponse(data=config)

@config_router.put("/{config_key}", response_model=BaseResponse[SysConfig])
async def update_config(
    config_key: str,
    config: SysConfig,
    db: AsyncSession = Depends(get_async_db)
):
    """
    更新配置
    """
    config = await ConfigService.update_config(db, config_key, config)
    return BaseResponse(data=config)

@config_router.delete("/{config_key}", response_model=BaseResponse)
async def delete_config(
    config_key: str,
    db: AsyncSession = Depends(get_async_db)
):
    """
    删除配置
    """
    await ConfigService.delete_config(db, config_key)
    return BaseResponse(msg="删除成功")
