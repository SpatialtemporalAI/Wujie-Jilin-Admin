#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from typing import Optional, Any
from core.redis import get_redis_util
from core.config import settings
from core.security.oauth.jwt import JWTAuthManager
from core.utils.session_utils import generate_session_id
from datetime import datetime, timezone

import logging

logger = logging.getLogger(__name__)


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
            redis_key = settings.JWT.SESSION_PREFIX + user_role + str(token_data.get("id"))
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
