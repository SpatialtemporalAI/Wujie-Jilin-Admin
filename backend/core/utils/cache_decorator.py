"""
通用缓存装饰器

支持同步和异步函数，自动将结果存入 MemoryCache。
"""
import functools
import inspect
from typing import Callable, Optional

from core.utils.memory_cache import get_memory_cache


def _default_key_builder(*args, **kwargs) -> str:
    parts = [str(a) for a in args]
    parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    return ":".join(parts)


def cached(namespace: str, ttl: float, key_builder: Optional[Callable] = None):
    builder = key_builder or _default_key_builder

    def decorator(func):
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                cache = get_memory_cache()
                key = builder(*args, **kwargs)
                result = cache.get(namespace, key)
                if result is not None:
                    return result
                result = await func(*args, **kwargs)
                if result is not None:
                    cache.set(namespace, key, result, ttl)
                return result
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                cache = get_memory_cache()
                key = builder(*args, **kwargs)
                result = cache.get(namespace, key)
                if result is not None:
                    return result
                result = func(*args, **kwargs)
                if result is not None:
                    cache.set(namespace, key, result, ttl)
                return result
            return sync_wrapper
    return decorator
