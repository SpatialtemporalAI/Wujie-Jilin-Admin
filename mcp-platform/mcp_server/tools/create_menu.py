#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP 工具: create_menu
创建菜单记录，支持单条和批量
"""
import json

from mcp_server.registry import register_tool, ToolParam
from mcp_server.context import McpContext
from mcp_server.result import text_result_with_json, text_result_error
from mcp_server.types import TextContent
from mcp_server.http_client import McpHttpClient


@register_tool
class CreateMenu:
    @classmethod
    def tool_name(cls) -> str:
        return "create_menu"

    @classmethod
    def tool_description(cls) -> str:
        return "在数据库中创建前端菜单记录。支持单条和批量，每项含parent_id/name/path/component/meta_title/meta_icon/type/sort等"

    @classmethod
    def tool_params(cls) -> list[ToolParam]:
        return [
            ToolParam(name="menus", description="JSON数组，每项含parent_id,name,path,component,meta_title,meta_icon,type,sort,status等", type="string", required=True),
        ]

    async def handle(self, arguments: dict, context: McpContext) -> list[TextContent]:
        try:
            menus_raw = arguments.get("menus", "[]")
            items = json.loads(menus_raw)
            if isinstance(items, dict):
                items = [items]

            client = McpHttpClient()
            created = []
            failed = []
            name_to_id = {}

            for item in items:
                # 如果 parent_name 存在，尝试通过 name 映射解析 parent_id
                parent_name = item.pop("parent_name", None)
                if parent_name and parent_name in name_to_id:
                    item["parent_id"] = name_to_id[parent_name]

                try:
                    result = await client.post("/admin/sys/menu/add", json_data=item)
                    data = result.get("data", {})
                    created.append(data)
                    # 记录 name -> id 映射，供后续子菜单引用
                    if item.get("name"):
                        name_to_id[item["name"]] = data.get("id")
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
            return text_result_error(f"创建菜单失败: {str(e)}")
