#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP 独立服务配置
通过环境变量或 .env 文件加载
"""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MCPSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    NAME: str = Field("SmileX MCP Server", description="MCP 服务器名称")
    HOST: str = Field("127.0.0.1", description="服务监听地址")
    PORT: int = Field(9001, description="服务监听端口")
    UPSTREAM_BASE_URL: str = Field("http://127.0.0.1:8000", description="上游应用 URL")
    AUTH_HEADER: str = Field("Authorization", description="鉴权 Header 名称")
    REQUEST_TIMEOUT: int = Field(30, description="请求超时时间(秒)")


settings = MCPSettings()
