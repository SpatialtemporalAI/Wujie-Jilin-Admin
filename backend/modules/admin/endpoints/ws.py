#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WebSocket 实时通信端点
提供通知推送的 WebSocket 接入点
"""

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from database.models.sys.user import SysUser
from database.models.sys.role import SysRole
from core.security.oauth.jwt import JWTAuthManager
from core.config import settings
from core.exception import TokenError
from database import get_session

logger = logging.getLogger(__name__)

ws_router = APIRouter(prefix="/ws", tags=["WebSocket"])


@ws_router.websocket("/notifications")
async def notification_websocket(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="JWT 认证令牌"),
):
    """
    通知推送 WebSocket 端点

    连接流程：
    1. 从 URL Query 参数获取 token
    2. 解码并验证 JWT session
    3. 查询用户及角色信息
    4. 注册到全局 ConnectionManager
    5. 保持连接，接收心跳/确认消息
    6. 断开时自动清理
    """
    connection_id = str(uuid.uuid4())
    user_id = 0
    role_ids: list = []
    connection_manager = getattr(websocket.app.state, "connection_manager", None)

    if connection_manager is None:
        logger.error("WebSocket 连接失败: connection_manager 未初始化")
        await websocket.close(code=1011, reason="Server error")
        return

    # 认证阶段
    if token:
        try:
            jwt_manager = JWTAuthManager()
            # 兼容 "Bearer <jwt>" 与裸 JWT 两种写法，与 sys/file.py 的 token 解析保持一致
            payload = jwt_manager.decode_token(token.removeprefix("Bearer "))
            session_id = payload.get("session_id")
            _user_id = payload.get("user_id")
            user_role = payload.get("role")

            if not _user_id or not session_id or not user_role:
                await websocket.close(code=1008, reason="Invalid token")
                return

            # 验证 session 有效性
            cache_key = settings.JWT.SESSION_PREFIX + user_role + str(_user_id)
            from core.utils.memory_cache import get_memory_cache, CacheNamespace
            from core.redis import get_redis_util

            _cache = get_memory_cache()
            session_ck = f"{cache_key}:{session_id}"
            cached_valid = _cache.get(CacheNamespace.SESSION, session_ck)
            if cached_valid is None:
                local_session_meta = await get_redis_util().hget(cache_key, session_id)
                if local_session_meta is None:
                    try:
                        local_session_id = await get_redis_util().get(cache_key)
                    except Exception:
                        local_session_id = None
                    if local_session_id is None or local_session_id != session_id:
                        await websocket.close(code=1008, reason="Session expired")
                        return
                    _cache.set(CacheNamespace.SESSION, session_ck, True, ttl=5)
                else:
                    _cache.set(CacheNamespace.SESSION, session_ck, True, ttl=5)

            user_id = int(_user_id)

            # 查询用户角色
            async with get_session() as db:
                result = await db.execute(
                    select(SysUser)
                    .options(joinedload(SysUser.roles))
                    .where(SysUser.id == user_id)
                )
                user = result.unique().scalars().first()
                if user:
                    role_ids = [role.id for role in user.roles if role.status]
                else:
                    await websocket.close(code=1008, reason="User not found")
                    return

        except TokenError:
            await websocket.close(code=1008, reason="Token invalid or expired")
            return
        except Exception as exc:
            logger.warning(f"WebSocket 认证异常: {exc}")
            await websocket.close(code=1008, reason="Authentication failed")
            return
    else:
        # 允许匿名连接，但仅能接收广播消息
        pass

    # 注册连接
    await connection_manager.connect(
        connection_id=connection_id,
        websocket=websocket,
        user_id=user_id,
        roles=role_ids,
    )

    logger.info(f"WebSocket 连接已建立: {connection_id}, user_id={user_id}, roles={role_ids}")

    try:
        while True:
            # 接收客户端消息（心跳或确认）
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong", "data": None})
            elif msg_type == "ack":
                # 客户端确认收到某条通知
                pass
            else:
                # 忽略未知消息类型
                pass

    except WebSocketDisconnect:
        logger.debug(f"WebSocket 客户端主动断开: {connection_id}")
    except Exception as exc:
        logger.warning(f"WebSocket 连接异常: {connection_id}, error={exc}")
    finally:
        await connection_manager.disconnect(connection_id)
        logger.info(f"WebSocket 连接已清理: {connection_id}")
