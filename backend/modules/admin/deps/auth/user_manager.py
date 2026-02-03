#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional, Union, Dict, Any, Tuple
from fastapi import Depends, Request

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.config import settings
from app.models.sys.user import SysUser
from database import get_session
import hashlib
from core.exception import CustomError, TokenError
from core.response import CustomErrorCode
from core.security.oauth.user_manager import base_user_manager
from core.security.oauth.jwt import JWTAuthManager, Token, oauth2_scheme
from core.redis import get_redis_util


class UserManager:
    """
    用户管理器类
    负责用户的创建、认证、密码重置等操作
    """

    jwt_manager: JWTAuthManager

    def __init__(self, session: AsyncSession):
        self.session = session
        self.jwt_manager = JWTAuthManager()

    async def login_by_password(
        self, username: str, password: str
    ) -> Optional[Dict[str, str]]:
        """
        密码登录
        """
        if not username or not password:
            raise CustomError(
                msg="用户名和密码不能为空",
                error=CustomErrorCode.USER_LOGIN_FAILED,
            )
        stmt = select(SysUser).where(SysUser.username == username)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise CustomError(
                msg="用户名不存在",
                error=CustomErrorCode.USER_LOGIN_FAILED,
            )
        sha_id = hashlib.sha256(password.encode("utf-8")).hexdigest()
        if sha_id != user.password:
            raise CustomError(
                msg="密码错误",
                error=CustomErrorCode.USER_LOGIN_FAILED,
            )
        # 生成JWT令牌
        tokens = await base_user_manager.create_token(
            user_id=user.id, user_role="admin"
        )
        await base_user_manager.on_after_login(user=user)
        response_model = {
            **tokens.model_dump(),
        }
        return response_model

    async def current_user(self, token: str) -> SysUser:
        """
        获取当前认证的用户
        这是一个直接可用的FastAPI依赖项，封装了JWTAuthManager.current_user方法，
        用于在路由处理函数中验证并获取当前已认证的用户信息。
        Args:
            token: 通过OAuth2密码流程获取的JWT令牌
            db: 数据库会话依赖
        Returns:
            AppUser: 当前认证用户的数据库模型实例
        """
        user_id, _ = await self.verify_token_session(token)
        user = await self.session.execute(select(SysUser).where(SysUser.id == user_id))
        user = user.scalars().first()
        if user is None:
            raise TokenError()
        return user

    async def verify_token_session(
        self, token: str, _type: str = "access"
    ) -> Tuple[int, str]:
        """
        验证token中的session_id是否有效
        Args:
            token: JWT令牌
        Returns:
            user_id: 用户id
            session_id: 会话id
        """
        payload = self.jwt_manager.decode_token(token)
        session_id = payload.get("session_id")
        user_id = payload.get("user_id")
        user_role = payload.get("role")
        if payload.get("scope") != _type:
            raise TokenError()
        if not user_id:
            raise TokenError()
        if not session_id:
            raise TokenError()
        if not user_role:
            raise TokenError()
        local_session_id = await get_redis_util().get(
            settings.JWT.SESSION_PREFIX + user_role + str(user_id)
        )
        if local_session_id != session_id:
            raise TokenError()
        if user_id is None:
            raise TokenError()
        return int(user_id), session_id

    async def get_user_info(self, user_id: int):
        """
        获取用户信息
        将SysUser模型转换为符合UserInfoResponseData模型的字典，
        并处理datetime类型到str类型的转换
        Args:
            user_id: 用户ID
        Returns:
            dict: 符合UserInfoResponseData模型的用户信息字典
        """
        stmt = select(SysUser).where(SysUser.id == user_id)
        result = await self.session.execute(stmt)
        user = result.scalars().first()
        if not user:
            raise CustomError(
                error=CustomErrorCode.USER_NOT_FOUND,
            )

        # 转换为字典并处理datetime类型
        def format_datetime(dt):
            if dt:
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            return None

        user_info = {
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "email": user.email,
            "phone": user.phone,
            "avatar": user.avatar,
            "is_superuser": user.is_superuser,
            "status": user.status,
            "last_login_at": format_datetime(user.last_login_at),
            "last_login_ip": user.last_login_ip,
        }
        return user_info


async def get_user_manager(user_db: AsyncSession = Depends(get_session)):
    """
    获取用户管理器实例
    Args:
        user_db: 用户数据库实例
    Yields:
        UserManager: 用户管理器实例
    """
    yield UserManager(user_db)


async def current_user(
    token: str = Depends(oauth2_scheme),
    user_manager: UserManager = Depends(get_user_manager),
) -> SysUser:
    """
    获取当前认证用户的数据库模型实例
    Args:
        user_manager: 用户管理器实例
        token: 通过OAuth2密码流程获取的JWT令牌
    Returns:
        SysUser: 当前认证用户的数据库模型实例
    """
    return await user_manager.current_user(token)


# # 定义认证后端
# bearer_transport = BearerTransport(tokenUrl="/admin/auth/login")
# # 只显示需要修改的部分
# def get_redis_strategy(
#     redis_client: Redis = Depends(get_redis_client),
# ) -> RedisStrategy:
#     """
#     获取Redis策略实例
#     使用Redis连接池和设置中的密钥和过期时间
#     Returns:
#         RedisStrategy: Redis策略实例
#     """
#     return RedisStrategy(
#         redis_client, lifetime_seconds=3600, key_prefix="sys_user_token:")
# # 创建认证后端实例
# auth_backend = AuthenticationBackend(
#     name="redis",
#     transport=bearer_transport,
#     get_strategy=get_redis_strategy,
# )
