#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP 独立服务入口
启动方式: python run.py
"""
import logging
import uvicorn

from mcp_server.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

if __name__ == "__main__":
    uvicorn.run(
        "mcp_server.server:create_app",
        host=settings.HOST,
        port=settings.PORT,
        factory=True,
        reload=True,
    )
