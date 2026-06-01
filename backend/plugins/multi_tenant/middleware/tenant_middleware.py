#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from starlette.types import ASGIApp, Receive, Scope, Send
from typing import Optional

from plugins.multi_tenant.deps.tenant_context import (
    set_current_tenant_id,
    reset_tenant_id,
)


class TenantContextMiddleware:
    """
    从 JWT Authorization header 中提取 tenant_id 并设置到 contextvars。
    在 RequestContextMiddleware 之后执行。
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http":
            token = None
            try:
                tenant_id = self._extract_tenant_id(scope)
                token = set_current_tenant_id(tenant_id)
                await self.app(scope, receive, send)
            finally:
                if token is not None:
                    reset_tenant_id(token)
        else:
            await self.app(scope, receive, send)

    def _extract_tenant_id(self, scope: Scope) -> Optional[int]:
        """从请求头中解析 JWT 获取 tenant_id"""
        headers = dict(scope.get("headers", []))
        auth_header = headers.get(b"authorization", b"").decode("utf-8", errors="ignore")
        if not auth_header.startswith("Bearer "):
            return None
        try:
            from core.security.oauth.jwt import JWTAuthManager

            token_str = auth_header[7:]
            # 先用全局密钥尝试解码
            try:
                payload = JWTAuthManager.decode_token(token_str)
            except Exception:
                # 全局密钥失败（可能使用租户密钥签名），从未验证 payload 中提取 tenant_id
                payload = JWTAuthManager.decode_token_unverified(token_str)
            tid = payload.get("tenant_id")
            return int(tid) if tid else None
        except Exception:
            return None
