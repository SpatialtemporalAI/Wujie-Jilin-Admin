#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP 工具: create_permission
创建权限/API记录，支持单条和批量
"""
import json

from mcp_server.registry import register_tool, ToolParam
from mcp_server.context import McpContext
from mcp_server.result import text_result_with_json, text_result_error
from mcp_server.types import TextContent
from mcp_server.http_client import McpHttpClient


@register_tool
class CreatePermission:
    @classmethod
    def tool_name(cls) -> str:
        return "create_permission"

    @classmethod
    def tool_description(cls) -> str:
        return "在数据库中创建权限/API记录。支持单条和批量创建，每项包含name/code/resource_path/method/category等"

    @classmethod
    def tool_params(cls) -> list[ToolParam]:
        return [
            ToolParam(name="permissions", description="JSON数组，每项含name,code,resource_path,method,category,type,status,sort", type="string", required=True),
        ]

    async def handle(self, arguments: dict, context: McpContext) -> list[TextContent]:
        try:
            permissions_raw = arguments.get("permissions", "[]")
            items = json.loads(permissions_raw)
            if isinstance(items, dict):
                items = [items]

            client = McpHttpClient()
            created = []
            failed = []

            for item in items:
                try:
                    result = await client.post("/admin/sys/permission", json_data=item)
                    created.append(result.get("data", item))
                except Exception as e:
                    failed.append({"item": item, "error": str(e)})

            return text_result_with_json({
                "created": created,
                "failed": failed,
                "total_created": len(created),
                "total_failed": len(failed),
            })
        except json.JSONDecodeError as e:
            return text_result_error(f"JSON解析失败: {str(e)}")
        except Exception as e:
            return text_result_error(f"创建权限失败: {str(e)}")
