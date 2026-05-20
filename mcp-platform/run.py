#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP 独立服务入口
启动方式: python run.py
"""
import logging
import signal
import sys

import uvicorn

from mcp_server.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)

# 全局 uvicorn Server 引用，供信号处理器使用
_server: uvicorn.Server | None = None


def _signal_handler(signum: int, frame):
    """捕获 SIGINT/SIGTERM，触发 uvicorn 优雅关闭"""
    name = signal.Signals(signum).name
    logger.info("收到信号 %s，开始优雅关闭...", name)
    if _server is not None:
        _server.should_exit = True


def _install_signal_handlers():
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)


if __name__ == "__main__":
    _install_signal_handlers()

    config = uvicorn.Config(
        "mcp_server.server:create_app",
        host=settings.HOST,
        port=settings.PORT,
        factory=True,
        reload=False,
        log_level="info",
        timeout_graceful_shutdown=10,
    )
    _server = uvicorn.Server(config)
    logger.info(
        "MCP 服务启动中 → %s:%d (graceful shutdown timeout=10s)",
        settings.HOST,
        settings.PORT,
    )
    _server.run()
    logger.info("MCP 服务已完全停止")
