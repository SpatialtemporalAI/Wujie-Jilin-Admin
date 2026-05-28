#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
基于 FastAPI 原生 WebSocket 的连接管理实现
作为 ConnectionManager 的默认实现
"""

from typing import Dict, List, Set, Optional
import logging

from fastapi import WebSocket

from .manager import ConnectionManager

logger = logging.getLogger(__name__)


class FastAPIConnectionManager(ConnectionManager):
    """
    基于 FastAPI 原生 WebSocket 的连接管理实现
    使用内存字典维护连接映射关系
    """

    def __init__(self):
        # connection_id -> {websocket, user_id, roles}
        self._connections: Dict[str, dict] = {}
        # user_id -> Set[connection_id]
        self._user_connections: Dict[int, Set[str]] = {}

    async def connect(
        self,
        connection_id: str,
        websocket: WebSocket,
        user_id: int = 0,
        roles: Optional[List[int]] = None,
    ) -> None:
        """接受 WebSocket 连接并注册到内部映射"""
        await websocket.accept()
        self._connections[connection_id] = {
            "ws": websocket,
            "user_id": user_id,
            "roles": set(roles or []),
        }
        if user_id:
            self._user_connections.setdefault(user_id, set()).add(connection_id)
        logger.debug(f"WebSocket 连接已注册: {connection_id}, user_id={user_id}")

    async def disconnect(self, connection_id: str) -> None:
        """断开并清理连接"""
        conn = self._connections.pop(connection_id, None)
        if conn and conn["user_id"]:
            self._user_connections.get(conn["user_id"], set()).discard(connection_id)
        logger.debug(f"WebSocket 连接已断开: {connection_id}")

    async def send_to_user(self, user_id: int, message: dict) -> None:
        """向指定用户的所有连接发送消息"""
        connection_ids = self._user_connections.get(user_id, set()).copy()
        for cid in connection_ids:
            conn = self._connections.get(cid)
            if conn:
                try:
                    await conn["ws"].send_json(message)
                except Exception as exc:
                    logger.warning(f"向用户 {user_id} 发送消息失败: {exc}")

    async def send_to_users(self, user_ids: List[int], message: dict) -> None:
        """向多个用户发送消息"""
        for uid in user_ids:
            await self.send_to_user(uid, message)

    async def send_to_role(self, role_id: int, message: dict) -> None:
        """向具有指定角色的所有在线用户发送消息"""
        for cid, conn in list(self._connections.items()):
            if role_id in conn.get("roles", set()):
                try:
                    await conn["ws"].send_json(message)
                except Exception as exc:
                    logger.warning(f"向角色 {role_id} 的连接 {cid} 发送消息失败: {exc}")

    async def broadcast(self, message: dict) -> None:
        """向所有在线连接广播消息"""
        for cid, conn in list(self._connections.items()):
            try:
                await conn["ws"].send_json(message)
            except Exception as exc:
                logger.warning(f"广播消息到连接 {cid} 失败: {exc}")

    def get_user_connections(self, user_id: int) -> List[str]:
        """获取指定用户的所有连接ID"""
        return list(self._user_connections.get(user_id, set()))

    def get_online_user_count(self) -> int:
        """获取当前在线用户数"""
        return len(self._user_connections)

    def get_connection_count(self) -> int:
        """获取当前总连接数"""
        return len(self._connections)
