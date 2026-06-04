"""
通用缓存装饰器

支持同步和异步函数，自动将结果存入 MemoryCache。
使用哨兵值区分"未命中"和"缓存了 None/空值"。
"""
import functools
import inspect
from typing import Callable, Optional

from core.utils.memory_cache import get_memory_cache

_PRESENT = object()


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
                wrapper = cache.get(namespace, key)
                if wrapper is not None:
                    return wrapper.value
                result = await func(*args, **kwargs)
                cache.set(namespace, key, _WrapperValue(result), ttl)
                return result
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                cache = get_memory_cache()
                key = builder(*args, **kwargs)
                wrapper = cache.get(namespace, key)
                if wrapper is not None:
                    return wrapper.value
                result = func(*args, **kwargs)
                cache.set(namespace, key, _WrapperValue(result), ttl)
                return result
            return sync_wrapper
    return decorator


class _WrapperValue:
    __slots__ = ("value",)

    def __init__(self, value):
        self.value = value
