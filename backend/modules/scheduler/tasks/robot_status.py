#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
机器人状态相关定时任务
"""

import logging
from datetime import timedelta

from sqlalchemy import select

from database.db_manager import get_session
from database.models.business.robot import Robot, RobotStatus
from database.models.business.robot_status_record import RobotStatusRecord
from modules.robot.services.livekit_video_service import LiveKitVideoService
from modules.scheduler.core.registry import scheduled_task

logger = logging.getLogger(__name__)

# 机器人多久未更新状态记录则视为离线（秒）
ROBOT_OFFLINE_TIMEOUT_SECONDS = 60


@scheduled_task(
    interval=30,
    name="机器人自动离线检测",
    description="扫描长时间未上报状态的在线机器人，自动清理视频监控观众（不修改机器人状态）",
    task_key="robot.auto_offline_detection",
    is_system=True,
)
async def auto_offline_detection():
    """
    自动离线检测（只读状态，不修改 Robot.status）。

    对 status=online 的机器人，检查其一对一 status_record 的 updated_at：
    - updated_at 为空，或距今超过 ROBOT_OFFLINE_TIMEOUT_SECONDS，则视为已离线。
    - 调用 LiveKitVideoService.reset_room 清空该机器人的视频观众与房间状态。

    本任务不修改数据库中的机器人状态，仅负责在“心跳已超时但数据库仍是在线”时
    兜底清理视频监控资源。
    """
    from database.utils.timezone import timezone as tz

    now = tz.now()
    timeout_at = now - timedelta(seconds=ROBOT_OFFLINE_TIMEOUT_SECONDS)

    async for db in get_session():
        result = await db.execute(
            select(Robot, RobotStatusRecord)
            .join(RobotStatusRecord, Robot.id == RobotStatusRecord.robot_id)
            .where(
                Robot.status == RobotStatus.ONLINE,
                Robot.deleted_at.is_(None),
                RobotStatusRecord.deleted_at.is_(None),
                (
                    RobotStatusRecord.updated_at.is_(None)
                    | (RobotStatusRecord.updated_at < timeout_at)
                ),
            )
        )
        rows = result.all()

        if not rows:
            return {"status": "ok", "offline_count": 0}

        robot_ids = [robot.id for robot, _ in rows]
        serial_numbers = [robot.serial_number for robot, _ in rows]

        for serial_number in serial_numbers:
            try:
                await LiveKitVideoService.reset_room(serial_number)
            except Exception as exc:
                logger.error(
                    "自动离线清理视频监控失败 serial=%s: %s", serial_number, exc
                )

        logger.info(
            "自动离线检测完成，共 %d 个机器人心跳超时并清理视频观众: %s",
            len(robot_ids),
            robot_ids,
        )
        return {
            "status": "ok",
            "offline_count": len(robot_ids),
            "robot_ids": robot_ids,
        }
