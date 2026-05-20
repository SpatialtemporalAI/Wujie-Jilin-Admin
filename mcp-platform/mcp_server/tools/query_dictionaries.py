#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP 工具: query_dictionaries
查询系统字典及其选项
"""
from mcp_server.registry import register_tool, ToolParam
from mcp_server.context import McpContext
from mcp_server.result import text_result_with_json, text_result_error
from mcp_server.types import TextContent
from mcp_server.http_client import McpHttpClient


@register_tool
class QueryDictionaries:
    @classmethod
    def tool_name(cls) -> str:
        return "query_dictionaries"

    @classmethod
    def tool_description(cls) -> str:
        return "查询系统字典数据。指定dictType查询单个字典及其选项，不指定则返回所有字典列表"

    @classmethod
    def tool_params(cls) -> list[ToolParam]:
        return [
            ToolParam(name="dictType", description="字典类型编码(唯一标识)，不填则返回所有字典", type="string", required=False, default=""),
            ToolParam(name="includeDisabled", description="是否包含已禁用的字典/选项", type="boolean", required=False, default=False),
        ]

    async def handle(self, arguments: dict, context: McpContext) -> list[TextContent]:
        try:
            client = McpHttpClient()
            dict_type = arguments.get("dictType", "")
            include_disabled = arguments.get("includeDisabled", False)

            if dict_type:
                result = await client.get(f"/admin/sys/dict/code/{dict_type}")
                data = result.get("data", {})
                if not include_disabled and data.get("items"):
                    data["items"] = [item for item in data["items"] if item.get("status", True)]
                return text_result_with_json({"dictionary": data})
            else:
                params = {}
                if not include_disabled:
                    params["status"] = "true"
                result = await client.get("/admin/sys/dict/all", params=params)
                return text_result_with_json({"dictionaries": result.get("data", [])})
        except Exception as e:
            return text_result_error(f"查询字典失败: {str(e)}")
