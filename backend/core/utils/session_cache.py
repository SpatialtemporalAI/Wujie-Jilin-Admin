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
        self._store: OrderedDict[str, Tuple[float, bool]] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, redis_key: str, session_id: str) -> Optional[bool]:
        """返回缓存是否命中，未命中或已过期返回 None"""
        composite_key = f"{redis_key}:{session_id}"
        with self._lock:
            entry = self._store.get(composite_key)
            if entry is None:
                return None
            expires_at, _ = entry
            if time.monotonic() > expires_at:
                del self._store[composite_key]
                return None
            self._store.move_to_end(composite_key)
            return True

    def set(self, redis_key: str, session_id: str) -> None:
        """存储会话验证结果，TTL 自动过期"""
        composite_key = f"{redis_key}:{session_id}"
        with self._lock:
            expires_at = time.monotonic() + self._ttl
            if composite_key in self._store:
                self._store.move_to_end(composite_key)
            self._store[composite_key] = (expires_at, True)
            while len(self._store) > self._max_size:
                self._store.popitem(last=False)

    def invalidate(self, redis_key: str, session_id: str = None) -> None:
        """移除缓存条目，session_id 为 None 时清除该 redis_key 下的所有条目"""
        with self._lock:
            if session_id is not None:
                self._store.pop(f"{redis_key}:{session_id}", None)
            else:
                prefix = f"{redis_key}:"
                keys_to_remove = [k for k in self._store if k.startswith(prefix)]
                for k in keys_to_remove:
                    del self._store[k]


_session_cache = SessionCache()


def get_session_cache() -> SessionCache:
    return _session_cache
