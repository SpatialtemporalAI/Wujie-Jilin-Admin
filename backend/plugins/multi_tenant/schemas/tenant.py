#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional, List
from pydantic import Field
from app.models.common.base import BaseEntity, BaseRespEntity


class TenantCreate(BaseEntity):
    """创建租户请求"""

    name: str = Field(..., description="租户名称", min_length=1, max_length=100)
    code: str = Field(..., description="租户编码", min_length=1, max_length=50)
    description: Optional[str] = Field(None, description="租户描述")
    contact_name: Optional[str] = Field(None, description="联系人")
    contact_email: Optional[str] = Field(None, description="联系邮箱")
    contact_phone: Optional[str] = Field(None, description="联系手机")
    max_users: int = Field(100, description="最大用户数")


class TenantUpdate(BaseEntity):
    """更新租户请求"""

    name: Optional[str] = Field(None, description="租户名称", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="租户描述")
    contact_name: Optional[str] = Field(None, description="联系人")
    contact_email: Optional[str] = Field(None, description="联系邮箱")
    contact_phone: Optional[str] = Field(None, description="联系手机")
    max_users: Optional[int] = Field(None, description="最大用户数")


class TenantQueryParams(BaseEntity):
    """租户查询参数"""

    name: Optional[str] = Field(None, description="租户名称（模糊匹配）")
    code: Optional[str] = Field(None, description="租户编码（模糊匹配）")
    status: Optional[bool] = Field(None, description="状态筛选")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(100, ge=1, le=200, description="每页条数")


class TenantResponse(BaseRespEntity):
    """租户响应数据"""

    name: str
    code: str
    description: Optional[str] = None
    status: bool = True
    config: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    max_users: int = 100


class TenantListResponse(BaseRespEntity):
    """租户列表项"""

    name: str
    code: str
    description: Optional[str] = None
    status: bool = True
    contact_name: Optional[str] = None
    max_users: int = 100


class TenantSimpleResponse(BaseRespEntity):
    """租户简要信息（用于选择器）"""

    name: str
    code: str
    status: bool = True


class TenantAssignUser(BaseEntity):
    """分配用户到租户"""

    user_id: int = Field(..., description="用户ID")
    role: str = Field("member", description="租户角色：owner, admin, member")


class TenantUserInfo(BaseRespEntity):
    """租户中的用户信息"""

    username: str
    nickname: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: bool = True
    tenant_role: str = "member"


class SelectTenantRequest(BaseEntity):
    """选择租户请求"""

    tenant_id: int = Field(..., description="租户ID")
