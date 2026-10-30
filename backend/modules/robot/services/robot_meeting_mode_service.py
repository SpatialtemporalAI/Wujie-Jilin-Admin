#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
机器人会议模式服务层
经 gRPC（agent 端）直连机器人手动切换会议模式：
- 切换成功后把最新状态落库（robot.meeting_mode），列表页随 list 接口展示
- 机器人不可达或切换失败时抛 ServerError 提示前端
"""
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from core.exception.errors import ServerError
from database.models.business.robot import Robot
from modules.grpc.config_client import MeetingModeClient

logger = logging.getLogger(__name__)


class RobotMeetingModeService:
    @staticmethod
    async def set_meeting_mode(db: AsyncSession, robot: Robot, enabled: bool) -> bool:
        """
        切换机器人会议模式，返回切换后的最新状态

        Raises:
            ServerError: 机器人不可达（gRPC 未启用/未配置/调用失败）或切换动作失败
        """
        resp = await MeetingModeClient.set_meeting_mode(robot.id, enabled)
        if resp is None:
            raise ServerError(msg="机器人当前不可达，请确认机器人在线后重试")
        if not resp.success:
            raise ServerError(msg=resp.message or "会议模式切换失败，请稍后重试")

        robot.meeting_mode = resp.meeting_mode
        await db.commit()
        return robot.meeting_mode
