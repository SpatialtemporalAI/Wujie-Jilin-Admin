#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""限流参数动态配置提供器。

从 SysConfig 表读取 rate_limit.* 配置项，内存缓存 30 秒。
缓存失效由 ConfigService 写操作触发，降级时 fallback 到 settings.RATE_LIMIT。
"""
import json
import logging
import time
from typing import Any

from core.config import settings
from app.models.sys.config import ConfigType, ConfigGroup

logger = logging.getLogger(__name__)


class RateLimitConfigProvider:
    _cache: dict[str, Any] = {}
    _expire_at: float = 0.0
    TTL = 30

    @classmethod
    async def get(cls, key: str, default: Any = None) -> Any:
        await cls._ensure_cache()
        return cls._cache.get(key, default)

    @classmethod
    async def get_all(cls) -> dict[str, Any]:
        await cls._ensure_cache()
        return dict(cls._cache)

    @classmethod
    def invalidate(cls) -> None:
        cls._expire_at = 0.0

    @classmethod
    async def _ensure_cache(cls) -> None:
        if time.time() < cls._expire_at:
            return
        try:
            await cls._refresh()
        except Exception as exc:
            logger.error("RateLimitConfigProvider 刷新失败，使用旧缓存或 fallback: %s", exc)

    @classmethod
    async def _refresh(cls) -> None:
        from database import get_session
        from sqlalchemy import select
        from app.models.sys.config import SysConfig

        cache: dict[str, Any] = {}
        async for db in get_session():
            stmt = (
                select(SysConfig)
                .where(SysConfig.group == ConfigGroup.SECURITY)
                .where(SysConfig.key.startswith("rate_limit."))
            )
            result = await db.execute(stmt)
            rows = result.scalars().all()
            for row in rows:
                cache[row.key] = _convert_value(row.value, row.type)
            break

        cls._cache = cache
        cls._expire_at = time.time() + cls.TTL

    @classmethod
    def _fallback_defaults(cls) -> dict[str, Any]:
        cfg = settings.RATE_LIMIT
        return {
            "rate_limit.enabled": cfg.ENABLED,
            "rate_limit.ip_per_minute": cfg.IP_PER_MINUTE,
            "rate_limit.user_per_minute": cfg.USER_PER_MINUTE,
            "rate_limit.login_fail_max": cfg.LOGIN_FAIL_MAX,
            "rate_limit.login_fail_window": cfg.LOGIN_FAIL_WINDOW,
            "rate_limit.login_fail_block_ttl": cfg.LOGIN_FAIL_BLOCK_TTL,
            "rate_limit.blacklist_redis_ttl": cfg.BLACKLIST_REDIS_TTL,
            "rate_limit.captcha_trigger_threshold": cfg.CAPTCHA_TRIGGER_THRESHOLD,
            "rate_limit.captcha_tolerance": cfg.CAPTCHA_TOLERANCE,
            "rate_limit.captcha_token_ttl": cfg.CAPTCHA_TOKEN_TTL,
            "rate_limit.captcha_max_verify_attempts": cfg.CAPTCHA_MAX_VERIFY_ATTEMPTS,
            "rate_limit.whitelist_path_prefixes": list(cfg.WHITELIST_PATH_PREFIXES),
            "rate_limit.whitelist_ips": list(cfg.WHITELIST_IPS),
            "rate_limit.path_rules": [r.model_dump() for r in cfg.PATH_RULES],
        }


def _convert_value(value: str, config_type: ConfigType) -> Any:
    if value is None or value == "":
        return None
    try:
        if config_type == ConfigType.BOOLEAN:
            return value.lower() in ("true", "1", "yes", "on")
        if config_type == ConfigType.NUMBER:
            return float(value) if "." in value else int(value)
        if config_type in (ConfigType.JSON, ConfigType.ARRAY):
            return json.loads(value)
    except (ValueError, json.JSONDecodeError, TypeError):
        pass
    return value
