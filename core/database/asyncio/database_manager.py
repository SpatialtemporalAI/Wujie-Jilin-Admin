#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from core.config import settings
import logging
logger = logging.getLogger(__name__)
class DatabaseManager:
    """数据库连接管理器，封装连接池和会话管理"""
    def __init__(self):
        self._engine = None
        self._session_maker = None
    async def init_pool(self) -> None:
        """初始化数据库连接池"""
        if self._engine is not None:
            return  # 避免重复初始化
        self._engine = create_async_engine(
            settings.DATABASE.URL,
            echo=settings.DATABASE.ECHO,
            pool_size=settings.DATABASE.POOL_SIZE,
            max_overflow=settings.DATABASE.MAX_OVERFLOW,
            pool_recycle=settings.DATABASE.POOL_RECYCLE,
            pool_timeout=settings.DATABASE.POOL_TIMEOUT,
            pool_pre_ping=settings.DATABASE.POOL_PRE_PING,
            pool_use_lifo=settings.DATABASE.POOL_USE_LIFO,
        )
        self._session_maker = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )
    async def close_pool(self) -> None:
        """关闭数据库连接池"""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_maker = None
    async def get_conn(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话连接"""
        if self._session_maker is None:
            raise RuntimeError("数据库连接池未初始化，请先调用init_pool()")
        async with self._session_maker() as session:
            try:
                yield session
            finally:
                await session.close()
    @property
    def session_maker(self) -> Optional[async_sessionmaker[AsyncSession]]:
        """获取会话工厂（谨慎使用）"""
        return self._session_maker
# 创建数据库管理器实例
db_manager = DatabaseManager()
# 提供兼容旧接口的函数
async def init_pool() -> None:
    await db_manager.init_pool()
async def close_pool() -> None:
    await db_manager.close_pool()
async def get_conn() -> AsyncGenerator[AsyncSession, None]:
    async for conn in db_manager.get_conn():
        yield conn