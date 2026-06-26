"""
gRPC channel 单例管理

支持运行时切换 MapService 地址：
- get_map_service_addr() / set_map_service_addr(addr) 用于读写当前地址
- 切换地址会关闭旧 channel 并清空 stub 缓存，下次 RPC 自动按新地址重建
- 仅内存级覆盖，重启后回到 .env 配置

ConfigService（voice/speed/battery/face）按地址缓存多通道：
- get_config_channel_by_addr(addr) 按 host:port 维度缓存 channel
- 不同 robot 的 grpc_config 地址不同时复用各自 channel，避免反复重建
- 地址由调用方（config_client._dispatch_with_target）通过 ConfigServiceAddrProvider 解析后传入
"""
import asyncio
import logging

import grpc

from core.config import settings

logger = logging.getLogger(__name__)

_channel: grpc.aio.Channel | None = None
_override_addr: str | None = None
_reconfigure_lock = asyncio.Lock()

# ConfigService 多通道缓存：按 host:port 维度缓存 channel
_config_channels: dict[str, grpc.aio.Channel] = {}
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


async def get_config_channel_by_addr(addr: str) -> grpc.aio.Channel:
    """按地址获取（惰性创建）ConfigService gRPC aio Channel

    不同地址（来自不同 robot 的 grpc_config）各自缓存独立 channel，
    并发安全（双检锁）。
    """
    if addr in _config_channels:
        return _config_channels[addr]
    async with _config_reconfigure_lock:
        if addr in _config_channels:
            return _config_channels[addr]
        logger.info("create grpc.aio.insecure_channel config addr=%s", addr)
        _config_channels[addr] = grpc.aio.insecure_channel(addr)
        return _config_channels[addr]


async def close_all_config_channels() -> None:
    """关闭所有 ConfigService 缓存 channel（应用 shutdown 时调用）"""
    async with _config_reconfigure_lock:
        for addr, ch in _config_channels.items():
            try:
                await ch.close()
                logger.info("grpc config channel closed addr=%s", addr)
            except Exception:
                logger.exception("close config channel failed addr=%s", addr)
        _config_channels.clear()


async def close_channel() -> None:
    """关闭并清理所有 channel（MapService 单例 + ConfigService 多通道），供应用 shutdown 时调用"""
    global _channel, _override_addr
    async with _reconfigure_lock:
        if _channel is not None:
            await _channel.close()
            _channel = None
            logger.info("grpc channel closed")
    await close_all_config_channels()
