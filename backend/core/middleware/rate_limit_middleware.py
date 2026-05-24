#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""限流与 IP 黑名单中间件。

执行顺序（在 setup_registry 中靠后注册 = 实际执行靠前）：
    RequestContextMiddleware -> RateLimitMiddleware -> OperationLogMiddleware -> ...

逻辑：
    1. 命中白名单前缀 / 白名单 IP / 配置关闭 -> 直接放行
    2. 命中 IP 黑名单 -> 直接 429
    3. 解析 JWT 拿 user_id（可选，沿用 operation_log_middleware 的方式）
    4. 顺序检查：全局 IP -> 用户 -> 路径细粒度
"""
import logging
from typing import Callable, Optional

import jwt
from fastapi import Request
from fastapi.responses import ORJSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from core.config import settings
from core.security.rate_limit import (
    RateLimitExceeded,
    enforce_ip_limit,
    enforce_path_limit,
    enforce_user_limit,
    is_ip_blocked,
)
from core.utils.ip_utils import get_real_client_ip

logger = logging.getLogger(__name__)


def _is_whitelisted_path(path: str) -> bool:
    for prefix in settings.RATE_LIMIT.WHITELIST_PATH_PREFIXES:
        if path.startswith(prefix):
            return True
    return False


def _extract_user_id(request: Request) -> Optional[int]:
    """优先复用 operation_log_middleware 已经写入的 payload，避免重复解析 JWT。"""
    cached = getattr(request.state, "_jwt_payload", None)
    if cached and cached.get("user_id"):
        try:
            return int(cached["user_id"])
        except (TypeError, ValueError):
            return None

    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:]
    try:
        payload = jwt.decode(
            token,
            settings.JWT.SECRET_KEY,
            algorithms=[settings.JWT.ALGORITHM],
            audience=settings.JWT.AUDIENCE,
            options={"verify_exp": True},
        )
        request.state._jwt_payload = payload
        request.state._jwt_raw_token = token
        user_id = payload.get("user_id")
        if user_id:
            return int(user_id)
    except Exception:
        return None
    return None


def _match_path_rule(path: str, method: str):
    """匹配第一条命中的 PATH_RULES 规则。"""
    for rule in settings.RATE_LIMIT.PATH_RULES:
        if not path.startswith(rule.PATH):
            continue
        if rule.METHOD != "*" and rule.METHOD.upper() != method.upper():
            continue
        return rule
    return None


def _build_429_response(request_id: str, reason: str, retry_after: int) -> ORJSONResponse:
    """返回对齐 ResponseModel 结构的 429 响应。"""
    body = {
        "code": 429,
        "msg": reason,
        "data": None,
        "request_id": request_id,
        "err_code": 10901,
    }
    resp = ORJSONResponse(status_code=429, content=body)
    resp.headers["Retry-After"] = str(retry_after)
    return resp


def _build_blocked_response(request_id: str) -> ORJSONResponse:
    body = {
        "code": 429,
        "msg": "IP 已被加入黑名单，请联系管理员",
        "data": None,
        "request_id": request_id,
        "err_code": 10902,
    }
    resp = ORJSONResponse(status_code=429, content=body)
    resp.headers["Retry-After"] = "3600"
    return resp


class RateLimitMiddleware(BaseHTTPMiddleware):
    """多维度限流 + IP 黑名单。"""

    async def dispatch(self, request: Request, call_next: Callable):
        rate_cfg = settings.RATE_LIMIT
        if not rate_cfg.ENABLED:
            return await call_next(request)

        path = request.url.path
        if _is_whitelisted_path(path):
            return await call_next(request)

        client_ip = getattr(request.state, "client_ip", "") or get_real_client_ip(request)
        if client_ip and client_ip in rate_cfg.WHITELIST_IPS:
            return await call_next(request)

        request_id = getattr(request.state, "request_id", "") or ""

        try:
            if client_ip and await is_ip_blocked(client_ip):
                logger.warning("IP 命中黑名单 ip=%s path=%s", client_ip, path)
                return _build_blocked_response(request_id)

            if client_ip:
                await enforce_ip_limit(client_ip, rate_cfg.IP_PER_MINUTE, 60)

            user_id = _extract_user_id(request)
            if user_id:
                await enforce_user_limit(user_id, rate_cfg.USER_PER_MINUTE, 60)

            rule = _match_path_rule(path, request.method)
            if rule and client_ip:
                await enforce_path_limit(
                    method=request.method,
                    path=rule.PATH,
                    ip=client_ip,
                    limit=rule.PER_MINUTE,
                    window_seconds=60,
                )
        except RateLimitExceeded as exc:
            return _build_429_response(request_id, exc.reason, exc.retry_after)
        except Exception as exc:  # Redis 故障等 -> 失败放行，避免阻塞业务
            logger.error("限流中间件异常，放行请求 path=%s err=%s", path, exc)
            return await call_next(request)

        return await call_next(request)
