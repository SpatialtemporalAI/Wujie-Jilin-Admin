"""
MapService gRPC 客户端

封装 NotifyMapSaved / SearchMaps 两个 RPC，统一处理：
- ENABLED 开关（关闭时静默跳过）
- 单例 stub 复用
- 超时配置
"""
import logging

from app.grpc.generated.map import map_pb2, map_pb2_grpc

from core.config import settings
from modules.grpc.channel import get_channel

logger = logging.getLogger(__name__)


class MapServiceClient:
    """MapService gRPC 客户端（类方法风格，无需实例化）"""

    _stub: map_pb2_grpc.MapServiceStub | None = None

    @classmethod
    def _stub_(cls) -> map_pb2_grpc.MapServiceStub:
        if cls._stub is None:
            cls._stub = map_pb2_grpc.MapServiceStub(get_channel())
        return cls._stub

    @classmethod
    async def notify_map_saved(
        cls, map_info: map_pb2.MapInfo
    ) -> map_pb2.NotifyMapSavedResponse:
        """通知导览服务地图已保存，推送完整 MapInfo"""
        if not settings.GRPC.ENABLED:
            return map_pb2.NotifyMapSavedResponse(
                status="DISABLED", message="gRPC 未启用"
            )
        return await cls._stub_().NotifyMapSaved(
            map_pb2.NotifyMapSavedRequest(map_info=map_info),
            timeout=settings.GRPC.TIMEOUT_SECONDS,
        )

    @classmethod
    async def search_maps(cls) -> list[map_pb2.MapSummary]:
        """拉取导览服务已知的所有地图摘要（id + version）"""
        if not settings.GRPC.ENABLED:
            return []
        resp: map_pb2.SearchMapsResponse = await cls._stub_().SearchMaps(
            map_pb2.SearchMapsRequest(),
            timeout=settings.GRPC.TIMEOUT_SECONDS,
        )
        return list(resp.maps)
