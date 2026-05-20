#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP 服务器创建与 ASGI 挂载
使用 FastMCP + Streamable HTTP 传输
"""
import inspect
import logging

from mcp.server.fastmcp import FastMCP

from mcp_server.config import settings
from mcp_server.context import McpContext, mcp_request_ctx
from mcp_server.registry import discover_tools, get_all_tools

logger = logging.getLogger(__name__)

_mcp_server: FastMCP | None = None


def _type_annotation(type_name: str):
    return {
        "string": str,
        "number": float,
        "boolean": bool,
        "array": list,
        "object": dict,
    }.get(type_name, str)


def _make_tool_handler(tool_cls):
    """为 McpTool 实现类创建符合 FastMCP 签名要求的 async handler"""
    params_def = tool_cls.tool_params()

    # 必填参数排前，可选参数排后，避免 non-default follows default
    sorted_params = sorted(params_def, key=lambda p: p.required, reverse=True)

    sig_params = []
    for p in sorted_params:
        annotation = _type_annotation(p.type)
        if p.required:
            param = inspect.Parameter(
                p.name, inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=annotation
            )
        else:
            param = inspect.Parameter(
                p.name,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                annotation=annotation,
                default=p.default if p.default is not None else "",
            )
        sig_params.append(param)

    async def _handler(**kwargs):
        ctx = mcp_request_ctx.get() or McpContext()
        result = await tool_cls().handle(kwargs, ctx)
        return "\n".join(r.text for r in result)

    _handler.__name__ = tool_cls.tool_name()
    _handler.__doc__ = tool_cls.tool_description()
    _handler.__signature__ = inspect.Signature(sig_params)
    return _handler


def create_mcp_server() -> FastMCP:
    global _mcp_server

    mcp = FastMCP(
        settings.NAME,
        stateless_http=True,
        json_response=True,
    )

    discover_tools()

    for name, tool_cls in get_all_tools().items():
        handler = _make_tool_handler(tool_cls)
        mcp.tool(name=name, description=tool_cls.tool_description())(handler)

    _mcp_server = mcp
    logger.info(f"MCP 服务器已创建，注册了 {len(get_all_tools())} 个工具")
    return mcp


def create_app():
    """创建 ASGI 应用，供 uvicorn factory 模式使用

    同时挂载 MCP 协议端点和管理 API:
    - /mcp       → MCP 协议 (Streamable HTTP)
    - /health    → 健康检查
    - /manage/*  → 工具管理 REST API
    """
    from starlette.applications import Starlette
    from starlette.routing import Mount

    mcp = create_mcp_server()
    mcp_app = mcp.streamable_http_app()

    from mcp_server.manage import create_manage_app
    manage_app = create_manage_app()

    app = Starlette(
        routes=[
            Mount("/mcp", app=mcp_app),
            Mount("/", app=manage_app),
        ],
    )
    return app


def get_mcp_server() -> FastMCP | None:
    return _mcp_server
