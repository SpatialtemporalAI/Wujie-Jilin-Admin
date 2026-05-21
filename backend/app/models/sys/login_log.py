#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from core.models.base import Base
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import String, Boolean, DateTime
from datetime import datetime

from database.utils.timezone import timezone


class SysLoginLog(Base):
    """
    系统登录日志表
    记录用户登录尝试（成功和失败）
    """

    username: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True, comment="登录用户名"
    )
    ip: Mapped[str] = mapped_column(
        String(50), nullable=True, comment="客户端IP"
    )
    status: Mapped[bool] = mapped_column(
        Boolean, nullable=False, comment="登录状态：True-成功，False-失败"
    )
    detail: Mapped[str] = mapped_column(
        String(255), nullable=True, comment="详情：登录成功/密码错误/用户不存在等"
    )
    user_agent: Mapped[str] = mapped_column(
        String(500), nullable=True, comment="登录设备(User-Agent)"
    )
    login_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default_factory=timezone.now,
        comment="登录时间",
    )
