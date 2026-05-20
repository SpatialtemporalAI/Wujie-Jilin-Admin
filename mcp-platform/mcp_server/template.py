#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP 工具代码模板生成器
根据用户输入（名称、描述、参数、响应类型）生成 Python 工具代码
"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

TEMPLATE = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP 工具: {tool_name}
{tool_description}
自动生成 - 请根据业务需要修改 handle 方法
"""
from mcp_server.registry import register_tool, ToolParam
from mcp_server.context import McpContext
from mcp_server.result import text_result, text_result_with_json, text_result_error
from mcp_server.types import TextContent


@register_tool
class {class_name}:
    @classmethod
    def tool_name(cls) -> str:
        return "{tool_name}"

    @classmethod
    def tool_description(cls) -> str:
        return "{tool_description}"

    @classmethod
    def tool_params(cls) -> list[ToolParam]:
        return [{params}]

    async def handle(self, arguments: dict, context: McpContext) -> list[TextContent]:
        """
        工具处理逻辑
        TODO: 请根据业务需要实现此方法
        """
        {param_extracts}
        # TODO: 实现业务逻辑
        result = {{
            "message": "工具 {tool_name} 执行成功",
            "arguments": arguments,
        }}
        return text_result_with_json(result)
'''


def _to_class_name(tool_name: str) -> str:
    return "".join(word.capitalize() for word in tool_name.replace("-", "_").split("_"))


def generate_tool_code(
    name: str,
    description: str,
    params: list[dict],
) -> str:
    """生成工具 Python 代码"""
    class_name = _to_class_name(name)

    param_lines = []
    param_extracts = []
    for p in params:
        p_name = p["name"]
        p_desc = p.get("description", "")
        p_type = p.get("type", "string")
        p_required = p.get("required", True)
        p_default = p.get("default")

        default_repr = repr(p_default) if p_default is not None else "None"
        param_lines.append(
            f'        ToolParam(name="{p_name}", description="{p_desc}", '
            f'type="{p_type}", required={p_required}, default={default_repr}),'
        )
        param_extracts.append(
            f'        {p_name} = arguments.get("{p_name}"'
            f'{", " + repr(p_default) if p_default is not None else ""})'
        )

    return TEMPLATE.format(
        tool_name=name,
        tool_description=description,
        class_name=class_name,
        params="\n".join(param_lines),
        param_extracts="\n".join(param_extracts),
    )


def write_tool_file(name: str, code: str) -> str:
    """将工具代码写入 tools/ 目录，返回文件路径"""
    tools_dir = Path(__file__).resolve().parent / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)

    file_name = f"{name.replace('-', '_')}.py"
    file_path = tools_dir / file_name

    if file_path.exists():
        logger.warning(f"工具文件已存在，将覆盖: {file_path}")

    file_path.write_text(code, encoding="utf-8")
    logger.info(f"工具代码已生成: {file_path}")
    return str(file_path)
