#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sqlalchemy.orm import Mapped, mapped_column, MappedAsDataclass
from sqlalchemy import BigInteger


class TenantMixin(MappedAsDataclass):
    """租户隔离 Mixin，标记模型为租户隔离并添加 tenant_id 列。

    注意：此 Mixin 用于模型定义时直接继承。
    通过插件动态添加 tenant_id 的模型不需要继承此类，
    而是通过 tenant_filter 注册表机制实现隔离。
    """

    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
        default=0,
        comment="租户ID",
    )
