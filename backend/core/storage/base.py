#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
存储后端抽象基类
"""
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator


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
        读取文件（全量，小文件用）

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

    @abstractmethod
    def file_size(self, file_path: str) -> int:
        """获取文件大小（字节）"""

    @abstractmethod
    def get_full_path(self, file_path: str) -> str:
        """获取文件系统绝对路径"""

    @abstractmethod
    def stream(
        self, file_path: str, start: int = 0, end: int | None = None, chunk_size: int = 64 * 1024
    ) -> AsyncGenerator[bytes, None]:
        """
        分块流式读取文件

        Args:
            file_path: 文件存储路径
            start: 起始字节偏移
            end: 结束字节偏移（含），None 表示文件末尾
            chunk_size: 每块大小（字节）
        """
