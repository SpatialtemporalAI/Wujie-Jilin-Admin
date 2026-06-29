#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import List, Optional

from pydantic import ConfigDict, Field

from app.models.common.base import BaseEntity, BaseRespEntity, BoolField
from app.models.common.page import PageRequest


class MerchantQueryParams(PageRequest):
    """商户列表查询参数"""

    name: Optional[str] = Field(None, description="商户名称，支持模糊查询")
    code: Optional[str] = Field(None, description="商户编码，支持模糊查询")
    status: BoolField = Field(None, description="状态：True-启用，False-禁用")


class MerchantCreate(BaseEntity):
    """创建商户请求"""

    name: str = Field(..., description="商户名称", max_length=100)
    code: str = Field(..., description="商户编码", max_length=50)
    contact_name: Optional[str] = Field(None, description="联系人", max_length=100)
    contact_phone: Optional[str] = Field(None, description="联系电话", max_length=20)
    contact_email: Optional[str] = Field(None, description="联系邮箱", max_length=100)
    status: bool = Field(True, description="状态：True-启用，False-禁用")
    remark: Optional[str] = Field(None, description="备注", max_length=255)
    robot_ids: List[int] = Field([], description="绑定的机器人ID列表")


class MerchantUpdate(BaseEntity):
    """更新商户请求（不允许直接改 api_key/api_secret，走重置接口）"""

    name: Optional[str] = Field(None, description="商户名称", max_length=100)
    code: Optional[str] = Field(None, description="商户编码", max_length=50)
    contact_name: Optional[str] = Field(None, description="联系人", max_length=100)
    contact_phone: Optional[str] = Field(None, description="联系电话", max_length=20)
    contact_email: Optional[str] = Field(None, description="联系邮箱", max_length=100)
    status: BoolField = Field(None, description="状态：True-启用，False-禁用")
    remark: Optional[str] = Field(None, description="备注", max_length=255)
    robot_ids: Optional[List[int]] = Field(None, description="绑定的机器人ID列表")


class MerchantRobotBind(BaseEntity):
    """商户绑定机器人请求"""

    robot_ids: List[int] = Field(..., description="机器人ID列表（全量替换）")


class MerchantStatusUpdate(BaseEntity):
    """商户状态切换请求"""

    status: bool = Field(..., description="状态：True-启用，False-禁用")


class MerchantListResponse(BaseRespEntity):
    """商户列表响应"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="商户ID")
    name: str = Field(..., description="商户名称")
    code: str = Field(..., description="商户编码")
    contact_name: Optional[str] = Field(None, description="联系人")
    contact_phone: Optional[str] = Field(None, description="联系电话")
    contact_email: Optional[str] = Field(None, description="联系邮箱")
    api_key: str = Field(..., description="API Key")
    status: bool = Field(..., description="状态")
    remark: Optional[str] = Field(None, description="备注")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")


class MerchantDetailResponse(BaseRespEntity):
    """商户详情响应（含绑定的机器人ID，用于编辑回显）"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="商户ID")
    name: str = Field(..., description="商户名称")
    code: str = Field(..., description="商户编码")
    contact_name: Optional[str] = Field(None, description="联系人")
    contact_phone: Optional[str] = Field(None, description="联系电话")
    contact_email: Optional[str] = Field(None, description="联系邮箱")
    api_key: str = Field(..., description="API Key")
    status: bool = Field(..., description="状态")
    remark: Optional[str] = Field(None, description="备注")
    robot_ids: List[int] = Field([], description="绑定的机器人ID列表")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")


class MerchantCreateResponse(BaseRespEntity):
    """创建商户响应（api_secret 明文仅此处返回一次）"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="商户ID")
    name: str = Field(..., description="商户名称")
    code: str = Field(..., description="商户编码")
    api_key: str = Field(..., description="API Key")
    api_secret: str = Field("", description="API Secret 明文（仅本次返回，请妥善保存）")
    status: bool = Field(..., description="状态")
    created_at: datetime = Field(..., description="创建时间")


class MerchantApiKeyResetResponse(BaseRespEntity):
    """重置 API 密钥响应（api_secret 明文仅此处返回一次）"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="商户ID")
    api_key: str = Field(..., description="新的 API Key")
    api_secret: str = Field("", description="新的 API Secret 明文（仅本次返回，请妥善保存）")
