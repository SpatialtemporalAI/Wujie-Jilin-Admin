#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
机器人服务器自启动状态服务层
通过 HTTP 调用机器人控制面板（查询/重启 zenoh、middleware、大脑层）
接口约定见《接口说明_服务器自启动状态_Back.md》：
- GET  {BASE}/api/slot-status?robot_id=...&serial_number=... -> {"status": "已启动|启动中|启动失败"}
- POST {BASE}/api/slot-restart  body {"robot_id": "...", "serial_number": "..."} -> 同上
"""
import logging

import httpx

from core.config import settings
from core.exception.errors import ServerError
from database.models.business.robot import Robot

logger = logging.getLogger(__name__)


def _panel_ids(robot: Robot) -> dict:
    """面板要求的标识：robot_id + serial_number，每次必带且必须同一台"""
    return {"robot_id": str(robot.id), "serial_number": robot.serial_number}


class RobotSlotService:
    @staticmethod
    async def get_slot_status(robot: Robot) -> str:
        """
        查询服务器自启动状态

        Returns:
            面板返回的 status（已启动/启动中/启动失败）；
            面板地址未配置返回「未配置」，网络异常返回「未知」（不拖垮列表展示）
        """
        base_url = settings.ROBOT_PANEL.BASE_URL
        if not base_url:
            return "未配置"
        try:
            # trust_env=False：面板是内网地址，不能走进程环境里的 HTTP/SOCKS 代理
            async with httpx.AsyncClient(
                timeout=settings.ROBOT_PANEL.TIMEOUT_SECONDS, trust_env=False
            ) as client:
                resp = await client.get(
                    f"{base_url}/api/slot-status", params=_panel_ids(robot)
                )
                resp.raise_for_status()
                return resp.json().get("status", "未知")
        except Exception as exc:
            logger.warning(
                "查询机器人 %s 服务器自启动状态失败: %s", robot.id, exc
            )
            return "未知"

    @staticmethod
    async def restart_slot(robot: Robot) -> str:
        """
        触发面板按序补齐 zenoh -> middleware，返回重启后的 status

        Raises:
            ServerError: 面板地址未配置或网络异常
        """
        base_url = settings.ROBOT_PANEL.BASE_URL
        if not base_url:
            raise ServerError(msg="机器人控制面板地址未配置，请联系管理员")
        try:
            # trust_env=False：面板是内网地址，不能走进程环境里的 HTTP/SOCKS 代理
            async with httpx.AsyncClient(
                timeout=settings.ROBOT_PANEL.TIMEOUT_SECONDS, trust_env=False
            ) as client:
                resp = await client.post(
                    f"{base_url}/api/slot-restart", json=_panel_ids(robot)
                )
                resp.raise_for_status()
                return resp.json().get("status", "未知")
        except Exception as exc:
            logger.error("重启机器人 %s 服务器自启动失败: %s", robot.id, exc)
            raise ServerError(msg="重启服务器自启动失败，请稍后重试") from exc
