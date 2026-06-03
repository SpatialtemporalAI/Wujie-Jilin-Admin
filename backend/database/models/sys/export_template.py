#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sqlalchemy import String, Text, BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from database.models.base import Base


class SysExportTemplate(Base):
    """导出模板表"""

    name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="模板名称"
    )
    module_key: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True, comment="关联模块标识"
    )
    columns: Mapped[str] = mapped_column(
        Text, nullable=False, comment="列配置JSON"
    )
    joins_config: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="JOIN配置JSON，为空则单表查询"
    )
    description: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="模板描述"
    )
    created_by: Mapped[int] = mapped_column(
        BigInteger, nullable=False, comment="创建者ID"
    )
