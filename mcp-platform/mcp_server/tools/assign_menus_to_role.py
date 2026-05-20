#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP 工具: assign_menus_to_role
为角色分配菜单权限，仅追加不覆盖
"""
import json

from mcp_server.registry import register_tool, ToolParam
from mcp_server.context import McpContext
from mcp_server.result import text_result_with_json, text_result_error
from mcp_server.types import TextContent
from mcp_server.http_client import McpHttpClient


@register_tool
class AssignMenusToRole:
    @classmethod
    def tool_name(cls) -> str:
        return "assign_menus_to_role"

    @classmethod
    def tool_description(cls) -> str:
        return "将菜单权限追加分配给指定角色。仅追加不覆盖原有权限，幂等操作"

    @classmethod
    def tool_params(cls) -> list[ToolParam]:
        return [
            ToolParam(name="roleId", description="角色ID", type="number", required=True),
            ToolParam(name="menuIds", description="JSON数组，要分配的菜单ID列表，如 [1,2,3]", type="string", required=True),
        ]

    async def handle(self, arguments: dict, context: McpContext) -> list[TextContent]:
        try:
            role_id = arguments.get("roleId")
            menu_ids_raw = arguments.get("menuIds", "[]")
            menu_ids = json.loads(menu_ids_raw)

            client = McpHttpClient()
            result = await client.post(
                f"/admin/sys/role/{role_id}/menus",
                json_data={"menu_ids": menu_ids},
            )
            return text_result_with_json(result.get("data", {}))
        except json.JSONDecodeError as e:
            return text_result_error(f"JSON解析失败: {str(e)}")
        except Exception as e:
            return text_result_error(f"分配菜单权限失败: {str(e)}")
