#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WebSocket / 实时通信连接管理抽象层
业务代码通过此接口推送消息，不感知底层传输协议
后续替换为 Socket.IO / SSE 时只需新增实现类
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Set, Optional, Any
import logging

logger = logging.getLogger(__name__)


class ConnectionManager(ABC):
    """
    实时通信连接管理抽象基类
    所有具体传输实现（WebSocket/SSE/Socket.IO）均需继承此类
    """

    @abstractmethod
    async def connect(
        self,
        connection_id: str,
        websocket: Any,
        user_id: int = 0,
        roles: Optional[List[int]] = None,
    ) -> None:
        """
        注册一个新连接

        Args:
            connection_id: 连接唯一标识
            websocket: 底层连接对象（具体类型由实现决定）
            user_id: 关联用户ID，0 表示匿名
            roles: 用户角色ID列表
        """
        ...

    @abstractmethod
    async def disconnect(self, connection_id: str) -> None:
        """
        断开并清理指定连接

        Args:
            connection_id: 连接唯一标识
        """
        ...

    @abstractmethod
    async def send_to_user(self, user_id: int, message: dict) -> None:
        """
        向指定用户的所有连接推送消息

        Args:
            user_id: 目标用户ID
            message: 消息内容（会被序列化为JSON）
        """
        ...

    @abstractmethod
    async def send_to_users(self, user_ids: List[int], message: dict) -> None:
        """
        向多个指定用户推送消息

        Args:
            user_ids: 目标用户ID列表
            message: 消息内容
        """
        ...

    @abstractmethod
    async def send_to_role(self, role_id: int, message: dict) -> None:
        """
        向具有指定角色的所有在线用户推送消息

        Args:
            role_id: 目标角色ID
            message: 消息内容
        """
        ...

    @abstractmethod
    async def broadcast(self, message: dict) -> None:
        """
        向所有在线连接广播消息

        Args:
            message: 消息内容
        """
        ...

    @abstractmethod
    def get_user_connections(self, user_id: int) -> List[str]:
        """
        获取指定用户的所有连接ID

        Args:
            user_id: 用户ID

        Returns:
            连接ID列表
        """
        ...

    def get_online_user_count(self) -> int:
        """
        获取当前在线用户数（有登录态的连接）

        Returns:
            在线用户数
        """
        return 0
