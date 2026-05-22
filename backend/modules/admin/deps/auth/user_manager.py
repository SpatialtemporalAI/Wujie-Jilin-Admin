#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional, Union, Dict, Any, Tuple, List
from fastapi import Depends, Request

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from core.config import settings
from app.models.sys.user import SysUser
from app.models.sys.role import SysRole
from app.models.sys.menu import SysMenu, MenuType
from database import get_session
from core.exception import CustomError, TokenError
from core.response import CustomErrorCode
from core.security.oauth.user_manager import base_user_manager, BaseUserManager
from core.security.oauth.jwt import JWTAuthManager, Token, oauth2_scheme
from core.security.password import PasswordHasher
from core.redis import get_redis_util
from core.middleware.share_middleware import request_ctx
from core.utils.ip_utils import get_real_client_ip
from core.utils.session_cache import get_session_cache
from datetime import datetime, timedelta, timezone


import logging

logger = logging.getLogger(__name__)


class UserManager(BaseUserManager):
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

        pwd_match = PasswordHasher.verify(
            password=password,
            hashed_password=user.password,
        )

        if not pwd_match:
            raise CustomError(
                msg="密码错误",
                error=CustomErrorCode.USER_LOGIN_FAILED,
            )
        # 生成JWT令牌
        tokens = await self.create_token(user_id=user.id, user_role="admin", username=user.username)
        await self.on_after_login(user=user)
        response_model = {
            **tokens.model_dump(),
        }
        await self.session.commit()
        return response_model

    async def on_after_login(self, user: SysUser):
        """
        用户登录后的回调
        可以在这里实现用户登录后的额外逻辑，如更新最后登录时间、记录登录IP等
        Args:
            user: 登录的用户对象
            request: 请求对象（可选）
            response: 响应对象（可选）
        """
        logger.info(f"用户 {user.id} 登录成功")

        request: Request = request_ctx.get()

        if request is not None:
            # 这里可以添加登录成功后的逻辑，如更新登录时间、记录登录IP等
            user.last_login_ip = get_real_client_ip(request)
            user.last_login_at = datetime.now(timezone.utc)

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
        # 优先复用中间件已解码的 JWT payload，避免重复解码
        request: Request = request_ctx.get()
        cached_payload = None
        if request is not None:
            cached_payload = getattr(request.state, "_jwt_payload", None)
            cached_token = getattr(request.state, "_jwt_raw_token", None)
            if cached_token != token:
                cached_payload = None

        payload = cached_payload if cached_payload is not None else self.jwt_manager.decode_token(token)
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
        cache_key = settings.JWT.SESSION_PREFIX + user_role + str(user_id)
        cached_session_id = get_session_cache().get(cache_key)
        if cached_session_id is not None:
            if cached_session_id != session_id:
                raise TokenError()
        else:
            local_session_id = await get_redis_util().get(cache_key)
            if local_session_id != session_id:
                raise TokenError()
            if local_session_id is not None:
                get_session_cache().set(cache_key, local_session_id)
        if user_id is None:
            raise TokenError()
        return int(user_id), session_id

    async def get_user_info(self, user_id: int):
        """
        获取用户信息，包含角色列表和按钮权限列表
        Args:
            user_id: 用户ID
        Returns:
            dict: 用户信息字典，含 roles 和 buttons
        """
        stmt = (
            select(SysUser)
            .options(joinedload(SysUser.roles).joinedload(SysRole.menus))
            .where(SysUser.id == user_id)
        )
        result = await self.session.execute(stmt)
        user = result.unique().scalars().first()
        if not user:
            raise CustomError(
                error=CustomErrorCode.USER_NOT_FOUND,
            )

        def format_datetime(dt):
            if dt:
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            return None

        # 收集角色 code 列表
        roles: List[str] = [role.code for role in user.roles if role.status]

        # 收集按钮权限：通过角色 → 关联菜单 → 筛选 type=BUTTON → 提取 permission 字段
        buttons: List[str] = []
        if user.is_superuser:
            # 超级用户获取所有按钮权限
            btn_stmt = select(SysMenu).where(
                SysMenu.type == MenuType.BUTTON,
                SysMenu.status == True,
            )
            btn_result = await self.session.execute(btn_stmt)
            buttons = [
                m.permission for m in btn_result.scalars().all() if m.permission
            ]
        else:
            seen = set()
            for role in user.roles:
                if not role.status:
                    continue
                for menu in role.menus:
                    if (
                        menu.type == MenuType.BUTTON
                        and menu.status
                        and menu.permission
                        and menu.permission not in seen
                    ):
                        seen.add(menu.permission)
                        buttons.append(menu.permission)

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
            "roles": roles,
            "buttons": buttons,
        }
        return user_info


async def get_user_manager(
    user_db: AsyncSession = Depends(get_session),
):
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
