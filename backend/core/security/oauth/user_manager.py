#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from core.config import settings
from core.redis import get_redis_util
from core.security.oauth.jwt import JWTAuthManager
from core.utils.session_utils import generate_session_id
from datetime import datetime, timezone

import logging

logger = logging.getLogger(__name__)


def build_session_key(role: str, user_id: int, tenant_id: int = 0) -> str:
    """构建 Redis session key。

    - admin: JWT_SESSION:ADMIN:{tenant_id}:{user_id}
    - app:   JWT_SESSION:APP:{user_id}
    """
    prefix = settings.JWT.SESSION_PREFIX
    if role == "admin":
        return f"{prefix}ADMIN:{tenant_id}:{user_id}"
    return f"{prefix}{role.upper()}:{user_id}"


def build_session_key_legacy(role: str, user_id: int) -> str:
    """构建旧格式 Redis session key（兼容过渡期）"""
    return settings.JWT.SESSION_PREFIX + role + str(user_id)


class BaseUserManager:
    """
    基础用户管理器类
    包含所有服务共享的用户管理功能
    """

    jwt_manager: JWTAuthManager

    def __init__(self):
        self.jwt_manager = JWTAuthManager()

    async def create_token(
        self,
        user_id: int,
        user_role: str = "app",
        session_id: str = None,
        username: str = None,
        ip: str = "",
        user_agent: str = "",
        tenant_id: int = 0,
    ):
        """
        创建token，使用 Redis Hash 存储会话元数据以支持多会话追踪
        """
        new_session = False
        if session_id is None:
            session_id = generate_session_id(user_id)
            new_session = True
        token_data = {"id": user_id, "session_id": session_id, "role": user_role, "username": username}
        if new_session:
            redis_key = build_session_key(user_role, user_id, tenant_id=tenant_id)

            # 清理旧格式 key（兼容过渡）
            legacy_key = build_session_key_legacy(user_role, user_id)
            await get_redis_util().delete(legacy_key)

            # 清理同用户其他 tenant_id 的旧 key（仅 admin）
            if user_role == "admin" and tenant_id != 0:
                old_key = build_session_key(user_role, user_id, tenant_id=0)
                if old_key != redis_key:
                    await get_redis_util().delete(old_key)

            session_meta = json.dumps({
                "session_id": session_id,
                "login_time": datetime.now(timezone.utc).isoformat(),
                "ip": ip,
                "user_agent": user_agent,
            })
            await get_redis_util().hset(redis_key, session_id, session_meta)
            await get_redis_util().expire(redis_key, settings.JWT.REFRESH_LIFETIME)
        tokens = JWTAuthManager.create_tokens(token_data)
        return tokens


base_user_manager = BaseUserManager()
