#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP 工具: code_execute
代码生成执行器，按计划批量创建字典、权限、菜单并分配角色
"""
import json
import logging

from mcp_server.registry import register_tool, ToolParam
from mcp_server.context import McpContext
from mcp_server.result import text_result_with_json, text_result_error
from mcp_server.types import TextContent
from mcp_server.http_client import McpHttpClient

logger = logging.getLogger(__name__)


@register_tool
class CodeExecute:
    @classmethod
    def tool_name(cls) -> str:
        return "code_execute"

    @classmethod
    def tool_description(cls) -> str:
        return "执行代码生成计划，按顺序创建字典→权限→菜单→角色分配。支持批量操作，自动处理层级关系"

    @classmethod
    def tool_params(cls) -> list[ToolParam]:
        return [
            ToolParam(name="executionPlan", description="JSON执行计划，含dicts(字典列表),permissions(权限列表),menus(菜单列表),roleMenuAssignments(角色菜单分配)", type="string", required=True),
            ToolParam(name="requirement", description="原始需求描述(用于日志)", type="string", required=False, default=""),
        ]

    async def handle(self, arguments: dict, context: McpContext) -> list[TextContent]:
        try:
            plan_raw = arguments.get("executionPlan", "{}")
            plan = json.loads(plan_raw)
            client = McpHttpClient()
            results = {"dicts": [], "permissions": [], "menus": [], "roleMenuAssignments": []}

            # Step 1: 创建字典
            for d in plan.get("dicts", []):
                try:
                    dict_result = await client.post("/admin/sys/dict", json_data={
                        "code": d["code"],
                        "name": d.get("name", d["code"]),
                        "description": d.get("description", ""),
                        "status": True,
                        "sort": d.get("sort", 0),
                    })
                    dict_data = dict_result.get("data", {})
                    dict_id = dict_data.get("id")

                    # 创建字典选项
                    items = []
                    for idx, opt in enumerate(d.get("items", [])):
                        try:
                            item_result = await client.post("/admin/sys/dict/item", json_data={
                                "dict_id": dict_id,
                                "label": opt.get("label", ""),
                                "value": str(opt.get("value", "")),
                                "status": True,
                                "sort": opt.get("sort", idx),
                            })
                            items.append(item_result.get("data", {}))
                        except Exception as e:
                            items.append({"label": opt.get("label"), "error": str(e)})
                    results["dicts"].append({"dict": dict_data, "items": items})
                except Exception as e:
                    results["dicts"].append({"code": d.get("code"), "error": str(e)})

            # Step 2: 创建权限
            for p in plan.get("permissions", []):
                try:
                    result = await client.post("/admin/sys/permission", json_data=p)
                    results["permissions"].append(result.get("data", {}))
                except Exception as e:
                    results["permissions"].append({"code": p.get("code"), "error": str(e)})

            # Step 3: 创建菜单（按层级排序，父先子后）
            name_to_id = {}
            for m in plan.get("menus", []):
                menu_data = {k: v for k, v in m.items() if k != "parent_name"}
                parent_name = m.get("parent_name")
                if parent_name and parent_name in name_to_id:
                    menu_data["parent_id"] = name_to_id[parent_name]
                try:
                    result = await client.post("/admin/sys/menu/add", json_data=menu_data)
                    data = result.get("data", {})
                    results["menus"].append(data)
                    if m.get("name"):
                        name_to_id[m["name"]] = data.get("id")
                except Exception as e:
                    results["menus"].append({"name": m.get("name"), "error": str(e)})

            # Step 4: 分配菜单给角色
            for assignment in plan.get("roleMenuAssignments", []):
                role_id = assignment.get("roleId")
                menu_ids = assignment.get("menuIds", [])
                try:
                    result = await client.post(
                        f"/admin/sys/role/{role_id}/menus",
                        json_data={"menu_ids": menu_ids},
                    )
                    results["roleMenuAssignments"].append({"roleId": role_id, "data": result.get("data", {})})
                except Exception as e:
                    results["roleMenuAssignments"].append({"roleId": role_id, "error": str(e)})

            return text_result_with_json(results)
        except json.JSONDecodeError as e:
            return text_result_error(f"JSON解析失败: {str(e)}")
        except Exception as e:
            return text_result_error(f"代码执行失败: {str(e)}")
