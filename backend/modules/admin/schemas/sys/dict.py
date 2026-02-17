#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional, List
from pydantic import Field, ConfigDict
from datetime import datetime
from app.models.common.base import BaseRespEntity, BaseEntity
from app.models.common.page import PageRequest


class SysDictQueryParams(PageRequest):
    """
    系统字典查询参数模型
    用于字典列表分页查询时的筛选条件
    """

    name: Optional[str] = Field(None, description="字典名称，支持模糊查询")
    code: Optional[str] = Field(None, description="字典编码，支持模糊查询")
    status: Optional[bool] = Field(None, description="字典状态：True-启用，False-禁用")
    is_system: Optional[bool] = Field(None, description="是否为系统内置字典")


class SysDictCreate(BaseEntity):
    """
    系统字典创建请求模型
    用于创建新字典时的请求数据
    """

    name: str = Field(..., description="字典名称", max_length=100)
    code: str = Field(..., description="字典编码", max_length=100)
    description: Optional[str] = Field(None, description="字典描述")
    status: bool = Field(True, description="字典状态：True-启用，False-禁用")
    sort: int = Field(0, description="排序号")


class SysDictUpdate(BaseEntity):
    """
    系统字典更新请求模型
    用于更新字典信息时的请求数据
    """

    name: Optional[str] = Field(None, description="字典名称", max_length=100)
    description: Optional[str] = Field(None, description="字典描述")
    status: Optional[bool] = Field(None, description="字典状态：True-启用，False-禁用")
    sort: Optional[int] = Field(None, description="排序号")


class SysDictSimpleResponse(BaseRespEntity):
    """
    系统字典简单响应模型
    用于只需要展示基本字典信息的场景
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="字典ID")
    name: str = Field(..., description="字典名称")
    code: str = Field(..., description="字典编码")
    status: bool = Field(..., description="字典状态")


class SysDictResponseData(BaseRespEntity):
    """
    系统字典详细响应模型
    用于展示字典完整信息，包括关联的字典项
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="字典ID")
    name: str = Field(..., description="字典名称")
    code: str = Field(..., description="字典编码")
    description: Optional[str] = Field(None, description="字典描述")
    status: bool = Field(..., description="字典状态")
    is_system: bool = Field(..., description="是否为系统内置字典")
    sort: int = Field(..., description="排序号")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")


class SysDictItemQueryParams(PageRequest):
    """
    系统字典项查询参数模型
    用于字典项列表分页查询时的筛选条件
    """

    dict_id: Optional[int] = Field(None, description="字典ID")
    label: Optional[str] = Field(None, description="字典项文本，支持模糊查询")
    value: Optional[str] = Field(None, description="字典项值，支持模糊查询")
    status: Optional[bool] = Field(None, description="字典项状态：True-启用，False-禁用")


class SysDictItemCreate(BaseEntity):
    """
    系统字典项创建请求模型
    用于创建新字典项时的请求数据
    """

    dict_id: int = Field(..., description="关联字典ID")
    value: str = Field(..., description="字典项值", max_length=100)
    label: str = Field(..., description="字典项文本", max_length=100)
    description: Optional[str] = Field(None, description="字典项描述")
    ext_info: Optional[str] = Field(None, description="扩展信息(JSON格式)")
    status: bool = Field(True, description="字典项状态：True-启用，False-禁用")
    sort: int = Field(0, description="排序号")


class SysDictItemUpdate(BaseEntity):
    """
    系统字典项更新请求模型
    用于更新字典项信息时的请求数据
    """

    value: Optional[str] = Field(None, description="字典项值", max_length=100)
    label: Optional[str] = Field(None, description="字典项文本", max_length=100)
    description: Optional[str] = Field(None, description="字典项描述")
    ext_info: Optional[str] = Field(None, description="扩展信息(JSON格式)")
    status: Optional[bool] = Field(None, description="字典项状态：True-启用，False-禁用")
    sort: Optional[int] = Field(None, description="排序号")


class SysDictItemSimpleResponse(BaseRespEntity):
    """
    系统字典项简单响应模型
    用于只需要展示基本字典项信息的场景
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="字典项ID")
    dict_id: int = Field(..., description="关联字典ID")
    value: str = Field(..., description="字典项值")
    label: str = Field(..., description="字典项文本")
    status: bool = Field(..., description="字典项状态")


class SysDictItemResponseData(BaseRespEntity):
    """
    系统字典项详细响应模型
    用于展示字典项完整信息
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="字典项ID")
    dict_id: int = Field(..., description="关联字典ID")
    value: str = Field(..., description="字典项值")
    label: str = Field(..., description="字典项文本")
    description: Optional[str] = Field(None, description="字典项描述")
    ext_info: Optional[str] = Field(None, description="扩展信息(JSON格式)")
    status: bool = Field(..., description="字典项状态")
    sort: int = Field(..., description="排序号")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")


class SysDictWithItemsResponse(BaseRespEntity):
    """
    系统字典带字典项的响应模型
    用于展示字典及其所有字典项
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="字典ID")
    name: str = Field(..., description="字典名称")
    code: str = Field(..., description="字典编码")
    description: Optional[str] = Field(None, description="字典描述")
    status: bool = Field(..., description="字典状态")
    is_system: bool = Field(..., description="是否为系统内置字典")
    sort: int = Field(..., description="排序号")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    items: List[SysDictItemSimpleResponse] = Field([], description="字典项列表")


class SysDictBatchUpdateStatus(BaseEntity):
    """
    系统字典批量更新状态请求模型
    用于批量启用或禁用字典
    """

    dict_ids: List[int] = Field(..., description="字典ID列表")
    status: bool = Field(..., description="要设置的状态：True-启用，False-禁用")


class SysDictItemBatchUpdateStatus(BaseEntity):
    """
    系统字典项批量更新状态请求模型
    用于批量启用或禁用字典项
    """

    item_ids: List[int] = Field(..., description="字典项ID列表")
    status: bool = Field(..., description="要设置的状态：True-启用，False-禁用")
