"""
gRPC 实时推送进程内去重门

职责：
对「同一机器人 + 同一方法 + 字节级完全相同的载荷」在短窗口内（默认 1s）只推一次，
从源头压掉双击 / 多标签页 / 并发请求造成的 1s 内重复推送。

设计要点：
- 键 = (service_name, method_name, robot_id, payload_hash)
  只压「完全相同」的重复；不同值（如速度 low→high）不拦截，正常下发。
- 「预约式」置位：should_suppress 在检查命中时立即登记本次时间戳，
  check 与 set 之间无 await，asyncio 单线程下天然原子，可挡住真正并发的相同请求。
- 仅内存、进程级：单 worker 部署足以覆盖；多 worker 下同进程重复仍能挡住，
  跨进程重复由前端互斥锁 + 重试队列 cancel_superseded 兜底。
- 非权威缓存：即使误压，重试队列仍保证最终一致；故用内存而非 Redis，零外部依赖。

调用方：modules/robot/services/robot_config_service.py:_push_with_retry
（语音 / 速度 / 电量三类配置推送的唯一入口）。
"""
import hashlib
import json
import logging
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# 去重窗口（秒）：同键在此窗口内重复推送将被压掉
DEDUP_WINDOW_SECONDS: float = 1.0

# _last_pushed 容量上限：超过则触发机会式过期清理，避免无限增长
_MAX_ENTRIES: int = 4096

# key -> monotonic 时间戳
_last_pushed: Dict[str, float] = {}


def _make_key(
    service_name: str,
    method_name: str,
    robot_id: Optional[int],
    payload: Dict[str, Any],
) -> str:
    """构造去重键：service:method:robot_id:payload_md5

    payload 用 JSON 规范化（sort_keys）后再哈希，保证字段顺序不影响判定。
    """
    raw = json.dumps(payload or {}, sort_keys=True, default=str, ensure_ascii=False)
    digest = hashlib.md5(raw.encode("utf-8")).hexdigest()[:16]
    return f"{service_name}:{method_name}:{robot_id}:{digest}"


def _cleanup_expired(now: float, window: float) -> None:
    """机会式清理过期条目，控制 _last_pushed 体量"""
    if len(_last_pushed) < _MAX_ENTRIES:
        return
    # 清掉窗口 10 倍以外的旧记录；留够余量避免频繁清理
    threshold = window * 10
    for key, ts in list(_last_pushed.items()):
        if now - ts > threshold:
            _last_pushed.pop(key, None)


def should_suppress(
    service_name: str,
    method_name: str,
    robot_id: Optional[int],
    payload: Dict[str, Any],
    window: float = DEDUP_WINDOW_SECONDS,
) -> bool:
    """是否应压掉本次实时推送。

    「预约式」语义：命中（未超窗）返回 True；未命中则立即登记时间戳并返回 False。
    check + set 之间无 await，asyncio 单线程下原子，可挡并发相同请求。

    Returns:
        True  —— 窗口内刚推过同键载荷，本次可跳过 RPC；
        False —— 首次或已过窗，照常推送（并已登记本次时间）。
    """
    key = _make_key(service_name, method_name, robot_id, payload)
    now = time.monotonic()
    _cleanup_expired(now, window)

    last = _last_pushed.get(key)
    if last is not None and (now - last) < window:
        return True

    # 预约：无论本次推送成败，窗口内同键再来都压掉
    _last_pushed[key] = now
    return False
