#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Any
from fastapi import HTTPException
from enum import Enum
from core.response import StandardResponseCode, CustomErrorCode


class BaseExceptionMixin(Exception):
    """基础异常混入类"""

    code: int
    err_code: CustomErrorCode

    def __init__(
        self,
        *,
        msg: str = None,
        data: Any = None,
    ):
        self.msg = msg
        self.data = data


class HTTPError(HTTPException):
    """HTTP 异常"""

    def __init__(
        self, *, code: int, msg: Any = None, headers: dict[str, Any] | None = None
    ):
        super().__init__(status_code=code, detail=msg, headers=headers)


class CustomError(BaseExceptionMixin):
    """自定义异常"""

    def __init__(
        self,
        *,
        error: CustomErrorCode,
        msg: str = None,
        data: Any = None,
    ):
        self.code = error.code
        super().__init__(msg=msg or error.msg, data=data)


class RequestError(BaseExceptionMixin):
    """请求异常"""

    def __init__(
        self,
        *,
        code: int = StandardResponseCode.HTTP_400,
        msg: str = "Bad Request",
        data: Any = None,
    ):
        self.code = code
        super().__init__(msg=msg, data=data)


class ForbiddenError(BaseExceptionMixin):
    """禁止访问异常"""

    code = StandardResponseCode.HTTP_403

    def __init__(self, *, msg: str = "Forbidden", data: Any = None):
        super().__init__(msg=msg, data=data)


class NotFoundError(BaseExceptionMixin):
    """资源不存在异常"""

    code = StandardResponseCode.HTTP_404

    def __init__(self, *, msg: str = "Not Found", data: Any = None):
        super().__init__(msg=msg, data=data)


class ServerError(BaseExceptionMixin):
    """服务器异常"""

    code = StandardResponseCode.HTTP_500

    def __init__(
        self,
        *,
        msg: str = "Internal Server Error",
        data: Any = None,
    ):
        super().__init__(msg=msg, data=data)


class GatewayError(BaseExceptionMixin):
    """网关异常"""

    code = StandardResponseCode.HTTP_502

    def __init__(
        self,
        *,
        msg: str = "Bad Gateway",
        data: Any = None,
    ):
        super().__init__(msg=msg, data=data)


class AuthorizationError(BaseExceptionMixin):
    """授权异常"""

    code = StandardResponseCode.HTTP_403

    def __init__(
        self,
        *,
        msg: str = "Permission Denied",
        data: Any = None,
    ):
        super().__init__(msg=msg, data=data)


class TokenError(HTTPError):
    """Token 异常"""

    code = StandardResponseCode.HTTP_401

    def __init__(
        self, *, msg: str = "Not Authenticated", headers: dict[str, Any] | None = None
    ):
        super().__init__(
            code=self.code, msg=msg, headers=headers or {"WWW-Authenticate": "Bearer"}
        )


class ConflictError(BaseExceptionMixin):
    """资源冲突异常"""

    code = StandardResponseCode.HTTP_409

    def __init__(
        self,
        *,
        msg: str = "Conflict",
        data: Any = None,
    ):
        super().__init__(msg=msg, data=data)


class ValidationError(BaseExceptionMixin):
    """验证异常"""

    code = StandardResponseCode.HTTP_422

    def __init__(
        self,
        *,
        msg: str = "Validation Error",
        data: Any = None,
    ):
        super().__init__(msg=msg, data=data)
