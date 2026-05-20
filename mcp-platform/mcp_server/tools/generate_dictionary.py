#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP 工具: generate_dictionary
生成字典及其选项，自动检测重复
"""
import json

from mcp_server.registry import register_tool, ToolParam
from mcp_server.context import McpContext
from mcp_server.result import text_result_with_json, text_result_error
from mcp_server.types import TextContent
from mcp_server.http_client import McpHttpClient


@register_tool
class GenerateDictionary:
    @classmethod
    def tool_name(cls) -> str:
        return "generate_dictionary"

    @classmethod
    def tool_description(cls) -> str:
        return "智能生成字典并批量创建字典选项。自动检测字典是否已存在，已存在则跳过创建"

    @classmethod
    def tool_params(cls) -> list[ToolParam]:
        return [
            ToolParam(name="dictType", description="字典类型编码(唯一标识)", type="string", required=True),
            ToolParam(name="dictName", description="字典名称", type="string", required=True),
            ToolParam(name="fieldDesc", description="字典描述", type="string", required=False, default=""),
            ToolParam(name="options", description="JSON数组，选项列表 [{label, value, sort}]", type="string", required=True),
        ]

    async def handle(self, arguments: dict, context: McpContext) -> list[TextContent]:
        try:
            dict_type = arguments["dictType"]
            dict_name = arguments["dictName"]
            field_desc = arguments.get("fieldDesc", "")
            options_raw = arguments.get("options", "[]")
            options = json.loads(options_raw)

            client = McpHttpClient()

            # 检查字典是否已存在
            dict_id = None
            try:
                existing = await client.get(f"/admin/sys/dict/code/{dict_type}")
                if existing.get("data"):
                    dict_id = existing["data"].get("id")
            except Exception:
                pass

            # 不存在则创建字典
            if not dict_id:
                dict_result = await client.post("/admin/sys/dict", json_data={
                    "code": dict_type,
                    "name": dict_name,
                    "description": field_desc,
                    "status": True,
                    "sort": 0,
                })
                dict_id = dict_result.get("data", {}).get("id")

            if not dict_id:
                return text_result_error("创建字典后未能获取字典ID")

            # 批量创建字典选项
            created_items = []
            for idx, opt in enumerate(options):
                item_data = {
                    "dict_id": dict_id,
                    "label": opt.get("label", ""),
                    "value": str(opt.get("value", "")),
                    "status": True,
                    "sort": opt.get("sort", idx),
                }
                if opt.get("description"):
                    item_data["description"] = opt["description"]
                try:
                    item_result = await client.post("/admin/sys/dict/item", json_data=item_data)
                    created_items.append(item_result.get("data", {}))
                except Exception:
                    created_items.append({"label": opt.get("label"), "value": opt.get("value"), "status": "skipped"})

            return text_result_with_json({
                "dict_id": dict_id,
                "dict_type": dict_type,
                "dict_name": dict_name,
                "items": created_items,
                "total_items": len(created_items),
            })
        except json.JSONDecodeError as e:
            return text_result_error(f"JSON解析失败: {str(e)}")
        except Exception as e:
            return text_result_error(f"生成字典失败: {str(e)}")
