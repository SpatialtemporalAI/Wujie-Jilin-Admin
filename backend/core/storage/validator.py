#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文件校验工具
"""
import os
import uuid
from typing import Optional, Tuple

from core.exception.errors import RequestError


def validate_file_extension(
    filename: str,
    allowed_extensions: Optional[Tuple[str, ...]] = None,
) -> str:
    """
    校验文件扩展名

    Args:
        filename: 原始文件名
        allowed_extensions: 允许的扩展名白名单 (不含点, 如 ("png", "jpg"))

    Returns:
        扩展名 (不含点, 小写)

    Raises:
        RequestError: 文件扩展名不在白名单中
    """
    ext = os.path.splitext(filename)[1].lstrip(".").lower()
    if not ext:
        raise RequestError(msg="文件缺少扩展名")
    if allowed_extensions and ext not in [e.lower() for e in allowed_extensions]:
        raise RequestError(
            msg=f"不支持的文件类型: .{ext}，允许的类型: {', '.join(allowed_extensions)}"
        )
    return ext


def validate_file_size(size_bytes: int, max_size: int) -> None:
    """
    校验文件大小

    Args:
        size_bytes: 文件大小 (字节)
        max_size: 最大允许大小 (字节)

    Raises:
        RequestError: 文件大小超过限制
    """
    if size_bytes > max_size:
        max_mb = max_size / (1024 * 1024)
        raise RequestError(msg=f"文件大小超过限制，最大允许 {max_mb:.1f}MB")


def generate_stored_name(extension: str) -> str:
    """
    生成唯一存储文件名

    Args:
        extension: 文件扩展名 (不含点)

    Returns:
        UUID-based 存储文件名
    """
    return f"{uuid.uuid4().hex}.{extension}"
