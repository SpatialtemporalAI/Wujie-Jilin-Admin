#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from modules.scheduler.core.registry import scheduled_task


@scheduled_task(
    interval=25,
    name="刷新限流配置缓存",
    description="定时从数据库刷新限流参数到内存缓存，避免请求路径上回源",
    task_key="system.refresh_rate_limit_config",
    is_system=True,
)
async def refresh_rate_limit_config():
    from core.security.rate_limit_config import RateLimitConfigProvider

    await RateLimitConfigProvider.force_refresh()
    return {"status": "ok"}
