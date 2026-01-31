#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional, Any
import redis.asyncio as redis
from core.config import settings
from logging import getLogger
logger = getLogger(__name__)
class RedisPool:
    """异步 Redis 连接池管理类"""
    _pool: Optional[redis.ConnectionPool] = None
    @classmethod
    async def init_pool(cls) -> None:
        """初始化连接池"""
        if not cls._pool:
            cls._pool = redis.ConnectionPool(
                host=settings.REDIS.HOST,
                port=settings.REDIS.PORT,
                db=settings.REDIS.DB,
                password=settings.REDIS.PASSWORD,
                decode_responses=settings.REDIS.DECODE_RESPONSES,
                max_connections=settings.REDIS.MAX_CONNECTIONS,
                socket_connect_timeout=settings.REDIS.SOCKET_CONNECT_TIMEOUT,
                socket_timeout=settings.REDIS.SOCKET_TIMEOUT,
                socket_keepalive=settings.REDIS.SOCKET_KEEPALIVE,
                socket_keepalive_options=settings.REDIS.SOCKET_KEEPALIVE_OPTIONS,
                retry_on_timeout=settings.REDIS.RETRY_ON_TIMEOUT,
            )
            # 验证连接池有效性
            async with redis.Redis(connection_pool=cls._pool) as client:
                try:
                    await client.ping()
                except Exception as e:
                    cls._pool = None
                    raise ConnectionError(f"Redis 连接池初始化失败: {str(e)}")
    @classmethod
    def get_client(cls) -> redis.Redis:
        """获取一个 Redis 连接客户端"""
        if cls._pool is None:
            raise RuntimeError("Redis 连接池尚未初始化，请先调用 init_pool()")
        return redis.Redis(connection_pool=cls._pool)
    @classmethod
    async def close_pool(cls) -> None:
        """关闭连接池"""
        if cls._pool is not None:
            await cls._pool.disconnect()
            cls._pool = None
# FastAPI 依赖项：获取一个 Redis 客户端（自动从连接池获取）
async def get_redis_client() -> redis.Redis:
    """获取Redis客户端实例，作为FastAPI依赖项"""
    return RedisPool.get_client()