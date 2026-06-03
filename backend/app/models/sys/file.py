#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
系统文件存储表
"""
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import String, BigInteger

from database.models.base import Base


class SysFile(Base):
    """
    系统文件存储表
    """

    original_name: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="原始文件名"
    )
    stored_name: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="存储文件名"
    )
    file_path: Mapped[str] = mapped_column(
        String(1000), nullable=False, comment="存储路径"
    )
    file_size: Mapped[int] = mapped_column(
        BigInteger, nullable=False, comment="文件大小(字节)"
    )
    mime_type: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="MIME类型"
    )
    extension: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="扩展名"
    )
    created_by: Mapped[int] = mapped_column(
        BigInteger, nullable=False, comment="上传者用户ID"
    )
    storage_platform: Mapped[str] = mapped_column(
        String(50), nullable=False, default="local", comment="存储平台标识"
    )
    hash: Mapped[str | None] = mapped_column(
        String(64), nullable=True, default=None, comment="SHA-256哈希"
    )
