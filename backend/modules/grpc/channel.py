"""
gRPC channel 单例管理

支持运行时切换 MapService 地址：
- get_map_service_addr() / set_map_service_addr(addr) 用于读写当前地址
- 切换地址会关闭旧 channel 并清空 stub 缓存，下次 RPC 自动按新地址重建
- 仅内存级覆盖，重启后回到 .env 配置

ConfigService（voice/speed/battery/face）使用独立的 channel：
- get_config_channel() 通过 ConfigServiceAddrProvider 获取地址
- 默认从 settings.GRPC.CONFIG_SERVICE_ADDR 读取，将来可注入数据库实现
"""
import asyncio
import logging

import grpc

from core.config import settings
from modules.grpc.addr_provider import get_config_addr_provider

logger = logging.getLogger(__name__)

_channel: grpc.aio.Channel | None = None
_override_addr: str | None = None
_reconfigure_lock = asyncio.Lock()

# ConfigService 独立 channel（与 MapService 解耦，地址来自 Provider）
_config_channel: grpc.aio.Channel | None = None
_config_channel_addr: str | None = None
_config_reconfigure_lock = asyncio.Lock()


def get_map_service_addr() -> str:
    """当前生效的 MapService 地址（运行时覆盖 > settings 配置）"""
    return _override_addr or settings.GRPC.MAP_SERVICE_ADDR


def get_channel() -> grpc.aio.Channel:
    """获取（惰性创建）单例 gRPC aio Channel"""
    global _channel
    if _channel is None:
        addr = get_map_service_addr()
        logger.info("create grpc.aio.insecure_channel addr=%s", addr)
        _channel = grpc.aio.insecure_channel(addr)
    return _channel


async def set_map_service_addr(addr: str) -> str:
    """运行时切换 MapService 地址

    流程：关闭旧 channel -> 清空 stub 缓存 -> 写入运行时地址。
    下次 RPC 调用会自动按新地址重建 channel 与 stub。
    并发安全（asyncio.Lock）；正在进行的 RPC 会被中断。

    Returns:
        切换后的地址（便于日志/响应回显）
    """
    global _channel, _override_addr

    # 延迟导入避免循环依赖
    from modules.grpc.client import MapServiceClient

    new_addr = (addr or "").strip()
    if not new_addr:
        raise ValueError("MapService 地址不能为空")

    async with _reconfigure_lock:
        old_addr = get_map_service_addr()
        if new_addr == old_addr and _channel is not None:
            logger.debug("set_map_service_addr noop: addr unchanged %s", new_addr)
            return new_addr

        if _channel is not None:
            await _channel.close()
            _channel = None
            logger.info("grpc channel closed for reconfigure")

        # 清空 stub 缓存，下次 _stub_() 重建
        MapServiceClient._stub = None

        _override_addr = new_addr
        logger.info("grpc MapService addr switched: %s -> %s", old_addr, new_addr)
        return new_addr


async def close_channel() -> None:
    """关闭并清理 channel，供应用 shutdown 时调用"""
    global _channel, _override_addr, _config_channel, _config_channel_addr
    async with _reconfigure_lock:
        if _channel is not None:
            await _channel.close()
            _channel = None
            logger.info("grpc channel closed")
    async with _config_reconfigure_lock:
        if _config_channel is not None:
            await _config_channel.close()
            _config_channel = None
            _config_channel_addr = None
            logger.info("grpc config channel closed")


async def get_config_channel() -> grpc.aio.Channel:
    """获取（惰性创建）ConfigService 单例 gRPC aio Channel

    地址由 ConfigServiceAddrProvider 提供（默认 settings，可注入数据库实现）。
    若 Provider 返回的地址与缓存不一致，关闭旧 channel 并重建。
    """
    global _config_channel, _config_channel_addr
    provider = get_config_addr_provider()
    addr = await provider.get_addr()
    if _config_channel is not None and _config_channel_addr == addr:
        return _config_channel
    async with _config_reconfigure_lock:
        # 双检锁：进入锁后再核对一次
        if _config_channel is not None and _config_channel_addr == addr:
            return _config_channel
        if _config_channel is not None:
            await _config_channel.close()
            logger.info(
                "grpc config channel closed for reconfigure: %s -> %s",
                _config_channel_addr,
                addr,
            )
        logger.info("create grpc.aio.insecure_channel config addr=%s", addr)
        _config_channel = grpc.aio.insecure_channel(addr)
        _config_channel_addr = addr
        return _config_channel
