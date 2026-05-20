#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP 管理接口
提供工具管理、健康检查、优雅关闭等 REST API
"""
import asyncio
import json
import logging
import os
import signal

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from mcp_server.registry import discover_tools, get_all_tools, get_tool, ToolParam
from mcp_server.template import generate_tool_code, write_tool_file
from mcp_server.context import McpContext

logger = logging.getLogger(__name__)


async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


async def list_tools(request: Request) -> JSONResponse:
    discover_tools()
    tools = get_all_tools()
    result = []
    for name, cls in tools.items():
        params = cls.tool_params()
        result.append({
            "name": name,
            "description": cls.tool_description(),
            "params": [
                {
                    "name": p.name,
                    "description": p.description,
                    "type": p.type,
                    "required": p.required,
                    "default": str(p.default) if p.default is not None else None,
                }
                for p in params
            ],
        })
    return JSONResponse(result)


async def create_tool(request: Request) -> JSONResponse:
    body = await request.json()
    name = body["name"]
    description = body.get("description", "")
    params = body.get("params", [])

    code = generate_tool_code(name=name, description=description, params=params)
    file_path = write_tool_file(name, code)
    return JSONResponse({"name": name, "file_path": file_path})


async def test_tool(request: Request) -> JSONResponse:
    body = await request.json()
    tool_name = body["tool_name"]
    arguments = body.get("arguments", {})

    discover_tools()
    tool_cls = get_tool(tool_name)
    if not tool_cls:
        return JSONResponse({"error": f"工具 '{tool_name}' 不存在"}, status_code=404)

    try:
        tool_instance = tool_cls()
        result = await tool_instance.handle(arguments, McpContext())
        return JSONResponse({
            "tool_name": tool_name,
            "result": [r.text for r in result],
        })
    except Exception as e:
        logger.error(f"测试工具失败: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


async def shutdown(request: Request) -> JSONResponse:
    """触发优雅关闭，向当前进程发送 SIGTERM"""
    logger.info("收到远程关闭请求，开始优雅关闭...")
    loop = asyncio.get_running_loop()
    loop.call_later(0.1, os.kill, os.getpid(), signal.SIGTERM)
    return JSONResponse({"status": "shutting_down"})


routes = [
    Route("/health", health),
    Route("/manage/shutdown", shutdown, methods=["POST"]),
    Route("/manage/tools/list", list_tools),
    Route("/manage/tools/create", create_tool, methods=["POST"]),
    Route("/manage/tools/test", test_tool, methods=["POST"]),
]


def create_manage_app() -> Starlette:
    return Starlette(routes=routes)
