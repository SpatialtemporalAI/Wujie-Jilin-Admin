#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional, Any, final
import redis as redis
from core.config import settings
from typing import Generator
from contextlib import contextmanager
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
            with redis.Redis(connection_pool=cls._pool) as client:
                try:
                    client.ping()
                except Exception as e:
                    cls._pool = None
                    raise ConnectionError(f"Redis 连接池初始化失败: {str(e)}")
    @classmethod
    def get_pool(cls) -> redis.ConnectionPool:
        """获取连接池实例"""
        if not cls._pool:
            raise RuntimeError("Redis连接池未初始化，请先调用init方法")
        return cls._pool
    @classmethod
    def get_client(cls) -> redis.Redis:
        """获取一个 Redis 连接，当使用完后关闭"""
        client = redis.Redis(connection_pool=cls._pool)
        try:
            yield client
        finally:
            client.close()
    @classmethod
    def close_pool(cls) -> None:
        """关闭连接池"""
        if cls._pool is not None:
            cls._pool.disconnect()
            cls._pool = None
# FastAPI 依赖项：获取一个 Redis 客户端（自动从连接池获取）
def get_redis_client() -> redis.Redis:
    return RedisPool.get_client()
@contextmanager
def get_sync_redis_client() -> Generator[redis.Redis, None, None]:
    """
    获取同步Redis客户端的上下文管理器
    用法:
        with get_sync_redis_client() as redis:
            redis.set("key", "value")
    自动处理连接的获取和关闭，确保资源释放
    """
    # 从连接池获取客户端
    client = redis.Redis(connection_pool=RedisPool.get_pool())
    try:
        yield client  # 提供客户端给上下文使用
    finally:
        # 确保连接被关闭（放回连接池）
        client.close()
# 用于FastAPI依赖注入的版本
def get_sync_redis_dependency() -> Generator[redis.Redis, None, None]:
    """
    供FastAPI的Depends使用的同步Redis依赖项
    在路径操作函数中使用:
        def endpoint(redis: Redis = Depends(get_sync_redis_dependency)):
            redis.set("key", "value")
    """
    with get_sync_redis_client() as client:
        yield client