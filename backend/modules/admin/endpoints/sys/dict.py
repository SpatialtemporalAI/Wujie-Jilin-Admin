#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
字典管理相关接口
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

from modules.admin.services.sys import DictService
from modules.admin.schemas.sys.dict import (
    SysDictCreate,
    SysDictUpdate,
    SysDictQueryParams,
    SysDictResponseData,
    SysDictSimpleResponse,
    SysDictWithItemsResponse,
    SysDictItemCreate,
    SysDictItemUpdate,
    SysDictItemQueryParams,
    SysDictItemResponseData,
    SysDictItemSimpleResponse,
    SysDictBatchUpdateStatus,
    SysDictItemBatchUpdateStatus,
)

# 获取logger
logger = logging.getLogger(__name__)

# 创建字典管理路由
dict_router = APIRouter(prefix="/dict", tags=["字典管理"])


# ==================== 字典分类管理 ====================

@dict_router.get("/list", response_model=ResponsePageModel[SysDictResponseData])
async def get_dict_list(
    name: Optional[str] = Query(None, description="字典名称，支持模糊查询"),
    code: Optional[str] = Query(None, description="字典编码，支持模糊查询"),
    status: Optional[bool] = Query(None, description="字典状态：True-启用，False-禁用"),
    is_system: Optional[bool] = Query(None, description="是否为系统内置字典"),
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(10, ge=1, le=200, description="每页条数，最大200"),
    db: AsyncSession = Depends(get_session),
):
    """
    获取字典列表（分页）
    """
    try:
        logger.info("获取字典列表接口被调用")

        # 构建查询参数
        query_params = SysDictQueryParams(
            name=name,
            code=code,
            status=status,
            is_system=is_system,
            page=page,
            page_size=page_size,
        )

        # 调用服务层
        dicts, total = await DictService.get_dict_list(db, query_params)

        # 转换为响应模型
        records = [SysDictResponseData.model_validate(d) for d in dicts]
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        page_data = ResponsePageDataModel(
            records=records,
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        )

        logger.info("获取字典列表接口成功，共 %d 条记录", total)
        return response_base.page(data=page_data)

    except Exception as e:
        logger.error("获取字典列表接口失败: %s", str(e), exc_info=True)
        raise


@dict_router.get("/all", response_model=ResponseModel[List[SysDictSimpleResponse]])
async def get_all_dicts(
    status: Optional[bool] = Query(None, description="字典状态：True-启用，False-禁用"),
    db: AsyncSession = Depends(get_session),
):
    """
    获取所有字典（不分页）
    """
    try:
        logger.info("获取所有字典接口被调用")

        # 构建查询参数
        query_params = SysDictQueryParams(
            status=status,
            page=1,
            page_size=1000,
        )

        # 调用服务层
        dicts, _ = await DictService.get_dict_list(db, query_params)

        # 转换为响应模型
        records = [SysDictSimpleResponse.model_validate(d) for d in dicts]

        logger.info("获取所有字典接口成功，共 %d 条记录", len(records))
        return response_base.success(data=records)

    except Exception as e:
        logger.error("获取所有字典接口失败: %s", str(e), exc_info=True)
        raise


@dict_router.get("/code/{code}", response_model=ResponseModel[SysDictWithItemsResponse])
async def get_dict_by_code(
    code: str,
    db: AsyncSession = Depends(get_session),
):
    """
    通过编码获取字典及其字典项
    """
    try:
        logger.info("通过编码获取字典接口被调用，编码: %s", code)

        # 先获取字典
        dict_obj = await DictService.get_dict_by_code(db, code)

        # 再获取带字典项的完整信息
        dict_with_items = await DictService.get_dict_with_items(db, dict_obj.id)

        # 转换为响应模型
        response_data = SysDictWithItemsResponse(
            id=dict_with_items.id,
            name=dict_with_items.name,
            code=dict_with_items.code,
            description=dict_with_items.description,
            status=dict_with_items.status,
            is_system=dict_with_items.is_system,
            sort=dict_with_items.sort,
            created_at=dict_with_items.created_at,
            updated_at=dict_with_items.updated_at,
            items=[SysDictItemSimpleResponse.model_validate(item) for item in dict_with_items.dict_items],
        )

        logger.info("通过编码获取字典接口成功，编码: %s", code)
        return response_base.success(data=response_data)

    except Exception as e:
        logger.error("通过编码获取字典接口失败: %s", str(e), exc_info=True)
        raise


@dict_router.get("/{dict_id}", response_model=ResponseModel[SysDictResponseData])
async def get_dict(
    dict_id: int,
    db: AsyncSession = Depends(get_session),
):
    """
    获取单个字典
    """
    try:
        logger.info("获取字典详情接口被调用，字典ID: %d", dict_id)

        dict_obj = await DictService.get_dict(db, dict_id)
        response_data = SysDictResponseData.model_validate(dict_obj)

        logger.info("获取字典详情接口成功，字典ID: %d", dict_id)
        return response_base.success(data=response_data)

    except Exception as e:
        logger.error("获取字典详情接口失败: %s", str(e), exc_info=True)
        raise


@dict_router.get("/{dict_id}/with-items", response_model=ResponseModel[SysDictWithItemsResponse])
async def get_dict_with_items(
    dict_id: int,
    db: AsyncSession = Depends(get_session),
):
    """
    获取字典及其所有字典项
    """
    try:
        logger.info("获取字典及其字典项接口被调用，字典ID: %d", dict_id)

        dict_with_items = await DictService.get_dict_with_items(db, dict_id)

        # 转换为响应模型
        response_data = SysDictWithItemsResponse(
            id=dict_with_items.id,
            name=dict_with_items.name,
            code=dict_with_items.code,
            description=dict_with_items.description,
            status=dict_with_items.status,
            is_system=dict_with_items.is_system,
            sort=dict_with_items.sort,
            created_at=dict_with_items.created_at,
            updated_at=dict_with_items.updated_at,
            items=[SysDictItemSimpleResponse.model_validate(item) for item in dict_with_items.dict_items],
        )

        logger.info("获取字典及其字典项接口成功，字典ID: %d", dict_id)
        return response_base.success(data=response_data)

    except Exception as e:
        logger.error("获取字典及其字典项接口失败: %s", str(e), exc_info=True)
        raise


@dict_router.post("", response_model=ResponseModel[SysDictResponseData])
@dict_router.post("/add", response_model=ResponseModel[SysDictResponseData])
async def create_dict(
    dict_in: SysDictCreate,
    db: AsyncSession = Depends(get_session),
):
    """
    创建字典
    """
    try:
        logger.info("创建字典接口被调用")

        dict_obj = await DictService.create_dict(db, dict_in)
        response_data = SysDictResponseData.model_validate(dict_obj)

        logger.info("创建字典接口成功，字典ID: %d", dict_obj.id)
        return response_base.success(data=response_data, msg="创建成功")

    except Exception as e:
        logger.error("创建字典接口失败: %s", str(e), exc_info=True)
        raise


@dict_router.put("/{dict_id}", response_model=ResponseModel[SysDictResponseData])
async def update_dict(
    dict_id: int,
    dict_in: SysDictUpdate,
    db: AsyncSession = Depends(get_session),
):
    """
    更新字典
    """
    try:
        logger.info("更新字典接口被调用，字典ID: %d", dict_id)

        dict_obj = await DictService.update_dict(db, dict_id, dict_in)
        response_data = SysDictResponseData.model_validate(dict_obj)

        logger.info("更新字典接口成功，字典ID: %d", dict_id)
        return response_base.success(data=response_data, msg="更新成功")

    except Exception as e:
        logger.error("更新字典接口失败: %s", str(e), exc_info=True)
        raise


@dict_router.put("/batch/status", response_model=ResponseModel)
async def batch_update_dict_status(
    batch_in: SysDictBatchUpdateStatus,
    db: AsyncSession = Depends(get_session),
):
    """
    批量更新字典状态
    """
    try:
        logger.info("批量更新字典状态接口被调用")

        updated_count = await DictService.batch_update_dict_status(db, batch_in)

        logger.info("批量更新字典状态接口成功，更新数量: %d", updated_count)
        return response_base.success(msg=f"成功更新 {updated_count} 条记录")

    except Exception as e:
        logger.error("批量更新字典状态接口失败: %s", str(e), exc_info=True)
        raise


@dict_router.delete("/{dict_id}", response_model=ResponseModel)
async def delete_dict(
    dict_id: int,
    db: AsyncSession = Depends(get_session),
):
    """
    删除字典
    """
    try:
        logger.info("删除字典接口被调用，字典ID: %d", dict_id)

        await DictService.delete_dict(db, dict_id)

        logger.info("删除字典接口成功，字典ID: %d", dict_id)
        return response_base.success(msg="删除成功")

    except Exception as e:
        logger.error("删除字典接口失败: %s", str(e), exc_info=True)
        raise


# ==================== 字典项管理 ====================


@dict_router.get("/item/list", response_model=ResponsePageModel[SysDictItemResponseData])
async def get_dict_item_list(
    dict_id: Optional[int] = Query(None, description="字典ID"),
    label: Optional[str] = Query(None, description="字典项文本，支持模糊查询"),
    value: Optional[str] = Query(None, description="字典项值，支持模糊查询"),
    status: Optional[bool] = Query(None, description="字典项状态：True-启用，False-禁用"),
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(10, ge=1, le=200, description="每页条数，最大200"),
    db: AsyncSession = Depends(get_session),
):
    """
    获取字典项列表（分页）
    """
    try:
        logger.info("获取字典项列表接口被调用")

        # 构建查询参数
        query_params = SysDictItemQueryParams(
            dict_id=dict_id,
            label=label,
            value=value,
            status=status,
            page=page,
            page_size=page_size,
        )

        # 调用服务层
        dict_items, total = await DictService.get_dict_item_list(db, query_params)

        # 转换为响应模型
        records = [SysDictItemResponseData.model_validate(item) for item in dict_items]
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        page_data = ResponsePageDataModel(
            records=records,
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        )

        logger.info("获取字典项列表接口成功，共 %d 条记录", total)
        return response_base.page(data=page_data)

    except Exception as e:
        logger.error("获取字典项列表接口失败: %s", str(e), exc_info=True)
        raise


@dict_router.get("/item/all/{dict_code}", response_model=ResponseModel[List[SysDictItemSimpleResponse]])
async def get_dict_items_by_dict_code(
    dict_code: str,
    db: AsyncSession = Depends(get_session),
):
    """
    通过字典编码获取字典项列表（只返回启用的）
    """
    try:
        logger.info("通过字典编码获取字典项接口被调用，编码: %s", dict_code)

        dict_items = await DictService.get_dict_items_by_dict_code(db, dict_code)

        # 转换为响应模型
        records = [SysDictItemSimpleResponse.model_validate(item) for item in dict_items]

        logger.info("通过字典编码获取字典项接口成功，编码: %s，数量: %d", dict_code, len(records))
        return response_base.success(data=records)

    except Exception as e:
        logger.error("通过字典编码获取字典项接口失败: %s", str(e), exc_info=True)
        raise


@dict_router.get("/item/{item_id}", response_model=ResponseModel[SysDictItemResponseData])
async def get_dict_item(
    item_id: int,
    db: AsyncSession = Depends(get_session),
):
    """
    获取单个字典项
    """
    try:
        logger.info("获取字典项详情接口被调用，字典项ID: %d", item_id)

        dict_item = await DictService.get_dict_item(db, item_id)
        response_data = SysDictItemResponseData.model_validate(dict_item)

        logger.info("获取字典项详情接口成功，字典项ID: %d", item_id)
        return response_base.success(data=response_data)

    except Exception as e:
        logger.error("获取字典项详情接口失败: %s", str(e), exc_info=True)
        raise


@dict_router.post("/item", response_model=ResponseModel[SysDictItemResponseData])
@dict_router.post("/item/add", response_model=ResponseModel[SysDictItemResponseData])
async def create_dict_item(
    item_in: SysDictItemCreate,
    db: AsyncSession = Depends(get_session),
):
    """
    创建字典项
    """
    try:
        logger.info("创建字典项接口被调用")

        dict_item = await DictService.create_dict_item(db, item_in)
        response_data = SysDictItemResponseData.model_validate(dict_item)

        logger.info("创建字典项接口成功，字典项ID: %d", dict_item.id)
        return response_base.success(data=response_data, msg="创建成功")

    except Exception as e:
        logger.error("创建字典项接口失败: %s", str(e), exc_info=True)
        raise


@dict_router.put("/item/{item_id}", response_model=ResponseModel[SysDictItemResponseData])
async def update_dict_item(
    item_id: int,
    item_in: SysDictItemUpdate,
    db: AsyncSession = Depends(get_session),
):
    """
    更新字典项
    """
    try:
        logger.info("更新字典项接口被调用，字典项ID: %d", item_id)

        dict_item = await DictService.update_dict_item(db, item_id, item_in)
        response_data = SysDictItemResponseData.model_validate(dict_item)

        logger.info("更新字典项接口成功，字典项ID: %d", item_id)
        return response_base.success(data=response_data, msg="更新成功")

    except Exception as e:
        logger.error("更新字典项接口失败: %s", str(e), exc_info=True)
        raise


@dict_router.put("/item/batch/status", response_model=ResponseModel)
async def batch_update_dict_item_status(
    batch_in: SysDictItemBatchUpdateStatus,
    db: AsyncSession = Depends(get_session),
):
    """
    批量更新字典项状态
    """
    try:
        logger.info("批量更新字典项状态接口被调用")

        updated_count = await DictService.batch_update_dict_item_status(db, batch_in)

        logger.info("批量更新字典项状态接口成功，更新数量: %d", updated_count)
        return response_base.success(msg=f"成功更新 {updated_count} 条记录")

    except Exception as e:
        logger.error("批量更新字典项状态接口失败: %s", str(e), exc_info=True)
        raise


@dict_router.delete("/item/{item_id}", response_model=ResponseModel)
async def delete_dict_item(
    item_id: int,
    db: AsyncSession = Depends(get_session),
):
    """
    删除字典项
    """
    try:
        logger.info("删除字典项接口被调用，字典项ID: %d", item_id)

        await DictService.delete_dict_item(db, item_id)

        logger.info("删除字典项接口成功，字典项ID: %d", item_id)
        return response_base.success(msg="删除成功")

    except Exception as e:
        logger.error("删除字典项接口失败: %s", str(e), exc_info=True)
        raise

