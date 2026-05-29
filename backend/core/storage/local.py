#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
本地文件存储后端
"""
import os

import aiofiles

from core.exception.errors import NotFoundError
from .base import StorageBackend


class LocalStorageBackend(StorageBackend):
    """本地文件系统存储"""

    def __init__(self, base_dir: str = "uploads"):
        self._base_dir = base_dir

    async def save(self, file_data: bytes, stored_name: str, path_prefix: str) -> str:
        dir_path = os.path.join(self._base_dir, path_prefix)
        os.makedirs(dir_path, exist_ok=True)

        file_path = f"{path_prefix}/{stored_name}"
        full_path = os.path.join(self._base_dir, path_prefix, stored_name)

        async with aiofiles.open(full_path, "wb") as f:
            await f.write(file_data)

        return file_path

    async def read(self, file_path: str) -> bytes:
        full_path = os.path.join(self._base_dir, file_path)
        if not os.path.exists(full_path):
            raise NotFoundError(msg="文件不存在")
        async with aiofiles.open(full_path, "rb") as f:
            return await f.read()

    async def delete(self, file_path: str) -> bool:
        full_path = os.path.join(self._base_dir, file_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        return False

    def get_full_url(self, file_path: str) -> str:
        return f"/uploads/{file_path}"
