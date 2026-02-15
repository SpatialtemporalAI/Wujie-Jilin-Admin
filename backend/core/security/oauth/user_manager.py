#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from optparse import Option
from typing import Optional, Generic, TypeVar, Any
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_session
from core.redis import get_redis_util
from core.config import settings
from core.security.oauth.jwt import JWTAuthManager, Token, oauth2_scheme
from app.models.business.user import AppUser

from core.utils.session_utils import generate_session_id
from fastapi import Request
from logging import getLogger
from datetime import datetime, timedelta, timezone

logger = getLogger(__name__)


class BaseUserManager:
    """
    基础用户管理器类
    包含所有服务共享的用户管理功能
    """

    jwt_manager: JWTAuthManager

    def __init__(self):
        self.jwt_manager = JWTAuthManager()

    async def create_token(
        self, user_id: int, user_role: str = "app", session_id: str = None
    ):
        """
        创建token
        """
        new_session = False
        if session_id is None:
            session_id = generate_session_id(user_id)
            new_session = True
        # 使用JWTAuthManager创建令牌
        token_data = {"id": user_id, "session_id": session_id, "role": user_role}
        if new_session:
            # 保存session_id到redis - 添加用户角色区分
            await get_redis_util().set(
                settings.JWT.SESSION_PREFIX + user_role + str(token_data.get("id")),
                token_data.get("session_id"),
                settings.JWT.REFRESH_LIFETIME,
            )
        tokens = JWTAuthManager.create_tokens(token_data)
        return tokens


base_user_manager = BaseUserManager()
