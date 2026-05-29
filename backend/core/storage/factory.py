#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
存储后端工厂
"""
from core.config import settings
from .base import StorageBackend
from .local import LocalStorageBackend


def get_storage_backend() -> StorageBackend:
    """
    根据配置返回对应的存储后端实例

    Returns:
        StorageBackend 实例
    """
    platform = settings.STORAGE.PLATFORM

    if platform == "local":
        return LocalStorageBackend(base_dir=settings.UPLOAD_LOCAL.BASE_DIR)

    raise ValueError(f"不支持的存储平台: {platform}")
