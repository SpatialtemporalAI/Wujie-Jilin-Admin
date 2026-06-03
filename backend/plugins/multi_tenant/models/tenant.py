#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from database.models.base import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String, Text, Boolean, BigInteger, Table, Column, ForeignKey
from typing import Optional, List


# 用户-租户关联表
sys_user_tenant_association = Table(
    "sys_user_tenant",
    Base.metadata,
    Column(
        "user_id",
        BigInteger,
        ForeignKey("sys_user.id", ondelete="CASCADE"),
        primary_key=True,
        comment="用户ID",
    ),
    Column(
        "tenant_id",
        BigInteger,
        ForeignKey("sys_tenant.id", ondelete="CASCADE"),
        primary_key=True,
        comment="租户ID",
    ),
    Column(
        "role",
        String(50),
        nullable=False,
        default="member",
        comment="租户角色：owner, admin, member",
    ),
    comment="用户租户关联表",
)


class Tenant(Base):
    """
    租户表
    存储租户/组织的基本信息和配置
    """

    __tablename__ = "sys_tenant"

    name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, comment="租户名称"
    )
    code: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True, comment="租户编码"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, default=None, comment="租户描述"
    )
    status: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="状态：True-启用，False-禁用"
    )
    config: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, default=None, comment="租户配置(JSON)"
    )
    contact_name: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, default=None, comment="联系人"
    )
    contact_email: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, default=None, comment="联系邮箱"
    )
    contact_phone: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, default=None, comment="联系手机"
    )
    max_users: Mapped[int] = mapped_column(
        default=100, comment="最大用户数"
    )
    # 关系在 on_activate() 中动态设置（避免模型导入时要求 SysUser 已有 tenants 属性）
    # users: Mapped[List["SysUser"]] — 通过 on_activate() 添加
