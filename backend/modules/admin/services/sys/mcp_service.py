#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP 管理服务层
"""
import logging
from typing import List

from mcp_platform.registry import get_all_tools, get_tool, discover_tools, ToolParam
from mcp_platform.standalone import StandaloneMCPManager
from mcp_platform.template import generate_tool_code, write_tool_file
from mcp_platform.context import McpContext
from modules.admin.schemas.sys.mcp import (
    AutoMcpToolCreate,
    McpToolInfo,
    McpToolParamSchema,
    McpToolTestRequest,
    McpServerStatusResponse,
)

logger = logging.getLogger(__name__)


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
        code = generate_tool_code(
            name=tool_create.name,
            description=tool_create.description,
            params=params,
        )
        file_path = write_tool_file(tool_create.name, code)
        return {"name": tool_create.name, "file_path": file_path}

    @staticmethod
    async def get_server_status() -> McpServerStatusResponse:
        status = StandaloneMCPManager.status()
        return McpServerStatusResponse(**status)

    @staticmethod
    async def start_server() -> dict:
        return StandaloneMCPManager.start()

    @staticmethod
    async def stop_server() -> dict:
        return StandaloneMCPManager.stop()

    @staticmethod
    async def list_tools() -> List[McpToolInfo]:
        discover_tools()
        tools = get_all_tools()
        result = []
        for name, cls in tools.items():
            params = cls.tool_params()
            result.append(McpToolInfo(
                name=name,
                description=cls.tool_description(),
                params=[
                    McpToolParamSchema(
                        name=p.name,
                        description=p.description,
                        type=p.type,
                        required=p.required,
                        default=str(p.default) if p.default is not None else None,
                    )
                    for p in params
                ],
            ))
        return result

    @staticmethod
    async def list_routes() -> list:
        from mcp_platform.server import get_mcp_server
        mcp = get_mcp_server()
        if not mcp:
            return []
        tools = mcp._tool_manager.list_tools()
        return [
            {
                "name": t.name,
                "description": t.description,
            }
            for t in tools
        ]

    @staticmethod
    async def test_tool(test_request: McpToolTestRequest) -> dict:
        discover_tools()
        tool_cls = get_tool(test_request.tool_name)
        if not tool_cls:
            return {"error": f"工具 '{test_request.tool_name}' 不存在"}

        try:
            tool_instance = tool_cls()
            result = await tool_instance.handle(test_request.arguments, McpContext())
            return {
                "tool_name": test_request.tool_name,
                "result": [r.text for r in result],
            }
        except Exception as e:
            logger.error(f"测试工具失败: {e}")
            return {"error": str(e)}
