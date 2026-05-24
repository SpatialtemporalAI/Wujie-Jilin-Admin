#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
限流业务服务：
- 登录失败统计与自动拉黑
- 启动预热 DB 黑名单到 Redis
"""
import logging

from core.config import settings
from core.security.rate_limit import (
    clear_login_failure as _redis_clear_login_failure,
    incr_login_failure as _redis_incr_login_failure,
)
from core.security.rate_limit_config import RateLimitConfigProvider
from database import get_session
from modules.admin.services.sys.ip_blacklist_service import IpBlacklistService

logger = logging.getLogger(__name__)


class RateLimitService:
    """限流相关业务编排"""

    @staticmethod
    async def record_login_failure(ip: str, username: str | None = None) -> None:
        """登录失败 +1，超过阈值自动拉黑 IP（temporary，TTL = LOGIN_FAIL_BLOCK_TTL）。"""
        if not ip or ip == "unknown":
            return
        fail_max = await RateLimitConfigProvider.get(
            "rate_limit.login_fail_max", settings.RATE_LIMIT.LOGIN_FAIL_MAX
        )
        block_ttl = await RateLimitConfigProvider.get(
            "rate_limit.login_fail_block_ttl", settings.RATE_LIMIT.LOGIN_FAIL_BLOCK_TTL
        )
        try:
            count = await _redis_incr_login_failure(ip)
        except Exception as exc:
            logger.error("登录失败计数写入 Redis 失败 ip=%s err=%s", ip, exc)
            return

        if count < fail_max:
            return

        reason = f"登录失败 {count} 次自动拉黑（username={username or 'unknown'}）"
        try:
            async for db in get_session():
                await IpBlacklistService.auto_block(
                    db=db,
                    ip=ip,
                    reason=reason,
                    ttl_seconds=block_ttl,
                )
                break
        except Exception as exc:
            logger.error("自动拉黑 IP 失败 ip=%s err=%s", ip, exc)

    @staticmethod
    async def clear_login_failure(ip: str) -> None:
        if not ip:
            return
        try:
            await _redis_clear_login_failure(ip)
        except Exception as exc:
            logger.error("清理登录失败计数失败 ip=%s err=%s", ip, exc)

    @staticmethod
    async def warmup_blacklist() -> int:
        """启动时把 DB 中未过期的黑名单加载到 Redis。"""
        try:
            async for db in get_session():
                count = await IpBlacklistService.warmup_to_redis(db)
                logger.info("IP 黑名单预热完成 count=%s", count)
                return count
        except Exception as exc:
            logger.error("IP 黑名单预热失败 err=%s", exc)
            return 0
