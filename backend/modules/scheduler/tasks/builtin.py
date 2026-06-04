#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
内置系统定时任务
通过 @scheduled_task 装饰器注册，安装插件时自动同步到数据库
"""

from sqlalchemy import delete, text
from datetime import datetime, timedelta, timezone

from modules.scheduler.core.registry import scheduled_task


@scheduled_task(
    cron="0 3 * * *",
    name="清理过期操作日志",
    description="自动清理30天前的操作日志",
    task_key="system.cleanup_operation_logs",
    is_system=True,
)
async def cleanup_operation_logs():
    """清理过期操作日志"""
    from database.db_manager import get_session
    from database.models.sys.operation_log import SysOperationLog

    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    total = 0
    async for db in get_session():
        stmt = delete(SysOperationLog).where(SysOperationLog.created_at < cutoff)
        result = await db.execute(stmt)
        await db.commit()
        total = result.rowcount
    return {"deleted": total}


@scheduled_task(
    cron="0 4 * * *",
    name="清理过期登录日志",
    description="自动清理30天前的登录日志",
    task_key="system.cleanup_login_logs",
    is_system=True,
)
async def cleanup_login_logs():
    """清理过期登录日志"""
    from database.db_manager import get_session
    from database.models.sys.login_log import SysLoginLog

    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    total = 0
    async for db in get_session():
        stmt = delete(SysLoginLog).where(SysLoginLog.created_at < cutoff)
        result = await db.execute(stmt)
        await db.commit()
        total = result.rowcount
    return {"deleted": total}
