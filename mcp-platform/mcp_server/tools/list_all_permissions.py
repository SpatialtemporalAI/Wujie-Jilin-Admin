#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP 工具: list_all_permissions
列出系统中所有权限记录
"""
from mcp_server.registry import register_tool, ToolParam
from mcp_server.context import McpContext
from mcp_server.result import text_result_with_json, text_result_error
from mcp_server.types import TextContent
from mcp_server.http_client import McpHttpClient


@register_tool
class ListAllPermissions:
    @classmethod
    def tool_name(cls) -> str:
        return "list_all_permissions"

    @classmethod
    def tool_description(cls) -> str:
        return "列出系统中所有已注册的权限/API记录，含ID、名称、编码、资源路径、请求方法、分类等"

    @classmethod
    def tool_params(cls) -> list[ToolParam]:
        return [
            ToolParam(name="category", description="按权限分类筛选", type="string", required=False, default=""),
            ToolParam(name="status", description="按状态筛选: true-启用, false-禁用", type="boolean", required=False, default=True),
        ]

    async def handle(self, arguments: dict, context: McpContext) -> list[TextContent]:
        try:
            client = McpHttpClient()
            params = {}
            category = arguments.get("category", "")
            if category:
                params["category"] = category
            status = arguments.get("status")
            if status is not None:
                params["status"] = str(status).lower()

            result = await client.get("/admin/sys/permission/list", params=params)
            permissions = result.get("data", [])
            return text_result_with_json({
                "permissions": permissions,
                "total": len(permissions),
            })
        except Exception as e:
            return text_result_error(f"获取权限列表失败: {str(e)}")
