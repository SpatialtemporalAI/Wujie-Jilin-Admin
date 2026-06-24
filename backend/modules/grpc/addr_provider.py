"""
ConfigService gRPC 地址 Provider

抽象出地址来源，便于将来从数据库表读取（按 robot_id 维度等）。
当前默认实现从 settings.GRPC.CONFIG_SERVICE_ADDR 读取。

切换实现：启动时调用 `set_config_addr_provider(DbConfigAddrProvider())` 即可，
业务代码（channel.py / config_client.py）零改动。
"""
from abc import ABC, abstractmethod

from core.config import settings


class ConfigServiceAddrProvider(ABC):
    """ConfigService gRPC 地址抽象接口（voice/speed/battery/face 共用）"""

    @abstractmethod
    async def get_addr(self) -> str:
        """返回当前生效的地址 host:port"""
        raise NotImplementedError


class SettingsConfigAddrProvider(ConfigServiceAddrProvider):
    """默认实现：从 settings.GRPC.CONFIG_SERVICE_ADDR 读取"""

    async def get_addr(self) -> str:
        return settings.GRPC.CONFIG_SERVICE_ADDR


_addr_provider: ConfigServiceAddrProvider = SettingsConfigAddrProvider()


def get_config_addr_provider() -> ConfigServiceAddrProvider:
    """获取当前生效的地址 Provider"""
    return _addr_provider


def set_config_addr_provider(provider: ConfigServiceAddrProvider) -> None:
    """注入新的地址 Provider（例如启动时切到数据库实现）"""
    global _addr_provider
    _addr_provider = provider
