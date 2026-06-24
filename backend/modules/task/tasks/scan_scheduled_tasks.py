#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
定时任务：扫描启用了定时调度的任务并触发执行

每分钟扫描所有 schedule_enabled=True 且 enabled=True 的任务，
若当前本地时间命中调度配置：
- 单次模式（无 repeat_cycle 或仅 'none'）：schedule_date + schedule_start_time 精确匹配
- 重复模式（repeat_cycle 含有效星期）：当前星期 ∈ cycle_list 且 today >= schedule_date，且 start_time HH:MM 匹配

命中后按"启动任务"按钮同款逻辑调用 start_or_resume_execution：
- 已有 paused 执行 → 批量恢复
- 无活跃执行 → 新建执行（source=platform_schedule）

依赖模块加载时通过 @scheduled_task 装饰器自动注册到调度注册表，
由 main.py 在应用启动时导入触发注册，再由 seed_scheduler 同步到 DB。
"""
import logging
from datetime import date, datetime, time

from sqlalchemy import select

from database.models.business.task import Task, task_robot_association
from database.utils.timezone import timezone
from modules.scheduler.core.registry import scheduled_task

logger = logging.getLogger(__name__)

WEEKDAY_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def _is_schedule_due(task_obj: Task, now: datetime) -> bool:
    """判断任务调度是否在当前时间命中。

    匹配规则：
    - schedule_date 和 schedule_start_time 必须同时配置
    - schedule_start_time 的 HH:MM 等于当前 HH:MM（精确到分钟）
    - 若 schedule_repeat_cycle 为空或仅含 'none'：单次模式，schedule_date 必须等于今天
    - 若 schedule_repeat_cycle 含有效星期：重复模式，当前星期 ∈ cycle_list 且 today >= schedule_date
    """
    start_time: time | None = task_obj.schedule_start_time
    schedule_date: date | None = task_obj.schedule_date

    if start_time is None or schedule_date is None:
        return False

    if start_time.strftime("%H:%M") != now.strftime("%H:%M"):
        return False

    repeat_cycle: str | None = task_obj.schedule_repeat_cycle
    cycle_list: list[str] = []
    if repeat_cycle:
        cycle_list = [
            w.strip().lower()
            for w in repeat_cycle.split(",")
            if w.strip() and w.strip().lower() != "none"
        ]

    # 单次模式：date 必须等于今天
    if not cycle_list:
        return schedule_date == now.date()

    # 重复模式：当前星期 ∈ cycle_list 且 起始日约束 today >= schedule_date
    current_weekday = WEEKDAY_KEYS[now.weekday()]
    if current_weekday not in cycle_list:
        return False

    return now.date() >= schedule_date


@scheduled_task(
    cron="* * * * *",
    name="扫描定时调度任务",
    description="每分钟扫描启用了定时调度的任务，命中调度时间则按启动按钮逻辑恢复或新建执行",
    task_key="task.scan_scheduled_tasks",
    is_system=True,
    concurrent_policy="skip",
)
async def scan_scheduled_tasks():
    """每分钟扫描调度任务，命中则恢复或新建执行"""
    from database.db_manager import get_session
    from modules.task.services.task_execution_record_service import (
        TaskExecutionRecordService,
    )

    now = timezone.now()
    stats = {
        "scanned": 0,
        "due": 0,
        "started": 0,
        "resumed": 0,
        "skipped": 0,
        "failed": 0,
    }

    # 第一阶段：扫描所有候选任务，筛选命中调度的 task_id
    due_task_ids: list[int] = []
    async for db in get_session():
        stmt = select(Task).where(
            Task.schedule_enabled == True,  # noqa: E712
            Task.enabled == True,  # noqa: E712
            Task.deleted_at.is_(None),
        )
        result = await db.execute(stmt)
        tasks = result.scalars().all()
        stats["scanned"] = len(tasks)
        for task_obj in tasks:
            try:
                if _is_schedule_due(task_obj, now):
                    due_task_ids.append(task_obj.id)
            except Exception as exc:
                logger.warning(
                    "任务 %s 调度命中判断异常: %s", task_obj.id, exc
                )

    stats["due"] = len(due_task_ids)
    if not due_task_ids:
        return stats

    # 第二阶段：为每个命中任务单独开 session 处理，避免互相影响
    for task_id in due_task_ids:
        try:
            async for db in get_session():
                robot_ids_result = await db.execute(
                    select(task_robot_association.c.robot_id).where(
                        task_robot_association.c.task_id == task_id
                    )
                )
                robot_ids = [row[0] for row in robot_ids_result.all()]

                if not robot_ids:
                    logger.warning(
                        "调度命中任务 %s 但未关联任何机器人，跳过", task_id
                    )
                    stats["skipped"] += 1
                    continue

                outcome = (
                    await TaskExecutionRecordService.start_or_resume_execution(
                        db=db,
                        task_id=task_id,
                        robot_ids=robot_ids,
                        user_id=None,
                        source="platform_schedule",
                    )
                )
                if outcome["action"] == "resumed":
                    stats["resumed"] += int(outcome["count"])
                    logger.info(
                        "调度命中: 恢复任务 task_id=%s 执行数=%s",
                        task_id,
                        outcome["count"],
                    )
                else:
                    stats["started"] += int(outcome["count"])
                    logger.info(
                        "调度命中: 新建任务 task_id=%s 执行数=%s",
                        task_id,
                        outcome["count"],
                    )
        except Exception as exc:
            stats["failed"] += 1
            logger.error(
                "调度触发任务 %s 失败: %s",
                task_id,
                exc,
                exc_info=True,
            )

    return stats
