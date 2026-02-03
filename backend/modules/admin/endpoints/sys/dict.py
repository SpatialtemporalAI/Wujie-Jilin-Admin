#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
字典管理相关接口
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from database.db_manager import get_session
from core.response.response_schema import ResponseModel

from app.models.sys.dict import SysDict, SysDictItem
from modules.admin.services.sys import DictService

# 创建字典管理路由
dict_router = APIRouter(prefix="/dict", tags=["字典管理"])


@dict_router.get("/list", response_model=ResponseModel[List[SysDict]])
async def get_dict_list(
    status: Optional[bool] = Query(None, description="状态"),
    db: AsyncSession = Depends(get_session),
):
    """
    获取字典列表
    """
    dicts = await DictService.get_dict_list(db, status)
    return ResponseModel(data=dicts)


@dict_router.get("/{dict_id}", response_model=ResponseModel[SysDict])
async def get_dict(dict_id: int, db: AsyncSession = Depends(get_session)):
    """
    获取单个字典
    """
    dict_obj = await DictService.get_dict(db, dict_id)
    return ResponseModel(data=dict_obj)


@dict_router.post("", response_model=ResponseModel[SysDict])
async def create_dict(dict_obj: SysDict, db: AsyncSession = Depends(get_session)):
    """
    创建字典
    """
    dict_obj = await DictService.create_dict(db, dict_obj)
    return ResponseModel(data=dict_obj)


@dict_router.put("/{dict_id}", response_model=ResponseModel[SysDict])
async def update_dict(
    dict_id: int, dict_obj: SysDict, db: AsyncSession = Depends(get_session)
):
    """
    更新字典
    """
    dict_obj = await DictService.update_dict(db, dict_id, dict_obj)
    return ResponseModel(data=dict_obj)


@dict_router.delete("/{dict_id}", response_model=ResponseModel)
async def delete_dict(dict_id: int, db: AsyncSession = Depends(get_session)):
    """
    删除字典
    """
    await DictService.delete_dict(db, dict_id)
    return ResponseModel(msg="删除成功")


# ==================== 字典�?====================


@dict_router.get("/item/list", response_model=ResponseModel[List[SysDictItem]])
async def get_dict_item_list(
    dict_id: int = Query(..., description="字典ID"),
    db: AsyncSession = Depends(get_session),
):
    """
    获取字典项列�?"""
    dict_items = await DictService.get_dict_item_list(db, dict_id)
    return ResponseModel(data=dict_items)


@dict_router.post("/item", response_model=ResponseModel[SysDictItem])
async def create_dict_item(
    dict_item: SysDictItem, db: AsyncSession = Depends(get_session)
):
    """
    创建字典�?"""
    dict_item = await DictService.create_dict_item(db, dict_item)
    return ResponseModel(data=dict_item)


@dict_router.put("/item/{item_id}", response_model=ResponseModel[SysDictItem])
async def update_dict_item(
    item_id: int, dict_item: SysDictItem, db: AsyncSession = Depends(get_session)
):
    """
    更新字典�?"""
    dict_item = await DictService.update_dict_item(db, item_id, dict_item)
    return ResponseModel(data=dict_item)


@dict_router.delete("/item/{item_id}", response_model=ResponseModel)
async def delete_dict_item(item_id: int, db: AsyncSession = Depends(get_session)):
    """
    删除字典�?"""
    await DictService.delete_dict_item(db, item_id)
    return ResponseModel(msg="删除成功")
