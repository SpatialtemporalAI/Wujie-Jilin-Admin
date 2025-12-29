#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional, Generic, TypeVar, Any
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_conn
from core.redis import get_redis_util
from core.config import settings
from core.security.oauth.jwt import JWTAuthManager, Token, oauth2_scheme

from core.utils.session_utils import generate_session_id
from fastapi import Request
from logging import getLogger

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

    async def on_after_login(
        self,
        user: AppUser,
        request: Optional[Request] = None,
        response: Optional[Any] = None,
    ):
        """
        用户登录后的回调
        可以在这里实现用户登录后的额外逻辑，如更新最后登录时间、记录登录IP等
        Args:
            user: 登录的用户对象
            request: 请求对象（可选）
            response: 响应对象（可选）
        """
        logger.info(f"用户 {user.id} 登录成功")
        # 这里可以添加登录成功后的逻辑，如更新登录时间、记录登录IP等


base_user_manager = BaseUserManager()
