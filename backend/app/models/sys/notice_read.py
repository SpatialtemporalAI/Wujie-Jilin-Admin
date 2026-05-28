#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
用户通知阅读记录表
存储每个用户对应通知的已读状态
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, UniqueConstraint
from sqlalchemy.orm import mapped_column, Mapped

from core.models.base import Base


class SysNoticeRead(Base):
    """
    用户通知阅读记录表
    记录每个用户收到的通知及已读状态
    """

    __table_args__ = (
        UniqueConstraint("user_id", "notice_id", name="uix_user_notice"),
        {"comment": "用户通知阅读记录表"},
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, index=True, comment="用户ID"
    )
    notice_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, index=True, comment="通知ID"
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="是否已读"
    )
    read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None, comment="阅读时间"
    )
