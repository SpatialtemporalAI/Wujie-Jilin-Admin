#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
操作日志中间件
自动捕获所有 admin 接口的操作日志
"""
import asyncio
import json
import logging
import time
from typing import Callable

import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from core.config import settings
from core.utils.ip_utils import get_real_client_ip

logger = logging.getLogger(__name__)

MAX_RESPONSE_RESULT_LENGTH = 2000

WHITELIST_PREFIXES = (
    "/admin/auth",
    "/admin/sys/operation-log",
    "/admin/sys/login-log",
    "/docs",
    "/redoc",
    "/openapi.json",
)


def _is_whitelisted(path: str) -> bool:
    for prefix in WHITELIST_PREFIXES:
        if path.startswith(prefix):
            return True
    return False


def _extract_user_from_token(request: Request) -> tuple[int | None, str | None]:
    """从 Authorization 头解析 JWT 获取 user_id 和 username"""
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        return None, None
    token = auth_header[7:]
    try:
        payload = jwt.decode(
            token,
            settings.JWT.SECRET_KEY,
            algorithms=[settings.JWT.ALGORITHM],
            audience=settings.JWT.AUDIENCE,
            options={"verify_exp": True},
        )
        user_id = payload.get("user_id")
        username = payload.get("username")
        if user_id:
            return int(user_id), username or "unknown"
    except Exception:
        pass
    return None, None


async def _capture_request_body(request: Request) -> str | None:
    """读取请求体并序列化为 JSON 字符串"""
    try:
        body = await request.body()
        if not body:
            params = {}
            if request.query_params:
                params["query"] = dict(request.query_params)
            return json.dumps(params, ensure_ascii=False) if params else None
        params = {"query": dict(request.query_params)} if request.query_params else {}
        try:
            params["body"] = json.loads(body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            params["body"] = body.decode("utf-8", errors="replace")
        return json.dumps(params, ensure_ascii=False)
    except Exception:
        return None


def _read_response_body_fast(response: Response) -> str | None:
    """从已缓冲的响应中快速读取 body（BaseHTTPMiddleware 已缓冲，无需遍历 body_iterator）"""
    try:
        body = getattr(response, "body", None)
        if body:
            text = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else str(body)
            if len(text) > MAX_RESPONSE_RESULT_LENGTH:
                text = text[:MAX_RESPONSE_RESULT_LENGTH] + "...(truncated)"
            return text
    except Exception:
        pass
    return None


async def _write_operation_log(
    user_id: int | None,
    username: str | None,
    method: str,
    path: str,
    ip: str | None,
    request_params: str | None,
    response_code: int | None,
    response_result: str | None,
    elapsed_ms: float | None,
):
    """异步写入操作日志到数据库"""
    try:
        from database import get_session
        from app.models.sys.operation_log import SysOperationLog

        async for db in get_session():
            log_entry = SysOperationLog(
                user_id=user_id or 0,
                username=username or "anonymous",
                module=path.split("/")[2] if len(path.split("/")) > 2 else "unknown",
                action=method.lower(),
                description=f"{method} {path}",
                method=method,
                path=path,
                ip=ip,
                request_params=request_params,
                response_code=response_code,
                response_result=response_result,
                elapsed_ms=elapsed_ms,
            )
            db.add(log_entry)
            await db.commit()
    except Exception as e:
        logger.error(f"写入操作日志失败: {e}")


class OperationLogMiddleware(BaseHTTPMiddleware):
    """自动记录所有 admin 接口的操作日志"""

    async def dispatch(self, request: Request, call_next: Callable):
        path = request.url.path

        if not path.startswith("/admin/") or _is_whitelisted(path):
            return await call_next(request)

        start = time.monotonic()

        request_params = await _capture_request_body(request)
        user_id, username = _extract_user_from_token(request)
        ip = get_real_client_ip(request)

        response = await call_next(request)

        elapsed_ms = (time.monotonic() - start) * 1000

        response_result = _read_response_body_fast(response)

        asyncio.create_task(
            _write_operation_log(
                user_id=user_id,
                username=username,
                method=request.method,
                path=path,
                ip=ip,
                request_params=request_params,
                response_code=response.status_code,
                response_result=response_result,
                elapsed_ms=elapsed_ms,
            )
        )

        return response
