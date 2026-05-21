#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional
from pydantic import BaseModel, Field


class TemplateColumnItem(BaseModel):
    """模板中的单列配置"""
    field: str = Field(..., description="字段名")
    header: str = Field(..., description="Excel 列头")
    width: int = Field(20, description="列宽")
    table: str | None = Field(None, description="来源表名，跨表查询时必填")


class JoinCondition(BaseModel):
    """JOIN 条件中的一对字段映射"""
    left: str = Field(..., description="左表字段，如 sys_user.id")
    right: str = Field(..., description="右表字段，如 sys_user_role.user_id")


class JoinConfigItem(BaseModel):
    """单个 JOIN 配置"""
    table: str = Field(..., description="要 JOIN 的表名")
    type: str = Field("left", description="JOIN 类型: left/inner/right")
    on: list[JoinCondition] = Field(..., description="JOIN 条件")


class ExportTemplateCreate(BaseModel):
    """创建导出模板"""
    name: str = Field(..., description="模板名称")
    module_key: str = Field(..., description="关联模块")
    columns: list[TemplateColumnItem] = Field(..., description="列配置")
    joins_config: list[JoinConfigItem] | None = Field(None, description="JOIN 配置，为空则单表查询")
    description: str | None = Field(None, description="模板描述")


class ExportTemplateUpdate(BaseModel):
    """更新导出模板"""
    name: str | None = Field(None, description="模板名称")
    columns: list[TemplateColumnItem] | None = Field(None, description="列配置")
    joins_config: list[JoinConfigItem] | None = Field(None, description="JOIN 配置")
    description: str | None = Field(None, description="模板描述")


class ExportTemplateResponse(BaseModel):
    """模板响应"""
    id: int
    name: str
    module_key: str
    columns: list[TemplateColumnItem]
    joins_config: list[JoinConfigItem] | None = None
    description: str | None = None
    created_by: int
    created_at: str | None = None
    updated_at: str | None = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_with_format(cls, obj) -> "ExportTemplateResponse":
        import json

        columns = [TemplateColumnItem(**c) for c in json.loads(obj.columns)]
        joins_config = None
        if obj.joins_config:
            joins_config = [JoinConfigItem(**j) for j in json.loads(obj.joins_config)]

        def fmt(dt):
            return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else None

        return cls(
            id=obj.id,
            name=obj.name,
            module_key=obj.module_key,
            columns=columns,
            joins_config=joins_config,
            description=obj.description,
            created_by=obj.created_by,
            created_at=fmt(obj.created_at),
            updated_at=fmt(obj.updated_at),
        )


class ModuleFieldResponse(BaseModel):
    """模块可用字段"""
    field: str
    header: str
    width: int = 20


class ModuleInfoResponse(BaseModel):
    """模块信息（含可用字段列表）"""
    module_key: str
    name: str
    fields: list[ModuleFieldResponse]
