#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.common.base import BaseReqEntity, BaseRespEntity, BoolField


class SysPermissionQueryParams(BaseModel):
    """系统权限查询参数模型

    注意：查询参数统一使用基础 Optional[str]（FastAPI 对 Annotated query 模型字段在部分
    版本存在兼容性问题，可能漏收集请求参数导致模型构造缺键报 missing）；空值/脏值收敛由 service 层完成。
    """

    category: Optional[str] = Field(None, description="权限分类")
    status: Optional[str] = Field(None, description="状态：True-启用，False-禁用")


class SysPermissionCreate(BaseReqEntity):
    """创建权限请求"""

    name: str = Field(..., description="权限名称")
    code: str = Field(..., description="权限编码")
    description: Optional[str] = Field(None, description="权限描述")
    resource_path: Optional[str] = Field(None, description="资源路径")
    method: Optional[str] = Field(None, description="请求方法")
    category: Optional[str] = Field(None, description="权限分类")
    type: str = Field(default="api", description="权限类型")
    status: bool = Field(default=True, description="状态")
    sort: int = Field(default=0, description="排序号")


class SysPermissionUpdate(BaseReqEntity):
    """更新权限请求"""

    name: Optional[str] = Field(None, description="权限名称")
    code: Optional[str] = Field(None, description="权限编码")
    description: Optional[str] = Field(None, description="权限描述")
    resource_path: Optional[str] = Field(None, description="资源路径")
    method: Optional[str] = Field(None, description="请求方法")
    category: Optional[str] = Field(None, description="权限分类")
    type: Optional[str] = Field(None, description="权限类型")
    status: BoolField = Field(None, description="状态")
    sort: Optional[int] = Field(None, description="排序号")


class SysPermissionResponse(BaseRespEntity):
    """权限响应模型"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    description: Optional[str] = None
    resource_path: Optional[str] = None
    method: Optional[str] = None
    category: Optional[str] = None
    type: Optional[str] = None
    status: bool = True
    sort: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
