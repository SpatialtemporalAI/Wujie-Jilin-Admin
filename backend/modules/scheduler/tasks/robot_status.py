#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
机器人状态相关定时任务
"""

import logging

from sqlalchemy import select

from core.redis.redis_pool import RedisPool
from database.db_manager import get_session
from database.models.business.robot import Robot, RobotStatus
from modules.robot.services.livekit_video_service import LiveKitVideoService
from modules.scheduler.core.registry import scheduled_task

logger = logging.getLogger(__name__)

# Redis key：记录上一次任务执行时在线的机器人序列号集合
_ONLINE_ROBOTS_SET_KEY = "wj:livekit:online_robots"


@scheduled_task(
    interval=30,
    name="机器人自动离线检测",
    description="检测机器人 status 由 online 变为非 online 的状态转换，并清理视频监控观众",
    task_key="robot.auto_offline_detection",
    is_system=True,
)
async def auto_offline_detection():
    """
    自动离线检测（只读 Robot.status，不修改状态）。

    每次执行时：
    1. 从数据库读取所有未删除机器人的 id + serial_number + status；
    2. 与 Redis 中保存的“上一轮在线机器人序列号集合”对比；
    3. 对“上一轮在线、当前不在线”的机器人，调用 reset_room 清空视频观众；
    4. 把当前在线集合写回 Redis，供下一轮对比。

    本任务不修改数据库中的机器人状态，只负责在 status 从 online 转离线时
    兜底清理视频监控资源。
    """
    async for db in get_session():
        result = await db.execute(
            select(Robot.id, Robot.serial_number, Robot.status).where(
                Robot.deleted_at.is_(None)
            )
        )
        rows = result.all()

        current_online_serials = {
            serial_number
            for _, serial_number, status in rows
            if status == RobotStatus.ONLINE
        }

        client = RedisPool.get_client()
        try:
            previous_online_serials = await client.smembers(_ONLINE_ROBOTS_SET_KEY)
            previous_online_serials = {
                s.decode() if isinstance(s, bytes) else s
                for s in (previous_online_serials or set())
            }
        except Exception as exc:
            logger.error("读取上一轮在线机器人集合失败: %s", exc)
            previous_online_serials = set()

        went_offline = previous_online_serials - current_online_serials

        for serial_number in went_offline:
            try:
                await LiveKitVideoService.reset_room(serial_number)
                logger.info(
                    "机器人状态由在线转离线，已清空视频监控观众 serial=%s",
                    serial_number,
                )
            except Exception as exc:
                logger.error(
                    "自动离线清理视频监控失败 serial=%s: %s", serial_number, exc
                )

        try:
            if current_online_serials:
                await client.delete(_ONLINE_ROBOTS_SET_KEY)
                await client.sadd(
                    _ONLINE_ROBOTS_SET_KEY, *current_online_serials
                )
            else:
                await client.delete(_ONLINE_ROBOTS_SET_KEY)
        except Exception as exc:
            logger.error("保存当前在线机器人集合失败: %s", exc)

        return {
            "status": "ok",
            "went_offline_count": len(went_offline),
            "went_offline_serials": sorted(went_offline),
            "current_online_count": len(current_online_serials),
        }
