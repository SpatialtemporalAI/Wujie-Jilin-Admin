#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from logging import getLogger
from typing import Optional

from fastapi import HTTPException, Request

from core.redis import RedisPool
from core.utils.ip_utils import get_real_client_ip

logger = getLogger(__name__)


async def check_rate_limit(
    key: str,
    limit: int,
    window_seconds: int,
    block_message: str,
) -> None:
    """基于 Redis INCR + EXPIRE 的固定窗口限流。"""
    redis_client = RedisPool.get_client()
    current = await redis_client.incr(key)
    if current == 1:
        await redis_client.expire(key, window_seconds)
    if current > limit:
        ttl = await redis_client.ttl(key)
        logger.warning("限流触发 key=%s count=%s ttl=%s", key, current, ttl)
        raise HTTPException(
            status_code=429,
            detail=f"{block_message}，请在 {max(ttl, 1)} 秒后重试",
        )


async def limit_by_ip(
    request: Request,
    action: str,
    limit: int,
    window_seconds: int,
    scope: str = "global",
    extra_suffix: Optional[str] = None,
) -> None:
    client_ip = get_real_client_ip(request)
    suffix = f":{extra_suffix}" if extra_suffix else ""
    key = f"ratelimit:{scope}:{action}:ip:{client_ip}{suffix}"
    await check_rate_limit(
        key=key,
        limit=limit,
        window_seconds=window_seconds,
        block_message="请求过于频繁",
    )

