#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import String, Boolean, DateTime

from database.models.base import Base
from database.utils.timezone import timezone


class PluginRegistry(Base):
    """
    插件注册表
    记录已安装的插件及其版本
    """

    name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True, comment="插件名称"
    )
    version: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="插件版本"
    )
    is_installed: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="是否已安装"
    )
    installed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        init=False,
        default_factory=timezone.now,
        comment="安装时间",
    )
