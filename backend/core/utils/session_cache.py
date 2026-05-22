"""
会话内存缓存
短 TTL 的 LRU 缓存，避免每次请求都访问 Redis 验证会话
每个 worker 进程独立持有一份缓存实例
"""
import threading
import time
from collections import OrderedDict
from typing import Optional, Tuple


class SessionCache:
    """基于 OrderedDict 的 LRU + TTL 会话缓存"""

    def __init__(self, ttl: float = 5, max_size: int = 1024):
        self._ttl = ttl
        self._max_size = max_size
        self._store: OrderedDict[str, Tuple[float, str]] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[str]:
        """返回缓存的 session_id，未命中或已过期返回 None"""
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            expires_at, session_id = entry
            if time.monotonic() > expires_at:
                del self._store[key]
                return None
            self._store.move_to_end(key)
            return session_id

    def set(self, key: str, session_id: str) -> None:
        """存储 session_id，TTL 自动过期"""
        with self._lock:
            expires_at = time.monotonic() + self._ttl
            if key in self._store:
                self._store.move_to_end(key)
            self._store[key] = (expires_at, session_id)
            while len(self._store) > self._max_size:
                self._store.popitem(last=False)

    def invalidate(self, key: str) -> None:
        """移除指定缓存条目"""
        with self._lock:
            self._store.pop(key, None)


_session_cache = SessionCache()


def get_session_cache() -> SessionCache:
    return _session_cache
