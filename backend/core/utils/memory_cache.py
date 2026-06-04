"""
全局通用 L2 内存缓存

基于 OrderedDict 的 LRU + TTL 缓存，支持 namespace 隔离。
每个 worker 进程独立持有一份缓存实例，用于减少跨请求的重复 Redis/DB 查询。
"""
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class _CacheEntry:
    expires_at: float
    value: Any


class CacheNamespace:
    USER = "user"                  # key: str(user_id), TTL: 30s
    PERMISSION = "permission"      # key: f"{user_id}:{permission_code}", TTL: 60s
    IP_BLACKLIST = "ip_blacklist"  # key: ip, TTL: 10s
    SESSION = "session"            # key: f"{redis_key}:{session_id}", TTL: 5s


class MemoryCache:
    """基于 OrderedDict 的 LRU + TTL 通用内存缓存，支持 namespace 隔离。"""

    def __init__(self, max_entries_per_namespace: int = 1024):
        self._max_entries = max_entries_per_namespace
        self._namespaces: dict[str, OrderedDict[str, _CacheEntry]] = {}
        self._locks: dict[str, threading.Lock] = {}
        self._global_lock = threading.Lock()

    def _get_namespace(self, namespace: str) -> tuple[OrderedDict, threading.Lock]:
        if namespace not in self._namespaces:
            with self._global_lock:
                if namespace not in self._namespaces:
                    self._namespaces[namespace] = OrderedDict()
                    self._locks[namespace] = threading.Lock()
        return self._namespaces[namespace], self._locks[namespace]

    def get(self, namespace: str, key: str) -> Any | None:
        store, lock = self._get_namespace(namespace)
        with lock:
            entry = store.get(key)
            if entry is None:
                return None
            if time.monotonic() > entry.expires_at:
                del store[key]
                return None
            store.move_to_end(key)
            return entry.value

    def set(self, namespace: str, key: str, value: Any, ttl: float) -> None:
        if ttl <= 0:
            return
        store, lock = self._get_namespace(namespace)
        with lock:
            expires_at = time.monotonic() + ttl
            if key in store:
                store.move_to_end(key)
            store[key] = _CacheEntry(expires_at=expires_at, value=value)
            while len(store) > self._max_entries:
                store.popitem(last=False)

    def delete(self, namespace: str, key: str) -> None:
        if namespace not in self._namespaces:
            return
        store, lock = self._get_namespace(namespace)
        with lock:
            store.pop(key, None)

    def delete_by_prefix(self, namespace: str, prefix: str) -> None:
        if namespace not in self._namespaces:
            return
        store, lock = self._get_namespace(namespace)
        with lock:
            keys_to_remove = [k for k in store if k.startswith(prefix)]
            for k in keys_to_remove:
                del store[k]

    def invalidate(self, namespace: str) -> None:
        if namespace not in self._namespaces:
            return
        store, lock = self._get_namespace(namespace)
        with lock:
            store.clear()

    def stats(self) -> dict[str, int]:
        return {ns: len(store) for ns, store in self._namespaces.items()}


_cache: Optional[MemoryCache] = None


def get_memory_cache() -> MemoryCache:
    global _cache
    if _cache is None:
        _cache = MemoryCache()
    return _cache
