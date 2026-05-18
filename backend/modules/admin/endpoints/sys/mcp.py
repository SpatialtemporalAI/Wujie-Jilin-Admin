#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP 管理接口
"""
import logging
from typing import List

from fastapi import APIRouter

from core.response.response_schema import ResponseModel
from modules.admin.services.sys.mcp_service import MCPService
from modules.admin.schemas.sys.mcp import (
    AutoMcpToolCreate,
    McpToolInfo,
    McpToolTestRequest,
    McpServerStatusResponse,
)

logger = logging.getLogger(__name__)

mcp_router = APIRouter(prefix="/mcp", tags=["MCP管理"])


@mcp_router.post("/add", response_model=ResponseModel)
async def create_mcp_tool(tool_create: AutoMcpToolCreate):
    """创建 MCP 工具（从模板生成代码）"""
    logger.info(f"创建 MCP 工具: {tool_create.name}")
    result = await MCPService.create_tool(tool_create)
    return ResponseModel(data=result, msg="MCP 工具创建成功")


@mcp_router.post("/status", response_model=ResponseModel[McpServerStatusResponse])
async def get_mcp_status():
    """获取 MCP 服务器状态"""
    logger.info("获取 MCP 服务器状态")
    status = await MCPService.get_server_status()
    return ResponseModel(data=status)


@mcp_router.post("/start", response_model=ResponseModel)
async def start_mcp_server():
    """启动 MCP 独立服务"""
    logger.info("启动 MCP 独立服务")
    result = await MCPService.start_server()
    return ResponseModel(data=result, msg="MCP 服务启动成功")


@mcp_router.post("/stop", response_model=ResponseModel)
async def stop_mcp_server():
    """停止 MCP 独立服务"""
    logger.info("停止 MCP 独立服务")
    result = await MCPService.stop_server()
    return ResponseModel(data=result, msg="MCP 服务已停止")


@mcp_router.post("/list", response_model=ResponseModel[List[McpToolInfo]])
async def list_mcp_tools():
    """获取已注册工具列表"""
    logger.info("获取 MCP 工具列表")
    tools = await MCPService.list_tools()
    return ResponseModel(data=tools)


@mcp_router.post("/routes", response_model=ResponseModel)
async def list_mcp_routes():
    """获取 MCP 路由信息"""
    logger.info("获取 MCP 路由信息")
    routes = await MCPService.list_routes()
    return ResponseModel(data=routes)


@mcp_router.post("/test", response_model=ResponseModel)
async def test_mcp_tool(test_request: McpToolTestRequest):
    """测试 MCP 工具"""
    logger.info(f"测试 MCP 工具: {test_request.tool_name}")
    result = await MCPService.test_tool(test_request)
    return ResponseModel(data=result)
