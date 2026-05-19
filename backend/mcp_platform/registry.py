#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP 工具注册表
提供 @register_tool 装饰器和工具自动发现
"""
import importlib
import logging
import pkgutil
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from mcp_platform.types import TextContent

from mcp_platform.context import McpContext

logger = logging.getLogger(__name__)


@dataclass
class ToolParam:
    name: str
    description: str
    type: str = "string"
    required: bool = True
    default: Any = None


@runtime_checkable
class McpTool(Protocol):
    @classmethod
    def tool_name(cls) -> str: ...

    @classmethod
    def tool_description(cls) -> str: ...

    @classmethod
    def tool_params(cls) -> list[ToolParam]: ...

    async def handle(self, arguments: dict, context: McpContext) -> list[TextContent]: ...


_tool_register: dict[str, type] = {}


def register_tool(cls) -> type:
    _tool_register[cls.tool_name()] = cls
    return cls


def discover_tools() -> None:
    import mcp_platform.tools as tools_pkg

    package_path = tools_pkg.__path__
    for _importer, module_name, _ispkg in pkgutil.iter_modules(package_path):
        full_name = f"mcp_platform.tools.{module_name}"
        try:
            importlib.import_module(full_name)
            logger.info(f"已发现 MCP 工具模块: {full_name}")
        except Exception as e:
            logger.error(f"加载 MCP 工具模块失败: {full_name}, 错误: {e}")


def get_all_tools() -> dict[str, type]:
    return dict(_tool_register)


def get_tool(name: str) -> type | None:
    return _tool_register.get(name)
