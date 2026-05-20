#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP 工具: list_all_menus
列出系统中所有菜单的树形结构
"""
from mcp_server.registry import register_tool, ToolParam
from mcp_server.context import McpContext
from mcp_server.result import text_result_with_json, text_result_error
from mcp_server.types import TextContent
from mcp_server.http_client import McpHttpClient


@register_tool
class ListAllMenus:
    @classmethod
    def tool_name(cls) -> str:
        return "list_all_menus"

    @classmethod
    def tool_description(cls) -> str:
        return "获取系统完整的菜单树形结构，包含路由配置(path/name/component)、元数据(title/icon/keepAlive)、父子关系等"

    @classmethod
    def tool_params(cls) -> list[ToolParam]:
        return [
            ToolParam(name="status", description="按状态筛选: true-启用, false-禁用", type="boolean", required=False, default=True),
        ]

    async def handle(self, arguments: dict, context: McpContext) -> list[TextContent]:
        try:
            client = McpHttpClient()
            params = {}
            status = arguments.get("status")
            if status is not None:
                params["status"] = str(status).lower()

            result = await client.get("/admin/sys/menu/tree", params=params)
            menu_tree = result.get("data", [])
            return text_result_with_json({"menuTree": menu_tree})
        except Exception as e:
            return text_result_error(f"获取菜单树失败: {str(e)}")
