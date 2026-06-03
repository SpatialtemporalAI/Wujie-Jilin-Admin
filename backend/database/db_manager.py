from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from core.config import settings
import logging
from . import init_async_pool, close_async_pool, get_session
from .utils.timezone import configure as configure_tz

logger = logging.getLogger(__name__)


async def init_pool():
    """
    初始化异步数据库连接池
    """
    configure_tz(
        timezone_str=settings.DATETIME.TIMEZONE,
        format_str=settings.DATETIME.FORMAT,
    )
    await init_async_pool(settings.DATABASE)

    logger.info("异步数据库连接池初始化完成")


async def close_pool():
    """
    关闭异步数据库连接池
    """
    await close_async_pool()
    logger.info("异步数据库连接池关闭完成")
