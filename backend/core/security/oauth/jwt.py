#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, TypeVar
import jwt
import logging
from fastapi import HTTPException, status
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError, DecodeError
from pydantic import BaseModel
from core.config import settings
from fastapi.security import OAuth2PasswordBearer
from pydantic import Field


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
token_type = "Bearer"

logger = logging.getLogger(__name__)


class TokenData(BaseModel):
    """JWT令牌数据模型"""

    username: Optional[str] = Field(None, description="用户名")
    user_id: Optional[str] = Field(None, description="用户ID")
    scope: Optional[str] = Field(None, description="令牌作用域")


class Token(BaseModel):
    """令牌响应模型"""

    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(..., description="令牌类型")
    expires_in: int = Field(..., description="令牌过期时间（秒）")
    refresh_token: str = Field(..., description="刷新令牌")


# 定义用户模型类型变量
t = TypeVar("T")


class JWTAuthManager:
    """JWT认证管理器"""

    @classmethod
    def create_access_token(
        cls, data: Dict[str, Any], expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        创建访问令牌
        Args:
            data: 要编码的数据
            expires_delta: 过期时间增量
        Returns:
            str: 编码后的JWT令牌
        """
        try:
            to_encode = data.copy()
            # 设置过期时间
            if expires_delta:
                expire = datetime.now(timezone.utc) + expires_delta
            else:
                expire = datetime.now(timezone.utc) + timedelta(
                    seconds=settings.JWT.ACCESS_LIFETIME
                )
            to_encode.update(
                {
                    "exp": expire,
                    "iat": datetime.now(timezone.utc),
                    "aud": settings.JWT.AUDIENCE,
                    "iss": "spatialtemporal-ai-cloud",
                }
            )
            encoded_jwt = jwt.encode(
                to_encode, settings.JWT.SECRET_KEY, algorithm=settings.JWT.ALGORITHM
            )
            return encoded_jwt
        except Exception as e:
            logger.exception("创建访问令牌异常: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="令牌创建失败"
            )

    @classmethod
    def create_refresh_token(
        cls, data: Dict[str, Any], expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        创建刷新令牌
        Args:
            data: 要编码的数据
            expires_delta: 过期时间增量
        Returns:
            str: 编码后的刷新令牌
        """
        try:
            to_encode = data.copy()
            # 设置过期时间，通常刷新令牌有效期更长
            if expires_delta:
                expire = datetime.now(timezone.utc) + expires_delta
            else:
                expire = datetime.now(timezone.utc) + timedelta(
                    seconds=settings.JWT.REFRESH_LIFETIME
                )
            to_encode.update(
                {
                    "exp": expire,
                    "iat": datetime.now(timezone.utc),
                    "aud": settings.JWT.AUDIENCE,
                    "iss": "spatialtemporal-ai-cloud",
                    "type": "refresh",
                }
            )
            encoded_jwt = jwt.encode(
                to_encode, settings.JWT.SECRET_KEY, algorithm=settings.JWT.ALGORITHM
            )
            return encoded_jwt
        except Exception as e:
            logger.exception("创建刷新令牌异常: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="刷新令牌创建失败",
            )

    @classmethod
    def decode_token(cls, token: str) -> Dict[str, Any]:
        """
        解码JWT令牌
        Args:
            token: JWT令牌字符串
        Returns:
            Dict[str, Any]: 解码后的令牌数据
        Raises:
            HTTPException: 令牌无效或已过期
        """
        try:
            payload = jwt.decode(
                token,
                settings.JWT.SECRET_KEY,
                algorithms=[settings.JWT.ALGORITHM],
                audience=settings.JWT.AUDIENCE,
                options={"verify_signature": True},
            )
            return payload
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌已过期",
                headers={"WWW-Authenticate": token_type},
            )
        except DecodeError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌格式错误",
                headers={"WWW-Authenticate": token_type},
            )
        except InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的令牌",
                headers={"WWW-Authenticate": token_type},
            )
        except Exception as e:
            logger.exception("令牌解码异常: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌验证失败",
                headers={"WWW-Authenticate": token_type},
            )

    @classmethod
    def create_tokens(cls, user_data: Dict[str, Any]) -> Token:
        """
        创建访问令牌和刷新令牌
        Args:
            user_data: 用户数据
        Returns:
            Token: 包含访问令牌和刷新令牌的响应模型
        """
        # 创建访问令牌的数据
        access_token_data = {
            "user_id": str(user_data.get("id", "")),
            "session_id": user_data.get("session_id", ""),
            "scope": "access",
            "role": user_data.get("role", ""),
        }
        # 创建刷新令牌的数据
        refresh_token_data = {
            "user_id": str(user_data.get("id", "")),
            "session_id": user_data.get("session_id", ""),
            "scope": "refresh",
            "role": user_data.get("role", ""),
        }
        # 创建访问令牌和刷新令牌
        access_token = cls.create_access_token(access_token_data)
        refresh_token = cls.create_refresh_token(refresh_token_data)
        return Token(
            access_token=access_token,
            token_type=token_type,
            expires_in=settings.JWT.ACCESS_LIFETIME,
            refresh_token=refresh_token,
        )
