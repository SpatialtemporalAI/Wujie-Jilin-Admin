#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP 服务器创建与 ASGI 挂载
使用 FastMCP + Streamable HTTP 传输
"""
import inspect
import logging

from mcp.server.fastmcp import FastMCP

from core.config import settings
from mcp_platform.context import McpContext, mcp_request_ctx
from mcp_platform.registry import discover_tools, get_all_tools

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

    # 构建 inspect.Signature 参数列表
    sig_params = []
    for p in params_def:
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
        settings.MCP.NAME,
        stateless_http=True,
        json_response=True,
    )

    # 自动发现并注册工具
    discover_tools()

    for name, tool_cls in get_all_tools().items():
        handler = _make_tool_handler(tool_cls)
        mcp.tool(name=name, description=tool_cls.tool_description())(handler)

    _mcp_server = mcp
    logger.info(f"MCP 服务器已创建，注册了 {len(get_all_tools())} 个工具")
    return mcp


def get_mcp_asgi_app():
    """返回 streamable_http_app() 供 Starlette Mount 使用"""
    if _mcp_server is None:
        create_mcp_server()
    return _mcp_server.streamable_http_app()


def get_mcp_server() -> FastMCP | None:
    return _mcp_server
