#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
系统配置相关接口
"""
import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from database.db_manager import get_session
from core.response.response_schema import (
    ResponseModel,
    ResponsePageModel,
    ResponsePageDataModel,
    response_base,
)

from modules.admin.services.sys import ConfigService
from modules.admin.schemas.sys.config import (
    SysConfigCreate,
    SysConfigUpdate,
    SysConfigQueryParams,
    SysConfigResponseData,
    SysConfigSimpleResponse,
    SysConfigBatchUpdate,
    SysConfigReset,
    SysConfigByGroupQuery,
)
from app.models.sys.config import ConfigType, ConfigGroup

# 获取logger
logger = logging.getLogger(__name__)

# 创建配置管理路由
config_router = APIRouter(prefix="/config", tags=["系统配置"])


@config_router.get("/list", response_model=ResponsePageModel[SysConfigResponseData])
async def get_config_list(
    key: Optional[str] = Query(None, description="配置键名，支持模糊查询"),
    description: Optional[str] = Query(None, description="配置描述，支持模糊查询"),
    type: Optional[ConfigType] = Query(None, description="配置类型"),
    group: Optional[ConfigGroup] = Query(None, description="配置分组"),
    editable: Optional[bool] = Query(None, description="是否可编辑"),
    is_system: Optional[bool] = Query(None, description="是否为系统内置配置"),
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(10, ge=1, le=200, description="每页条数，最大200"),
    db: AsyncSession = Depends(get_session),
):
    """
    获取配置列表（分页）
    """
    try:
        logger.info("获取配置列表接口被调用")

        # 构建查询参数
        query_params = SysConfigQueryParams(
            key=key,
            description=description,
            type=type,
            group=group,
            editable=editable,
            is_system=is_system,
            page=page,
            page_size=page_size,
        )

        # 调用服务层
        configs, total = await ConfigService.get_config_list(db, query_params)

        # 转换为响应模型
        records = [SysConfigResponseData.model_validate(c) for c in configs]
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        page_data = ResponsePageDataModel(
            records=records,
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        )

        logger.info("获取配置列表接口成功，共 %d 条记录", total)
        return response_base.page(data=page_data)

    except Exception as e:
        logger.error("获取配置列表接口失败: %s", str(e), exc_info=True)
        raise


@config_router.get("/all", response_model=ResponseModel[List[SysConfigSimpleResponse]])
async def get_all_configs(
    group: Optional[ConfigGroup] = Query(None, description="配置分组"),
    editable_only: bool = Query(False, description="是否只查询可编辑的配置"),
    db: AsyncSession = Depends(get_session),
):
    """
    获取所有配置（不分页）
    """
    try:
        logger.info("获取所有配置接口被调用")

        # 构建查询参数
        query_params = SysConfigQueryParams(
            group=group,
            editable=editable_only if editable_only else None,
            page=1,
            page_size=1000,
        )

        # 调用服务层
        configs, _ = await ConfigService.get_config_list(db, query_params)

        # 转换为响应模型
        records = [SysConfigSimpleResponse.model_validate(c) for c in configs]

        logger.info("获取所有配置接口成功，共 %d 条记录", len(records))
        return response_base.success(data=records)

    except Exception as e:
        logger.error("获取所有配置接口失败: %s", str(e), exc_info=True)
        raise


@config_router.get("/group/{group}", response_model=ResponseModel[List[SysConfigSimpleResponse]])
async def get_configs_by_group(
    group: ConfigGroup,
    editable_only: bool = Query(False, description="是否只查询可编辑的配置"),
    db: AsyncSession = Depends(get_session),
):
    """
    按分组获取配置列表
    """
    try:
        logger.info("按分组获取配置接口被调用，分组: %s", group)

        # 构建查询参数
        query = SysConfigByGroupQuery(
            group=group,
            editable_only=editable_only,
        )

        # 调用服务层
        configs = await ConfigService.get_configs_by_group(db, query)

        # 转换为响应模型
        records = [SysConfigSimpleResponse.model_validate(c) for c in configs]

        logger.info("按分组获取配置接口成功，共 %d 条记录", len(records))
        return response_base.success(data=records)

    except Exception as e:
        logger.error("按分组获取配置接口失败: %s", str(e), exc_info=True)
        raise


@config_router.get("/id/{config_id}", response_model=ResponseModel[SysConfigResponseData])
async def get_config_by_id(
    config_id: int,
    db: AsyncSession = Depends(get_session),
):
    """
    通过ID获取单个配置
    """
    try:
        logger.info("获取配置详情接口被调用，配置ID: %d", config_id)

        config = await ConfigService.get_config_by_id(db, config_id)
        response_data = SysConfigResponseData.model_validate(config)

        logger.info("获取配置详情接口成功，配置ID: %d", config_id)
        return response_base.success(data=response_data)

    except Exception as e:
        logger.error("获取配置详情接口失败: %s", str(e), exc_info=True)
        raise


@config_router.get("/key/{config_key}", response_model=ResponseModel[SysConfigResponseData])
async def get_config_by_key(
    config_key: str,
    db: AsyncSession = Depends(get_session),
):
    """
    通过键名获取单个配置
    """
    try:
        logger.info("获取配置详情接口被调用，配置键名: %s", config_key)

        config = await ConfigService.get_config_by_key(db, config_key)
        response_data = SysConfigResponseData.model_validate(config)

        logger.info("获取配置详情接口成功，配置键名: %s", config_key)
        return response_base.success(data=response_data)

    except Exception as e:
        logger.error("获取配置详情接口失败: %s", str(e), exc_info=True)
        raise


@config_router.get("/value/{config_key}", response_model=ResponseModel)
async def get_config_value(
    config_key: str,
    default: Optional[str] = Query(None, description="默认值"),
    db: AsyncSession = Depends(get_session),
):
    """
    获取配置值（已根据类型转换）
    """
    try:
        logger.info("获取配置值接口被调用，配置键名: %s", config_key)

        value = await ConfigService.get_config_value(db, config_key, default)

        logger.info("获取配置值接口成功，配置键名: %s", config_key)
        return response_base.success(data=value)

    except Exception as e:
        logger.error("获取配置值接口失败: %s", str(e), exc_info=True)
        raise


@config_router.post("", response_model=ResponseModel[SysConfigResponseData])
@config_router.post("/add", response_model=ResponseModel[SysConfigResponseData])
async def create_config(
    config_in: SysConfigCreate,
    db: AsyncSession = Depends(get_session),
):
    """
    创建配置
    """
    try:
        logger.info("创建配置接口被调用")

        config = await ConfigService.create_config(db, config_in)
        response_data = SysConfigResponseData.model_validate(config)

        logger.info("创建配置接口成功，配置ID: %d", config.id)
        return response_base.success(data=response_data, msg="创建成功")

    except Exception as e:
        logger.error("创建配置接口失败: %s", str(e), exc_info=True)
        raise


@config_router.put("/{config_id}", response_model=ResponseModel[SysConfigResponseData])
async def update_config(
    config_id: int,
    config_in: SysConfigUpdate,
    db: AsyncSession = Depends(get_session),
):
    """
    更新配置
    """
    try:
        logger.info("更新配置接口被调用，配置ID: %d", config_id)

        config = await ConfigService.update_config(db, config_id, config_in)
        response_data = SysConfigResponseData.model_validate(config)

        logger.info("更新配置接口成功，配置ID: %d", config_id)
        return response_base.success(data=response_data, msg="更新成功")

    except Exception as e:
        logger.error("更新配置接口失败: %s", str(e), exc_info=True)
        raise


@config_router.put("/batch/update", response_model=ResponseModel)
async def batch_update_configs(
    batch_in: SysConfigBatchUpdate,
    db: AsyncSession = Depends(get_session),
):
    """
    批量更新配置
    """
    try:
        logger.info("批量更新配置接口被调用")

        updated_count = await ConfigService.batch_update_configs(db, batch_in)

        logger.info("批量更新配置接口成功，更新数量: %d", updated_count)
        return response_base.success(msg=f"成功更新 {updated_count} 条记录")

    except Exception as e:
        logger.error("批量更新配置接口失败: %s", str(e), exc_info=True)
        raise


@config_router.put("/batch/reset", response_model=ResponseModel)
async def reset_configs(
    reset_in: SysConfigReset,
    db: AsyncSession = Depends(get_session),
):
    """
    批量重置配置为默认值
    """
    try:
        logger.info("重置配置接口被调用")

        reset_count = await ConfigService.reset_configs(db, reset_in)

        logger.info("重置配置接口成功，重置数量: %d", reset_count)
        return response_base.success(msg=f"成功重置 {reset_count} 条记录")

    except Exception as e:
        logger.error("重置配置接口失败: %s", str(e), exc_info=True)
        raise


@config_router.delete("/{config_id}", response_model=ResponseModel)
async def delete_config(
    config_id: int,
    db: AsyncSession = Depends(get_session),
):
    """
    删除配置
    """
    try:
        logger.info("删除配置接口被调用，配置ID: %d", config_id)

        await ConfigService.delete_config(db, config_id)

        logger.info("删除配置接口成功，配置ID: %d", config_id)
        return response_base.success(msg="删除成功")

    except Exception as e:
        logger.error("删除配置接口失败: %s", str(e), exc_info=True)
        raise

