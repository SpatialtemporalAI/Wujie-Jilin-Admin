#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP 工具: code_review
代码审查，对比需求与生成结果
"""
import json

from mcp_server.registry import register_tool, ToolParam
from mcp_server.context import McpContext
from mcp_server.result import text_result_with_json, text_result_error
from mcp_server.types import TextContent


@register_tool
class CodeReview:
    @classmethod
    def tool_name(cls) -> str:
        return "code_review"

    @classmethod
    def tool_description(cls) -> str:
        return "审查生成的代码/配置是否满足原始需求，检查菜单、权限、字典、角色分配的覆盖情况，生成调整指导"

    @classmethod
    def tool_params(cls) -> list[ToolParam]:
        return [
            ToolParam(name="userRequirement", description="原始需求描述(经requirement_analyzer处理后的)", type="string", required=True),
            ToolParam(name="generatedFiles", description="JSON数组，gva_execute/code_execute生成的结果描述", type="string", required=True),
        ]

    async def handle(self, arguments: dict, context: McpContext) -> list[TextContent]:
        try:
            requirement = arguments.get("userRequirement", "")
            files_raw = arguments.get("generatedFiles", "[]")
            generated_files = json.loads(files_raw)
            if isinstance(generated_files, dict):
                generated_files = [generated_files]

            return text_result_with_json({
                "requirement": requirement,
                "review": {
                    "instructions": (
                        "请根据以下需求与生成结果，进行审查：\n\n"
                        "1. 完整性检查：\n"
                        "   - menus: 需要的菜单是否全部创建？使用 list_all_menus 验证\n"
                        "   - permissions: 需要的权限是否全部创建？使用 list_all_permissions 验证\n"
                        "   - dictionaries: 需要的字典是否全部创建？使用 query_dictionaries 验证\n"
                        "   - roleAssignments: 角色权限是否已正确分配？\n\n"
                        "2. 如有不满足的情况：\n"
                        "   - 缺少菜单: 调用 create_menu 补充\n"
                        "   - 缺少权限: 调用 create_permission 补充\n"
                        "   - 缺少字典: 调用 generate_dictionary 补充\n"
                        "   - 缺少角色分配: 调用 assign_menus_to_role 补充\n\n"
                        "3. 注意事项：\n"
                        "   - 菜单层级关系是否正确（parent_id 是否对应）\n"
                        "   - 权限的 resource_path 和 method 是否与实际 API 匹配\n"
                        "   - 字典选项是否完整"
                    ),
                    "generatedFiles": generated_files,
                    "checklist": {
                        "menus": {"status": "pending", "action": "使用 list_all_menus 检查"},
                        "permissions": {"status": "pending", "action": "使用 list_all_permissions 检查"},
                        "dictionaries": {"status": "pending", "action": "使用 query_dictionaries 检查"},
                        "roleAssignments": {"status": "pending", "action": "对比需求中的角色分配要求"},
                    },
                },
            })
        except json.JSONDecodeError as e:
            return text_result_error(f"JSON解析失败: {str(e)}")
        except Exception as e:
            return text_result_error(f"审查失败: {str(e)}")
