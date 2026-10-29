#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
机器人麦克风蓝牙状态服务层
经 gRPC（agent 端）直连机器人查询/重连蓝牙麦克风：
- 状态文案：已连接 / 未连接 / 未知（机器人不可达、未配置 gRPC、未启用时不拖垮列表展示）
- 重连：机器人不可达或重连失败时抛 ServerError 提示前端
"""
import logging

from core.exception.errors import ServerError
from database.models.business.robot import Robot
from modules.grpc.config_client import MicBluetoothClient

logger = logging.getLogger(__name__)


class RobotMicBluetoothService:
    @staticmethod
    async def get_status(robot: Robot) -> str:
        """
        查询麦克风蓝牙连接状态

        Returns:
            已连接 / 未连接；机器人不可达返回「未知」（不拖垮列表展示）
        """
        resp = await MicBluetoothClient.get_status(robot.id)
        if resp is None:
            return "未知"
        return "已连接" if resp.connected else "未连接"

    @staticmethod
    async def reconnect(robot: Robot) -> str:
        """
        触发蓝牙麦克风重连，返回重连后的状态文案

        Raises:
            ServerError: 机器人不可达（gRPC 未启用/未配置/调用失败）或重连动作失败
        """
        resp = await MicBluetoothClient.reconnect(robot.id)
        if resp is None:
            raise ServerError(msg="机器人当前不可达，请确认机器人在线后重试")
        if not resp.success:
            raise ServerError(msg=resp.message or "麦克风蓝牙重连失败，请稍后重试")
        return "已连接" if resp.connected else "未连接"
