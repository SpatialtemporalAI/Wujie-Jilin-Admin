#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
项目入口文件
初始化FastAPI应用并注册各个模块
"""
from contextlib import asynccontextmanager
from typing import Union
import asyncio
from fastapi import FastAPI
from core.config import settings  # 导入配置
from logging import getLogger
from database.db_manager import init_pool, close_pool
from core.redis import RedisPool

from modules.app.router import router as app_app_router
from modules.admin.router import router as admin_app_router
from core.registry.setup_registry import setup_app

logger = getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()
    # 初始化数据库连接池
    logger.info("初始化数据库连接池")
    await init_pool()
    logger.info("数据库连接池初始化完成")
    # 初始化 Redis 连接池
    logger.info("初始化 Redis 连接池")
    await RedisPool.init_pool()
    logger.info("Redis 连接池初始化完成")
    yield
    # 关闭 Redis 连接池
    logger.info("关闭 Redis 连接池")
    await RedisPool.close_pool()
    logger.info("Redis 连接池已关闭")
    # 关闭数据库连接池
    logger.info("关闭数据库连接池")
    await close_pool()
    logger.info("数据库连接池已关闭")


app = FastAPI(
    title="SmileX_Cloud",
    description="这是一个使用FastAPI构建的示例API",
    version="1.0.0",
    contact={
        "name": "SpatialtemporalAI",
        "url": "https://github.com/orgs/SpatialtemporalAI/dashboard",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan,
    docs_url=None if settings.ENVIR == "prod" and not settings.SERVICE.OPENAPI_ENABLE_IN_PROD else "/docs",
    redoc_url=None if settings.ENVIR == "prod" and not settings.SERVICE.OPENAPI_ENABLE_IN_PROD else "/redoc",
    openapi_url=None if settings.ENVIR == "prod" and not settings.SERVICE.OPENAPI_ENABLE_IN_PROD else "/openapi.json",
)
# 配置app
setup_app(app, settings=settings)
logger.info("配置文件初始化完成")

# 挂载 MCP ASGI 子应用
if settings.MCP.ENABLED:
    from mcp_platform.server import create_mcp_server
    mcp_server = create_mcp_server()
    app.mount("/mcp", mcp_server.streamable_http_app())
    logger.info("MCP 服务已挂载到 /mcp")

# 挂载子应用
# app.mount("/admin", admin_app)
# app.mount("/app", app_app)
# 挂载认证路由
app.include_router(app_app_router)
app.include_router(admin_app_router)


if __name__ == "__main__":
    """
    主函数，用于直接运行应用
    添加Ctrl+C监听，实现优雅退出
    """
    import signal
    import uvicorn

    # 定义信号处理函数
    def signal_handler(signum, frame):
        """
        信号处理函数，用于处理Ctrl+C信号
        """
        logger.info("收到退出信号，正在优雅关闭应用...")
        # 这里不需要手动调用关闭函数，因为lifespan会处理
        # 我们只需要记录日志，让uvicorn正常关闭即可

    # 注册信号处理函数
    signal.signal(signal.SIGINT, signal_handler)  # 处理Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # 处理kill命令

    # 运行应用
    logger.info("启动应用...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
