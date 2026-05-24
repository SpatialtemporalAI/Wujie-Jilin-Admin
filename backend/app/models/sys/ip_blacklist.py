#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime

from core.models.base import Base
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import String, DateTime, BigInteger


class SysIpBlacklist(Base):
    """
    IP 黑名单表
    permanent: 永久；temporary: 临时（expire_at 为空表示永久）
    """

    ip: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True, comment="IP 地址"
    )
    type: Mapped[str] = mapped_column(
        String(16), nullable=False, default="permanent", comment="类型：permanent / temporary"
    )
    reason: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="加入原因"
    )
    expire_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="过期时间（temporary 必填）"
    )
    creator_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="创建人ID（系统自动写入时为空）"
    )
