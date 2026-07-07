#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pydantic import BaseModel, Field, field_validator, BeforeValidator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import (
    Session,
)
from sqlalchemy import select, and_, or_, ColumnElement, Select
from dataclasses import dataclass
from typing import TypeVar, List, Optional, Tuple, Callable, Type, Any, Union, Dict, Annotated
from pydantic import Field, BaseModel
from sqlalchemy.sql import func
from core.response import ResponsePageModel, response_base, ResponsePageDataModel
from sqlalchemy.sql.elements import BinaryExpression
from fastapi import Query
from database.models.base import Base
from app.models.common.base import parse_positive_int

T = TypeVar("SchemaT")


# 分页字段类型：脏值（空 / "null" / "undefined" / "NaN" / 非数字）收敛为默认值，<1 取 1，>max 截断。
# 必须配合 BaseModel 字段使用：BaseModel 字段的 BeforeValidator 会生效，而 Depends 函数参数
# (page: int = Query(...)) 上的 BeforeValidator 不会生效（FastAPI 对标量 query 参数先做 int 解析）。
PageField = Annotated[int, BeforeValidator(parse_positive_int(1))]
PageSizeField = Annotated[int, BeforeValidator(parse_positive_int(100, max_value=2000))]


class PageRequest(BaseModel):
    """分页请求的基类模型"""

    page: PageField = Field(1, description="当前页码，默认第 1 页")
    page_size: PageSizeField = Field(100, description="每页条数，默认 100 条")


async def get_paginated_results(
    db: AsyncSession,
    page_params: PageRequest,
    query: Select,
    schema: Optional[BaseModel] = None,
) -> ResponsePageModel:
    """
    获取分页查询结果
    参数:
        db: 数据库异步会话
        page_params: 分页参数对象
        query: SQLAlchemy查询对象
        schema: 数据模型类，用于转换查询结果
    返回:
        分页查询结果对象
    """
    # 保留未分页的 query 用于 count
    base_query = query
    # 分页
    offset = (page_params.page - 1) * page_params.page_size
    data_query = query.offset(offset).limit(page_params.page_size)
    # maintain_column_froms=True 保留原 FROM（含 join）；否则 SA 2.0 默认会丢弃
    # 由实体列派生的 FROM，使 count(*) 退化为无 FROM 查询（PostgreSQL 恒返回 1）。
    count_query = base_query.with_only_columns(
        func.count(), maintain_column_froms=True
    ).order_by(None)

    # 顺序执行：AsyncSession 不支持同一连接上的并发操作
    data_result = await db.execute(data_query)
    count_result = await db.execute(count_query)
    items = data_result.unique().scalars().all()
    total = count_result.scalar() or 0

    records = [schema.model_validate(item) for item in items] if schema else items
    pages = (total + page_params.page_size - 1) // page_params.page_size
    # 返回分页结果
    return ResponsePageDataModel(
        records=records,
        page=page_params.page,
        page_size=page_params.page_size,
        total=total,
        total_pages=pages,
    )


# FastAPI依赖项：获取分页参数
def get_page_params(
    page: Optional[str] = Query("1", description="页码，从1开始（非正整数回退到第1页）"),
    page_size: Optional[str] = Query("10", description="每页条数，最大2000（非正整数回退到默认值）"),
) -> PageRequest:
    """获取分页查询参数的依赖项。

    page/page_size 以字符串接收（容忍空字符串 / "null" / "undefined" / "NaN" 等脏值），
    交给 PageRequest 字段的 BeforeValidator 收敛为合法正整数，避免触发 int_parsing 错误。
    """
    return PageRequest(page=page, page_size=page_size)
