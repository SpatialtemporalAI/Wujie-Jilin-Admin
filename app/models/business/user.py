#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from core.models.base import Base, DataClassBase, snowflake_id_key
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String, Boolean, ForeignKey, text
from typing import TYPE_CHECKING, List
from sqlalchemy.dialects.postgresql import ARRAY


class AppUser(Base):
    """
    用户表 - 存储用户信息
    """

    name: Mapped[str] = mapped_column(String(255), comment="用户名")
    phone_code: Mapped[str] = mapped_column(
        String(10), comment="手机号区号，如：+86、+1 等", nullable=False
    )
    phone: Mapped[str] = mapped_column(String(13), comment="手机号")
    salt: Mapped[str] = mapped_column(
        String(255), comment="密码盐值", nullable=True, default=""
    )
    password: Mapped[str] = mapped_column(
        String(255), comment="密码哈希值", nullable=True, default=""
    )
    email: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="邮箱", default=None
    )
    wx_openid: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="微信 openid", default=None
    )
    wx_unionid: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="微信 unionid", default=None
    )
