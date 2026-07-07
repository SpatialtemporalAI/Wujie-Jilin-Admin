#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
导出任务相关定时任务

1. recover_stuck_export_tasks：每分钟扫描卡在 pending 超过阈值的导出任务，原子领取后重新生成。
   用于补偿 worker 回收/崩溃导致 asyncio 即时触发生成协程丢失、任务永卡 pending 的问题。
2. expire_timeout_export_tasks：每分钟扫描 processing 超过阈值的任务，删除残留文件并标记 expired。

两个任务都 cron 每分钟执行、concurrent_policy=skip（配合 APScheduler max_instances=1
保证单 worker 内不并发）；多 worker 间通过 _execute_task 内的原子领取保证不重复生成。

依赖模块加载时通过 @scheduled_task 装饰器自动注册到调度注册表，
由 main.py 在应用启动时导入触发注册，再由 seed_scheduler 同步到 DB。
"""
import logging
import os
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from database.models.sys.export_task import SysExportTask
from modules.admin.services.sys.export_task_service import (
    ExportTaskService,
    EXPORT_TIMEOUT_SECONDS,
    RECOVER_PENDING_AGE_SECONDS,
)
from modules.scheduler.core.registry import scheduled_task

logger = logging.getLogger(__name__)

# 每次兜底扫描最多处理的任务数，避免一次捞太多压垮 DB/内存
RECOVER_BATCH_LIMIT = 50


@scheduled_task(
    cron="* * * * *",
    name="补偿生成卡住的导出任务",
    description=f"每分钟扫描 pending 超过 {RECOVER_PENDING_AGE_SECONDS}s 的导出任务，原子领取后重新生成",
    task_key="admin.recover_stuck_export_tasks",
    is_system=True,
    concurrent_policy="skip",
    timeout=900,
)
async def recover_stuck_export_tasks():
    """补偿生成卡在 pending 的孤儿导出任务"""
    from database.db_manager import get_session

    cutoff = datetime.now(timezone.utc) - timedelta(seconds=RECOVER_PENDING_AGE_SECONDS)
    stuck_ids: list[int] = []

    async for db in get_session():
        stmt = (
            select(SysExportTask.id)
            .where(
                SysExportTask.status == "pending",
                SysExportTask.created_at < cutoff,
            )
            .order_by(SysExportTask.created_at.asc())
            .limit(RECOVER_BATCH_LIMIT)
        )
        result = await db.execute(stmt)
        stuck_ids = [row[0] for row in result.all()]

    recovered = 0
    for tid in stuck_ids:
        try:
            # _execute_task 自带 session，内部用原子 UPDATE 领取，多 worker 安全
            await ExportTaskService._execute_task(tid)
            recovered += 1
        except Exception as exc:
            logger.error("补偿导出任务 %s 异常: %s", tid, exc)

    if stuck_ids:
        logger.info(
            "export recover scan done scanned=%s recovered=%s",
            len(stuck_ids),
            recovered,
        )
    return {"scanned": len(stuck_ids), "recovered": recovered}


@scheduled_task(
    cron="* * * * *",
    name="清理超时的导出任务",
    description=f"每分钟扫描 processing 超过 {EXPORT_TIMEOUT_SECONDS}s 的任务，删除残留文件并标记 expired",
    task_key="admin.expire_timeout_export_tasks",
    is_system=True,
    concurrent_policy="skip",
    timeout=120,
)
async def expire_timeout_export_tasks():
    """将长时间处于 processing 的导出任务标记为超时失效，并删除残留文件"""
    from database.db_manager import get_session

    expired = 0
    async for db in get_session():
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=EXPORT_TIMEOUT_SECONDS)
        stmt = select(SysExportTask).where(
            SysExportTask.status == "processing",
            SysExportTask.started_at < cutoff,
        )
        result = await db.execute(stmt)
        tasks = result.scalars().all()

        now = datetime.now(timezone.utc)
        for task in tasks:
            # 删除残留文件（processing 超时通常文件尚未写完，此处做兜底）
            if task.file_path and os.path.exists(task.file_path):
                try:
                    os.remove(task.file_path)
                except OSError as exc:
                    logger.warning("删除导出任务 %s 残留文件失败: %s", task.id, exc)
            task.status = "expired"
            task.error_message = "导出超时已失效"
            task.finished_at = now
            expired += 1

        await db.commit()

    if expired:
        logger.info("export expire scan done expired=%s", expired)
    return {"expired": expired}
