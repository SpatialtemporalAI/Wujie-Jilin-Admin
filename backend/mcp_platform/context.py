#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP 鉴权上下文
通过 contextvars 在异步调用链中传递请求上下文
"""
from contextvars import ContextVar
from dataclasses import dataclass, field


@dataclass
class McpContext:
    token: str | None = None

    @classmethod
    def from_headers(cls, headers: dict) -> "McpContext":
        token = headers.get("x-token") or headers.get("Authorization")
        if token and token.startswith("Bearer "):
            token = token[7:]
        return cls(token=token)


mcp_request_ctx: ContextVar[McpContext | None] = ContextVar(
    "mcp_request_ctx", default=None
)
