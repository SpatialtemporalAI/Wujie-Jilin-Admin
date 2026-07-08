#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
定时任务：重试失败的 gRPC 推送

每分钟扫描 grpc_retry_task 表中 status=pending 且 next_retry_at <= now() 的任务，
按 service_name + method_name 路由到对应 client 方法重试：
- 成功 → status=completed
- 失败且 retry_count < max_retries → retry_count++，next_retry_at 按指数退避延后
- 失败且 retry_count >= max_retries → status=dead

依赖模块加载时通过 @scheduled_task 装饰器自动注册到调度注册表，
由 main.py 在应用启动时导入触发注册，再由 seed_scheduler 同步到 DB。
"""
import logging

from modules.grpc.retry_service import GrpcRetryService
from modules.scheduler.core.registry import scheduled_task

logger = logging.getLogger(__name__)


@scheduled_task(
    cron="* * * * *",
    name="重试失败的 gRPC 推送",
    description="每分钟扫描 grpc_retry_task 表中到期任务，先检测机器人在线，在线才推送；成功置 completed，离线等待，失败按指数退避延后或标记 dead",
    task_key="grpc.retry_failed_pushes",
    is_system=True,
    concurrent_policy="skip",
    # 单条重试硬超时 30s × limit 50 = 1500s，外加 DB 开销，留余量到 1600s
    # 原默认 300s 会在 pending 任务 ≥ 10 个时被外层 wait_for 强制 cancel，
    # 导致内层 _advance_fields 没机会跑、retry_count 永远为 0
    timeout=1600,
)
async def retry_failed_pushes():
    from database.db_manager import get_session

    async for db in get_session():
        stats = await GrpcRetryService.run_pending_once(db, limit=50)
        logger.info(
            "grpc retry scan done scanned=%s completed=%s rescheduled=%s dead=%s waiting_online=%s cancelled=%s",
            stats.get("scanned", 0),
            stats.get("completed", 0),
            stats.get("rescheduled", 0),
            stats.get("dead", 0),
            stats.get("waiting_online", 0),
            stats.get("cancelled", 0),
        )
        return stats
