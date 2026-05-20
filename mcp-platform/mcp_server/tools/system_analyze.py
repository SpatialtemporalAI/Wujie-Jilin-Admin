#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP 工具: system_analyze
获取当前系统状态：菜单、权限、角色、字典、配置
"""
import asyncio
import logging

from mcp_server.registry import register_tool, ToolParam
from mcp_server.context import McpContext
from mcp_server.result import text_result_with_json, text_result_error
from mcp_server.types import TextContent
from mcp_server.http_client import McpHttpClient

logger = logging.getLogger(__name__)


async def _safe_get(client: McpHttpClient, path: str, label: str) -> dict:
    try:
        result = await client.get(path)
        return result.get("data", [])
    except Exception as e:
        return {"error": f"{label}获取失败: {str(e)}"}


@register_tool
class SystemAnalyze:
    @classmethod
    def tool_name(cls) -> str:
        return "system_analyze"

    @classmethod
    def tool_description(cls) -> str:
        return "获取当前系统完整状态，包括菜单树、权限列表、角色列表、字典列表、系统配置，用于分析现有资源和规划新功能"

    @classmethod
    def tool_params(cls) -> list[ToolParam]:
        return [
            ToolParam(name="requirement", description="用户需求描述(用于上下文参考)", type="string", required=True),
        ]

    async def handle(self, arguments: dict, context: McpContext) -> list[TextContent]:
        try:
            client = McpHttpClient()
            requirement = arguments.get("requirement", "")

            menus, permissions, roles, dicts, configs = await asyncio.gather(
                _safe_get(client, "/admin/sys/menu/tree", "菜单"),
                _safe_get(client, "/admin/sys/permission/list", "权限"),
                _safe_get(client, "/admin/sys/role/all", "角色"),
                _safe_get(client, "/admin/sys/dict/all", "字典"),
                _safe_get(client, "/admin/sys/config/all", "配置"),
            )

            def _count(data):
                if isinstance(data, list):
                    return len(data)
                return 0

            return text_result_with_json({
                "requirement": requirement,
                "existingMenus": menus,
                "existingPermissions": permissions,
                "existingRoles": roles,
                "dictionaries": dicts,
                "configs": configs,
                "summary": {
                    "menuCount": _count(menus) if not isinstance(menus, dict) else 0,
                    "permissionCount": _count(permissions),
                    "roleCount": _count(roles),
                    "dictCount": _count(dicts),
                    "configCount": _count(configs),
                },
            })
        except Exception as e:
            return text_result_error(f"系统分析失败: {str(e)}")
