"""
NavigationService gRPC 客户端

商户开放 API（goto_point / navigate_route）的即时导航下发，按 robot.agent 地址单发：
- navigate_to_point：单点导航
- navigate_route：多点按序导航

调用约定（对齐 config_client._dispatch_with_target）：
- GRPC.ENABLED=false → 返回 success=False 哨兵，不抛异常
- robot.grpc_config[agent] 缺失 / enabled=false / 无 host:port → success=False 哨兵
- gRPC 调用失败 → 返回 success=False 失败响应，不抛异常
- 业务层（OpenApiService）据此组装返回文案，而非冒泡 500
"""
import logging
from typing import Any, Dict, List

from app.grpc.generated.navigation import navigation_pb2, navigation_pb2_grpc

from modules.grpc.config_client import _dispatch_with_target
from modules.grpc.channel import get_config_channel_by_addr

logger = logging.getLogger(__name__)


def _build_point(p: Dict[str, Any]) -> navigation_pb2.NavigationPoint:
    """从 dict 构造 NavigationPoint proto（缺失字段走 proto 默认值）"""
    return navigation_pb2.NavigationPoint(
        point_id=int(p.get("point_id") or 0),
        name=str(p.get("name") or ""),
        x=float(p.get("x") or 0.0),
        y=float(p.get("y") or 0.0),
        angle=float(p.get("angle") or 0.0),
    )


class NavigationClient:
    """即时导航 gRPC 客户端（走 agent）"""

    _stubs_by_addr: Dict[str, navigation_pb2_grpc.NavigationServiceStub] = {}

    @classmethod
    async def _get_stub_for_addr(
        cls, addr: str
    ) -> navigation_pb2_grpc.NavigationServiceStub:
        if addr not in cls._stubs_by_addr:
            channel = await get_config_channel_by_addr(addr)
            cls._stubs_by_addr[addr] = navigation_pb2_grpc.NavigationServiceStub(channel)
        return cls._stubs_by_addr[addr]

    @classmethod
    async def navigate_to_point(
        cls, robot_id: int, map_id: int, point: Dict[str, Any]
    ) -> navigation_pb2.NavigateToPointResponse:
        """单点导航：把目标点位下发到 robot.agent"""
        request = navigation_pb2.NavigateToPointRequest(
            robot_id=robot_id,
            map_id=map_id,
            point=_build_point(point),
        )
        return await _dispatch_with_target(
            robot_id=robot_id,
            target="agent",
            stub_factory=cls._get_stub_for_addr,
            method_name="NavigateToPoint",
            request=request,
            failure_factory=lambda msg: navigation_pb2.NavigateToPointResponse(
                success=False, message=msg
            ),
            log_ctx={
                "robot_id": robot_id,
                "rpc": "navigate_to_point",
                "map_id": map_id,
                "point_id": point.get("point_id"),
            },
        )

    @classmethod
    async def navigate_route(
        cls, robot_id: int, map_id: int, points: List[Dict[str, Any]]
    ) -> navigation_pb2.NavigateRouteResponse:
        """多点导航：按顺序途经多个点位，下发到 robot.agent"""
        request = navigation_pb2.NavigateRouteRequest(
            robot_id=robot_id,
            map_id=map_id,
            points=[_build_point(p) for p in points],
        )
        return await _dispatch_with_target(
            robot_id=robot_id,
            target="agent",
            stub_factory=cls._get_stub_for_addr,
            method_name="NavigateRoute",
            request=request,
            failure_factory=lambda msg: navigation_pb2.NavigateRouteResponse(
                success=False, message=msg
            ),
            log_ctx={
                "robot_id": robot_id,
                "rpc": "navigate_route",
                "map_id": map_id,
                "point_count": len(points),
            },
        )
