#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 只显示需要修改的部分
from typing import Any, Optional, Dict, List, Union
import redis.asyncio as redis
from .redis_pool import RedisPool
class RedisUtil:
    """Redis工具类，提供常用的Redis操作方法"""
    def __init__(self, redis_pool: RedisPool = RedisPool):
        """初始化Redis工具类
        Args:
            redis_pool: Redis连接池实例
        """
        self.redis_pool = redis_pool
    def _get_client(self) -> redis.Redis:
        """获取Redis客户端实例
        Returns:
            redis.Redis: Redis客户端实例
        """
        return self.redis_pool.get_client()
    async def set_nx_ex(self, key: str, value: Any, expire: int) -> bool:
        """原子操作：SET key value EX expire NX"""
        client = self._get_client()
        result = await client.set(key, value, ex=expire, nx=True)
        return result is True or result == b"OK"
    # 然后修改所有使用_get_client()的方法，例如：
    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """设置键值对
        Args:
            key: 键名
            value: 键值
            expire: 过期时间(秒)，默认为None(永不过期)
        Returns:
            bool: 操作结果
        """
        client = self._get_client()
        result = await client.set(key, value)
        if expire and result:
            await client.expire(key, expire)
        return result
    async def get(self, key: str, default: Any = None) -> Any:
        """获取键值
        Args:
            key: 键名
            default: 键不存在时的默认值
        Returns:
            Any: 键值或默认值
        """
        async with await self._get_client() as client:
            result = await client.get(key)
            return result if result is not None else default
    async def delete(self, *keys: str) -> int:
        """删除一个或多个键
        Args:
            *keys: 要删除的键名
        Returns:
            int: 被删除的键的数量
        """
        async with await self._get_client() as client:
            return await client.delete(*keys)
    async def exists(self, *keys: str) -> int:
        """检查一个或多个键是否存在
        Args:
            *keys: 要检查的键名
        Returns:
            int: 存在的键的数量
        """
        async with await self._get_client() as client:
            return await client.exists(*keys)
    async def expire(self, key: str, seconds: int) -> bool:
        """设置键的过期时间
        Args:
            key: 键名
            seconds: 过期时间(秒)
        Returns:
            bool: 操作结果
        """
        async with await self._get_client() as client:
            return await client.expire(key, seconds)
    async def ttl(self, key: str) -> int:
        """获取键的剩余过期时间
        Args:
            key: 键名
        Returns:
            int: 剩余过期时间(秒)，-1表示永不过期，-2表示键不存在
        """
        async with await self._get_client() as client:
            return await client.ttl(key)
    async def incr(self, key: str, amount: int = 1) -> int:
        """将键的数值增加指定量
        Args:
            key: 键名
            amount: 增加的数量，默认为1
        Returns:
            int: 增加后的数值
        """
        async with await self._get_client() as client:
            return await client.incr(key, amount)
    async def decr(self, key: str, amount: int = 1) -> int:
        """将键的数值减少指定量
        Args:
            key: 键名
            amount: 减少的数量，默认为1
        Returns:
            int: 减少后的数值
        """
        async with await self._get_client() as client:
            return await client.decr(key, amount)
    async def hset(self, name: str, key: str, value: Any) -> int:
        """设置哈希表中的字段值
        Args:
            name: 哈希表名
            key: 字段名
            value: 字段值
        Returns:
            int: 操作结果
        """
        async with await self._get_client() as client:
            return await client.hset(name, key, value)
    async def hget(self, name: str, key: str) -> Any:
        """获取哈希表中的字段值
        Args:
            name: 哈希表名
            key: 字段名
        Returns:
            Any: 字段值
        """
        async with await self._get_client() as client:
            return await client.hget(name, key)
    async def hgetall(self, name: str) -> Dict[str, Any]:
        """获取哈希表中的所有字段和值
        Args:
            name: 哈希表名
        Returns:
            Dict[str, Any]: 所有字段和值的字典
        """
        async with await self._get_client() as client:
            return await client.hgetall(name)
    async def hdel(self, name: str, *keys: str) -> int:
        """删除哈希表中的一个或多个字段
        Args:
            name: 哈希表名
            *keys: 要删除的字段名
        Returns:
            int: 被删除的字段的数量
        """
        async with await self._get_client() as client:
            return await client.hdel(name, *keys)
    async def lpush(self, name: str, *values: Any) -> int:
        """将一个或多个值插入到列表头部
        Args:
            name: 列表名
            *values: 要插入的值
        Returns:
            int: 插入后列表的长度
        """
        async with await self._get_client() as client:
            return await client.lpush(name, *values)
    async def rpush(self, name: str, *values: Any) -> int:
        """将一个或多个值插入到列表尾部
        Args:
            name: 列表名
            *values: 要插入的值
        Returns:
            int: 插入后列表的长度
        """
        async with await self._get_client() as client:
            return await client.rpush(name, *values)
    async def lpop(self, name: str) -> Any:
        """移除并返回列表的第一个元素
        Args:
            name: 列表名
        Returns:
            Any: 列表的第一个元素
        """
        async with await self._get_client() as client:
            return await client.lpop(name)
    async def rpop(self, name: str) -> Any:
        """移除并返回列表的最后一个元素
        Args:
            name: 列表名
        Returns:
            Any: 列表的最后一个元素
        """
        async with await self._get_client() as client:
            return await client.rpop(name)
    async def lrange(self, name: str, start: int, end: int) -> List[Any]:
        """获取列表指定范围内的元素
        Args:
            name: 列表名
            start: 起始索引
            end: 结束索引，-1表示最后一个元素
        Returns:
            List[Any]: 元素列表
        """
        async with await self._get_client() as client:
            return await client.lrange(name, start, end)
    async def sadd(self, name: str, *values: Any) -> int:
        """向集合添加一个或多个成员
        Args:
            name: 集合名
            *values: 要添加的成员
        Returns:
            int: 添加的成员数量
        """
        async with await self._get_client() as client:
            return await client.sadd(name, *values)
    async def srem(self, name: str, *values: Any) -> int:
        """移除集合中一个或多个成员
        Args:
            name: 集合名
            *values: 要移除的成员
        Returns:
            int: 移除的成员数量
        """
        async with await self._get_client() as client:
            return await client.srem(name, *values)
    async def smembers(self, name: str) -> set:
        """获取集合中的所有成员
        Args:
            name: 集合名
        Returns:
            set: 成员集合
        """
        async with await self._get_client() as client:
            return await client.smembers(name)
    async def sismember(self, name: str, value: Any) -> bool:
        """判断成员是否在集合中
        Args:
            name: 集合名
            value: 要判断的成员
        Returns:
            bool: 是否在集合中
        """
        async with await self._get_client() as client:
            return await client.sismember(name, value)
    async def zadd(self, name: str, mapping: Dict[Any, float]) -> int:
        """向有序集合添加一个或多个成员，或者更新已存在成员的分数
        Args:
            name: 有序集合名
            mapping: 成员及其分数的字典
        Returns:
            int: 添加的成员数量
        """
        async with await self._get_client() as client:
            return await client.zadd(name, mapping)
    async def zrange(self, name: str, start: int, end: int, withscores: bool = False) -> Union[List[Any], List[tuple]]:
        """获取有序集合指定范围内的成员
        Args:
            name: 有序集合名
            start: 起始索引
            end: 结束索引，-1表示最后一个元素
            withscores: 是否同时返回分数
        Returns:
            Union[List[Any], List[tuple]]: 成员列表或(成员,分数)元组列表
        """
        async with await self._get_client() as client:
            return await client.zrange(name, start, end, withscores=withscores)
    async def zrem(self, name: str, *values: Any) -> int:
        """移除有序集合中的一个或多个成员
        Args:
            name: 有序集合名
            *values: 要移除的成员
        Returns:
            int: 移除的成员数量
        """
        async with await self._get_client() as client:
            return await client.zrem(name, *values)
    async def keys(self, pattern: str = '*') -> List[str]:
        """查找所有符合给定模式的键
        Args:
            pattern: 匹配模式，默认为*（所有键）
        Returns:
            List[str]: 符合模式的键列表
        """
        async with await self._get_client() as client:
            return await client.keys(pattern)
    async def flushdb(self) -> bool:
        """删除当前数据库中的所有键
        Returns:
            bool: 操作结果
        """
        async with await self._get_client() as client:
            return await client.flushdb()
    async def setex(self, key: str, seconds: int, value: Any) -> bool:
        """设置带过期时间的键值对
        Args:
            key: 键名
            seconds: 过期时间(秒)
            value: 键值
        Returns:
            bool: 操作结果
        """
        async with await self._get_client() as client:
            return await client.setex(key, seconds, value)
    async def mset(self, mapping: Dict[str, Any]) -> bool:
        """同时设置多个键值对
        Args:
            mapping: 键值对字典
        Returns:
            bool: 操作结果
        """
        async with await self._get_client() as client:
            return await client.mset(mapping)
    async def mget(self, *keys: str) -> List[Any]:
        """同时获取多个键的值
        Args:
            *keys: 要获取的键名
        Returns:
            List[Any]: 键值列表
        """
        async with await self._get_client() as client:
            return await client.mget(*keys)
    async def publish(self, channel: str, message: Any) -> int:
        """向指定频道发布消息
        Args:
            channel: 频道名
            message: 要发布的消息
        Returns:
            int: 接收到消息的订阅者数量
        """
        async with await self._get_client() as client:
            return await client.publish(channel, message)
# 全局Redis工具实例
redis_util = RedisUtil()
# FastAPI依赖项：获取Redis工具实例
def get_redis_util() -> RedisUtil:
    """获取Redis工具实例
    Returns:
        RedisUtil: Redis工具实例
    """
    return redis_util