#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP 管理服务层
通过 HTTP 调用独立 MCP 服务器
"""
import logging
from typing import List

import httpx

from core.config import settings
from modules.admin.schemas.sys.mcp import (
    AutoMcpToolCreate,
    McpToolInfo,
    McpToolParamSchema,
    McpToolTestRequest,
    McpServerStatusResponse,
)

logger = logging.getLogger(__name__)


def _mcp_base_url() -> str:
    return f"http://{settings.MCP.HOST}:{settings.MCP.PORT}"


class MCPService:
    @staticmethod
    async def create_tool(tool_create: AutoMcpToolCreate) -> dict:
        params = [
            {
                "name": p.name,
                "description": p.description,
                "type": p.type,
                "required": p.required,
                "default": p.default,
            }
            for p in tool_create.params
        ]
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{_mcp_base_url()}/manage/tools/create",
                json={
                    "name": tool_create.name,
                    "description": tool_create.description,
                    "params": params,
                },
            )
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    async def get_server_status() -> McpServerStatusResponse:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{_mcp_base_url()}/health")
                if resp.status_code == 200:
                    return McpServerStatusResponse(
                        running=True,
                        status="running",
                        host=settings.MCP.HOST,
                        port=settings.MCP.PORT,
                    )
        except Exception:
            pass
        return McpServerStatusResponse(
            running=False,
            status="stopped",
            host=settings.MCP.HOST,
            port=settings.MCP.PORT,
        )

    @staticmethod
    async def start_server() -> dict:
        return {
            "status": "independent",
            "message": "MCP 服务已独立部署，请直接启动 mcp-server",
            "host": settings.MCP.HOST,
            "port": settings.MCP.PORT,
        }

    @staticmethod
    async def stop_server() -> dict:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.post(f"{_mcp_base_url()}/manage/shutdown")
                if resp.status_code == 200:
                    return {
                        "status": "shutting_down",
                        "message": "MCP 服务正在优雅关闭",
                    }
        except Exception:
            pass
        return {
            "status": "independent",
            "message": "MCP 服务已独立部署，请直接停止 mcp-server",
            "host": settings.MCP.HOST,
            "port": settings.MCP.PORT,
        }

    @staticmethod
    async def list_tools() -> List[McpToolInfo]:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{_mcp_base_url()}/manage/tools/list")
                resp.raise_for_status()
                data = resp.json()
                return [
                    McpToolInfo(
                        name=t["name"],
                        description=t.get("description", ""),
                        params=[
                            McpToolParamSchema(
                                name=p["name"],
                                description=p.get("description", ""),
                                type=p.get("type", "string"),
                                required=p.get("required", True),
                                default=p.get("default"),
                            )
                            for p in t.get("params", [])
                        ],
                    )
                    for t in data
                ]
        except Exception as e:
            logger.error(f"获取 MCP 工具列表失败: {e}")
            return []

    @staticmethod
    async def list_routes() -> list:
        tools = await MCPService.list_tools()
        return [
            {"name": t.name, "description": t.description}
            for t in tools
        ]

    @staticmethod
    async def test_tool(test_request: McpToolTestRequest) -> dict:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{_mcp_base_url()}/manage/tools/test",
                    json={
                        "tool_name": test_request.tool_name,
                        "arguments": test_request.arguments,
                    },
                )
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPStatusError as e:
            return e.response.json()
        except Exception as e:
            logger.error(f"测试工具失败: {e}")
            return {"error": str(e)}
