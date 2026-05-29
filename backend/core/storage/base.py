#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
存储后端抽象基类
"""
from abc import ABC, abstractmethod


class StorageBackend(ABC):
    """文件存储后端抽象基类"""

    @abstractmethod
    async def save(self, file_data: bytes, stored_name: str, path_prefix: str) -> str:
        """
        保存文件

        Args:
            file_data: 文件二进制数据
            stored_name: 存储文件名
            path_prefix: 路径前缀 (如 2026/05/28)

        Returns:
            文件存储路径
        """

    @abstractmethod
    async def read(self, file_path: str) -> bytes:
        """
        读取文件

        Args:
            file_path: 文件存储路径

        Returns:
            文件二进制数据
        """

    @abstractmethod
    async def delete(self, file_path: str) -> bool:
        """
        删除文件

        Args:
            file_path: 文件存储路径

        Returns:
            是否删除成功
        """

    @abstractmethod
    def get_full_url(self, file_path: str) -> str:
        """
        获取文件完整访问 URL

        Args:
            file_path: 文件存储路径

        Returns:
            文件访问 URL
        """
