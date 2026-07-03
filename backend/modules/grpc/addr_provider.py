"""
ConfigService gRPC 地址 Provider

按 robot_id + target 维度解析地址：
- 默认实现 RobotConfigAddrProvider：从 robot.grpc_config JSON 字段取 agent / middleware / ros 三套地址
- 兜底实现 SettingsConfigAddrProvider：从 settings.GRPC.CONFIG_SERVICE_ADDR 读取（兼容旧逻辑）

切换实现：启动时调用 `set_config_addr_provider(...)` 即可，业务代码零改动。
"""
import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from sqlalchemy import select

from core.config import settings
from database.manager.async_manager import get_session
from database.models.business.robot import Robot

logger = logging.getLogger(__name__)


class ConfigServiceAddrProvider(ABC):
    """ConfigService gRPC 地址抽象接口（voice/speed/battery/face 共用）

    target ∈ {"agent", "middleware", "ros"}，对应 robot.grpc_config 的三个子键。
    """

    @abstractmethod
    async def get_addr(
        self, robot_id: Optional[int], target: str
    ) -> Optional[str]:
        """根据 robot_id + target 返回 host:port；未配置 / 未启用 / robot 不存在 → None"""
        raise NotImplementedError

    async def find_addrs_by_target(self, target: str) -> List[Tuple[int, str]]:
        """返回所有启用该 target 的 robot 列表 [(robot_id, host:port), ...]

        默认空列表，由支持广播的实现覆盖（如 RobotConfigAddrProvider）。
        """
        return []


class SettingsConfigAddrProvider(ConfigServiceAddrProvider):
    """兜底实现：忽略 robot_id / target，固定返回 settings 配置的地址"""

    async def get_addr(
        self, robot_id: Optional[int], target: str
    ) -> Optional[str]:
        return settings.GRPC.CONFIG_SERVICE_ADDR


class RobotConfigAddrProvider(ConfigServiceAddrProvider):
    """从 robot.grpc_config 解析地址的默认实现

    - get_addr：单 robot 维度，按 target 子键返回 host:port
    - find_addrs_by_target：广播维度，返回所有启用该 target 的 robot 地址
    """

    @staticmethod
    def _extract_addr(grpc_config: Optional[dict], target: str) -> Optional[str]:
        """从 grpc_config 字典里取 target 子键对应的 host:port；未启用 / 缺字段 → None"""
        sub = (grpc_config or {}).get(target) or {}
        if not sub.get("enabled"):
            return None
        host = sub.get("host")
        port = sub.get("port")
        if not host or port is None:
            return None
        return f"{host}:{port}"

    async def get_addr(
        self, robot_id: Optional[int], target: str
    ) -> Optional[str]:
        if robot_id is None:
            return None
        try:
            async for db in get_session():
                result = await db.execute(
                    select(Robot.grpc_config).where(
                        Robot.id == robot_id,
                        Robot.deleted_at.is_(None),
                    )
                )
                grpc_config = result.scalar_one_or_none()
                break
        except Exception:
            logger.exception(
                "query robot.grpc_config failed robot_id=%s target=%s",
                robot_id,
                target,
            )
            return None

        addr = self._extract_addr(grpc_config, target)
        if not addr:
            logger.debug(
                "grpc addr not configured or disabled robot_id=%s target=%s",
                robot_id,
                target,
            )
        return addr

    async def find_addrs_by_target(self, target: str) -> List[Tuple[int, str]]:
        try:
            async for db in get_session():
                result = await db.execute(
                    select(Robot.id, Robot.grpc_config).where(
                        Robot.deleted_at.is_(None),
                        Robot.grpc_config.isnot(None),
                    )
                )
                rows = result.all()
                break
        except Exception:
            logger.exception(
                "query robot.grpc_config list failed target=%s", target
            )
            return []

        out: List[Tuple[int, str]] = []
        for robot_id, grpc_config in rows:
            addr = self._extract_addr(grpc_config, target)
            if addr:
                out.append((robot_id, addr))
        return out

    async def find_addrs_by_target_and_map(
        self, target: str, map_id: int
    ) -> List[Tuple[int, str]]:
        """返回所有绑定指定 map 且启用 target 的 robot 地址 [(robot_id, host:port), ...]

        地图保存/切换时按 Robot.map_id 反查需要下发的机器人。
        """
        try:
            async for db in get_session():
                result = await db.execute(
                    select(Robot.id, Robot.grpc_config).where(
                        Robot.map_id == map_id,
                        Robot.deleted_at.is_(None),
                        Robot.grpc_config.isnot(None),
                    )
                )
                rows = result.all()
                break
        except Exception:
            logger.exception(
                "query robot.grpc_config by map failed target=%s map_id=%s",
                target,
                map_id,
            )
            return []

        out: List[Tuple[int, str]] = []
        for robot_id, grpc_config in rows:
            addr = self._extract_addr(grpc_config, target)
            if addr:
                out.append((robot_id, addr))
        return out


_addr_provider: ConfigServiceAddrProvider = RobotConfigAddrProvider()


def get_config_addr_provider() -> ConfigServiceAddrProvider:
    """获取当前生效的地址 Provider"""
    return _addr_provider


def set_config_addr_provider(provider: ConfigServiceAddrProvider) -> None:
    """注入新的地址 Provider（一般不调用，默认就是 RobotConfigAddrProvider）"""
    global _addr_provider
    _addr_provider = provider
