#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP 工具: requirement_analyzer
智能需求分析与模块设计，返回结构化分析指导
"""
from mcp_server.registry import register_tool, ToolParam
from mcp_server.context import McpContext
from mcp_server.result import text_result_with_json
from mcp_server.types import TextContent


@register_tool
class RequirementAnalyzer:
    @classmethod
    def tool_name(cls) -> str:
        return "requirement_analyzer"

    @classmethod
    def tool_description(cls) -> str:
        return "深度分析用户需求，识别核心业务实体、流程和数据关系，输出结构化模块设计指导（菜单、权限、字典、角色分配建议）"

    @classmethod
    def tool_params(cls) -> list[ToolParam]:
        return [
            ToolParam(name="userRequirement", description="用户自然语言需求描述", type="string", required=True),
        ]

    async def handle(self, arguments: dict, context: McpContext) -> list[TextContent]:
        requirement = arguments.get("userRequirement", "")
        return text_result_with_json({
            "requirement": requirement,
            "analysis": {
                "instructions": (
                    "请根据以上需求，分析并规划以下内容：\n"
                    "1. moduleDesign: 模块设计（模块名、描述、父级菜单位置）\n"
                    "2. suggestedMenus: 建议的菜单列表（name/path/component/type/meta_title/sort）\n"
                    "3. suggestedPermissions: 建议的权限列表（name/code/resource_path/method/category）\n"
                    "4. suggestedDictionaries: 建议的字典列表（code/name/items）\n"
                    "5. suggestedRoleAssignments: 建议的角色分配（roleName/menuNames）\n"
                    "6. executionOrder: 推荐的执行顺序\n\n"
                    "原则：\n"
                    "- 不随意发散，不添加用户未提及的功能\n"
                    "- 每个菜单需要对应合理的路由path和组件component\n"
                    "- 权限需覆盖 CRUD 操作（GET/POST/PUT/DELETE）\n"
                    "- 字典用于枚举类型字段\n"
                    "- 使用 system_analyze 查看现有资源避免重复"
                ),
                "outputFormat": {
                    "moduleDesign": {
                        "moduleName": "string",
                        "description": "string",
                        "parentMenu": "string | null",
                    },
                    "suggestedMenus": [
                        {
                            "name": "string (路由name)",
                            "path": "string (路由path)",
                            "component": "string (Vue组件路径)",
                            "type": "catalog | menu | button | external",
                            "meta_title": "string (显示标题)",
                            "meta_icon": "string (图标)",
                            "sort": "number",
                            "parent_name": "string | null (父菜单name引用)",
                        }
                    ],
                    "suggestedPermissions": [
                        {
                            "name": "string",
                            "code": "string (唯一编码)",
                            "resource_path": "string (API路径)",
                            "method": "GET | POST | PUT | DELETE",
                            "category": "string (分类)",
                        }
                    ],
                    "suggestedDictionaries": [
                        {
                            "code": "string",
                            "name": "string",
                            "items": [{"label": "string", "value": "string"}],
                        }
                    ],
                    "suggestedRoleAssignments": [
                        {"roleName": "string", "menuNames": ["string"]},
                    ],
                    "executionOrder": ["create_dicts", "create_permissions", "create_menus", "assign_roles"],
                },
            },
        })
