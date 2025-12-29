#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional, Any, Union
from core.config import settings
import redis.asyncio as redis
from redis.asyncio.client import Redis
class AsyncRedisClient:
    """异步 Redis 客户端封装类"""
    def __init__(self, settings: RedisSettings = RedisSettings()):
        self.settings = settings
        self._client: Optional[Redis] = None
    async def connect(self) -> None:
        """建立 Redis 连接"""
        try:
            self._client = redis.Redis(
                host=settings.REDIS.HOST,
                port=settings.REDIS.PORT,
                db=settings.REDIS.DB,
                password=settings.REDIS.PASSWORD,
                decode_responses=settings.REDIS.DECODE_RESPONSES,
                socket_connect_timeout=settings.REDIS.SOCKET_CONNECT_TIMEOUT,
            )
            # 测试连接
            await self._client.ping()
        except Exception as e:
            raise ConnectionError(f"Redis 连接失败: {str(e)}")
    @property
    async def client(self) -> Redis:
        """获取 Redis 客户端实例，确保连接有效"""
        if not self._client:
            await self.connect()
        else:
            try:
                # 检查连接是否有效
                await self._client.ping()
            except:
                await self.connect()
        return self._client
    # 字符串操作
    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """设置键值对"""
        client = await self.client
        return await client.set(key, value, ex=expire)
    async def get(self, key: str) -> Optional[str]:
        """获取键值"""
        client = await self.client
        return await client.get(key)
    async def delete(self, key: str) -> int:
        """删除键"""
        client = await self.client
        return await client.delete(key)
    # 哈希操作
    async def hset(self, name: str, key: str, value: Any) -> int:
        """设置哈希字段"""
        client = await self.client
        return await client.hset(name, key, value)
    async def hget(self, name: str, key: str) -> Optional[str]:
        """获取哈希字段值"""
        client = await self.client
        return await client.hget(name, key)
    async def hgetall(self, name: str) -> dict:
        """获取哈希所有字段和值"""
        client = await self.client
        return await client.hgetall(name)
    # 列表操作
    async def lpush(self, name: str, *values: Any) -> int:
        """左侧插入元素"""
        client = await self.client
        return await client.lpush(name, *values)
    async def rpop(self, name: str) -> Optional[str]:
        """右侧弹出元素"""
        client = await self.client
        return await client.rpop(name)
    # 其他常用操作
    async def expire(self, key: str, seconds: int) -> bool:
        """设置键过期时间"""
        client = await self.client
        return await client.expire(key, seconds)
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        client = await self.client
        return await client.exists(key) == 1
    async def flushdb(self) -> bool:
        """清空当前数据库"""
        client = await self.client
        return await client.flushdb()
# 创建 Redis 实例
redis_client = AsyncRedisClient()
# 依赖项，用于 FastAPI 路由中注入
async def get_redis() -> AsyncRedisClient:
    return redis_client