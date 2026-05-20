#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP 工具结果辅助函数
"""
import json
from mcp_server.types import TextContent


def text_result(content: str) -> list[TextContent]:
    return [TextContent(type="text", text=content)]


def text_result_with_json(data) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, default=str))]


def text_result_error(message: str) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps({"error": message}, ensure_ascii=False))]
