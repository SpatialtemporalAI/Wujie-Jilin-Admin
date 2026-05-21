#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP 服务器创建与 ASGI 挂载
使用 FastMCP + Streamable HTTP 传输
"""
import asyncio
import inspect
import logging
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette

from mcp_server.config import settings
from mcp_server.context import McpContext, mcp_request_ctx
from mcp_server.registry import discover_tools, get_all_tools

logger = logging.getLogger(__name__)

_mcp_server: FastMCP | None = None

# 跟踪正在处理的请求数量，用于优雅关闭时等待完成
_active_requests: int = 0
_shutdown_event: asyncio.Event | None = None


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
        global _active_requests
        _active_requests += 1
        try:
            ctx = mcp_request_ctx.get() or McpContext()
            result = await tool_cls().handle(kwargs, ctx)
            return "\n".join(r.text for r in result)
        finally:
            _active_requests -= 1
            if _shutdown_event is not None and _shutdown_event.is_set() and _active_requests == 0:
                _shutdown_event.set()

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


@asynccontextmanager
async def _app_lifespan(app):
    """Starlette 应用生命周期：启动 session manager 与优雅关闭"""
    global _shutdown_event
    _shutdown_event = asyncio.Event()

    # 启动 MCP session manager 的任务组
    mcp = get_mcp_server()
    async with mcp.session_manager.run():
        logger.info("MCP 服务已就绪，开始接受请求")
        yield

    # 关闭阶段：等待正在处理的请求完成（最多 10 秒）
    logger.info("MCP 服务正在关闭，等待 %d 个进行中的请求完成...", _active_requests)
    if _active_requests > 0:
        try:
            await asyncio.wait_for(_shutdown_event.wait(), timeout=10)
            logger.info("所有请求已处理完毕")
        except asyncio.TimeoutError:
            logger.warning("关闭超时，仍有 %d 个请求未完成，强制关闭", _active_requests)
    else:
        logger.info("无进行中的请求，直接关闭")

    logger.info("MCP 服务已关闭")


def create_app():
    """创建 ASGI 应用，供 uvicorn factory 模式使用

    同时挂载 MCP 协议端点和管理 API:
    - /mcp       → MCP 协议 (Streamable HTTP)
    - /health    → 健康检查
    - /manage/*  → 工具管理 REST API
    """
    from starlette.routing import Mount

    mcp = create_mcp_server()
    mcp_app = mcp.streamable_http_app()
    # 提取 mcp_app 的路由，去掉其自带 lifespan（由外层 _app_lifespan 统一管理）
    mcp_routes = list(mcp_app.routes)

    from mcp_server.manage import routes as manage_routes

    app = Starlette(
        routes=[
            *manage_routes,
            *mcp_routes,
        ],
        lifespan=_app_lifespan,
    )
    return app


def get_mcp_server() -> FastMCP | None:
    return _mcp_server
