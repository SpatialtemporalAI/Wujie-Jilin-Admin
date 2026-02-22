#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional, List, Any
from pydantic import Field, ConfigDict
from datetime import datetime
from app.models.common.base import BaseRespEntity, BaseEntity
from app.models.common.page import PageRequest
from app.models.sys.config import ConfigType, ConfigGroup


class SysConfigQueryParams(PageRequest):
    """
    系统配置查询参数模型
    用于配置列表分页查询时的筛选条件
    """

    key: Optional[str] = Field(None, description="配置键名，支持模糊查询")
    description: Optional[str] = Field(None, description="配置描述，支持模糊查询")
    type: Optional[ConfigType] = Field(None, description="配置类型")
    group: Optional[ConfigGroup] = Field(None, description="配置分组")

    is_system: Optional[bool] = Field(None, description="是否为系统内置配置")


class SysConfigCreate(BaseEntity):
    """
    系统配置创建请求模型
    用于创建新配置时的请求数据
    """

    key: str = Field(..., description="配置键名", max_length=100)
    value: str = Field(..., description="配置值", max_length=255)
    default_value: Optional[str] = Field(None, description="默认值", max_length=255)
    validation_rule: Optional[str] = Field(None, description="校验规则", max_length=255)
    description: Optional[str] = Field(None, description="配置描述", max_length=255)
    type: ConfigType = Field(ConfigType.STRING, description="配置类型")
    group: ConfigGroup = Field(ConfigGroup.SYSTEM, description="配置分组")

    is_system: bool = Field(False, description="是否为系统内置配置")
    required: bool = Field(False, description="是否必填")


class SysConfigUpdate(BaseEntity):
    """
    系统配置更新请求模型
    用于更新配置信息时的请求数据
    """

    value: Optional[str] = Field(None, description="配置值", max_length=255)
    default_value: Optional[str] = Field(None, description="默认值", max_length=255)
    validation_rule: Optional[str] = Field(None, description="校验规则", max_length=255)
    description: Optional[str] = Field(None, description="配置描述", max_length=255)
    type: Optional[ConfigType] = Field(None, description="配置类型")
    group: Optional[ConfigGroup] = Field(None, description="配置分组")

    is_system: Optional[bool] = Field(None, description="是否为系统内置配置")
    required: Optional[bool] = Field(None, description="是否必填")


class SysConfigBatchUpdate(BaseEntity):
    """
    系统配置批量更新请求模型
    用于批量更新多个配置项
    """

    configs: List[dict] = Field(..., description="配置项列表，每项包含id和value")


class SysConfigSimpleResponse(BaseRespEntity):
    """
    系统配置简单响应模型
    用于只需要展示基本配置信息的场景
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="配置ID")
    key: str = Field(..., description="配置键名")
    value: str = Field(..., description="配置值")
    description: Optional[str] = Field(None, description="配置描述")
    type: ConfigType = Field(..., description="配置类型")
    group: ConfigGroup = Field(..., description="配置分组")


class SysConfigResponseData(BaseRespEntity):
    """
    系统配置详细响应模型
    用于展示配置完整信息
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="配置ID")
    key: str = Field(..., description="配置键名")
    value: str = Field(..., description="配置值")
    default_value: Optional[str] = Field(None, description="默认值")
    validation_rule: Optional[str] = Field(None, description="校验规则")
    description: Optional[str] = Field(None, description="配置描述")
    type: ConfigType = Field(..., description="配置类型")
    group: ConfigGroup = Field(..., description="配置分组")

    is_system: bool = Field(..., description="是否为系统内置配置")
    required: bool = Field(..., description="是否必填")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")


class SysConfigReset(BaseEntity):
    """
    系统配置重置请求模型
    用于重置配置为默认值
    """

    ids: List[int] = Field(..., description="要重置的配置ID列表")


class SysConfigByGroupQuery(BaseEntity):
    """
    按分组查询系统配置的请求模型
    """

    group: ConfigGroup = Field(..., description="配置分组")
