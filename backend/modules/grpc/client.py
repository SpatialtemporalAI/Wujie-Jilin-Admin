"""
MapService gRPC 客户端

封装 NotifyMapSaved / SearchMaps / SwitchMap 三个 RPC：

地址路由（target 对应 robot.grpc_config 的子键）：
- NotifyMapSaved（点击保存触发）→ 按 robot.middleware **广播**：遍历所有
  `Robot.map_id == 当前地图` 且 middleware 启用的 robot，逐个用各自 addr 发送，
  任一成功即整体 status="OK"。复用 face_recognition 的广播模式。
- SwitchMap（改机器人地图绑定时触发）→ 按 robot_id 的 middleware 地址单发。
- SearchMaps（定时版本同步任务）→ 仍走全局单例 `settings.GRPC.MAP_SERVICE_ADDR`，
  无 robot 上下文。

统一处理：
- ENABLED 开关（关闭时静默跳过）
- stub 按 addr 缓存（与 ConfigService 共享 channel 池：同 addr 一个 TCP channel）
- 超时配置
"""
import logging
from typing import Dict, List, Tuple

import grpc

from app.grpc.generated.map import map_pb2, map_pb2_grpc

from core.config import settings
from modules.grpc.channel import get_channel, get_config_channel_by_addr

logger = logging.getLogger(__name__)


class MapServiceClient:
    """MapService gRPC 客户端（类方法风格，无需实例化）"""

    # 全局单例 stub：仅 search_maps（无 robot 上下文）使用
    _stub: map_pb2_grpc.MapServiceStub | None = None
    # 按 addr 缓存的 stub：notify_map_saved / switch_map 按 robot.middleware 地址下发
    _stubs_by_addr: Dict[str, map_pb2_grpc.MapServiceStub] = {}

    @classmethod
    def _stub_(cls) -> map_pb2_grpc.MapServiceStub:
        if cls._stub is None:
            cls._stub = map_pb2_grpc.MapServiceStub(get_channel())
        return cls._stub

    @classmethod
    async def _get_stub_for_addr(
        cls, addr: str
    ) -> map_pb2_grpc.MapServiceStub:
        """按 addr 获取（惰性创建）MapService stub；与 ConfigService 共享 channel 池"""
        if addr not in cls._stubs_by_addr:
            channel = await get_config_channel_by_addr(addr)
            cls._stubs_by_addr[addr] = map_pb2_grpc.MapServiceStub(channel)
        return cls._stubs_by_addr[addr]

    @classmethod
    async def notify_map_saved_one(
        cls,
        map_info: map_pb2.MapInfo,
        robot_id: int,
        addr: str,
    ) -> map_pb2.NotifyMapSavedResponse:
        """单机器人单地址下发 NotifyMapSaved（广播与重试共用）

        addr 为空返回 DISABLED 哨兵；调用方据此判断是否入重试队列。
        成功返回 status=OK；gRPC 错误/异常被吞，返回 status=ERROR 的响应（不抛）。
        """
        if not settings.GRPC.ENABLED:
            return map_pb2.NotifyMapSavedResponse(
                status="DISABLED", message="gRPC 未启用"
            )
        if not addr:
            return map_pb2.NotifyMapSavedResponse(
                status="DISABLED", message="middleware 地址未配置"
            )

        request = map_pb2.NotifyMapSavedRequest(map_info=map_info)
        try:
            stub = await cls._get_stub_for_addr(addr)
            resp = await stub.NotifyMapSaved(
                request, timeout=settings.GRPC.TIMEOUT_SECONDS
            )
            if getattr(resp, "status", "") == "OK":
                logger.info(
                    "notify_map_saved ok map_id=%s version=%s robot_id=%s addr=%s",
                    map_info.id,
                    map_info.version,
                    robot_id,
                    addr,
                )
            else:
                logger.warning(
                    "notify_map_saved failed map_id=%s robot_id=%s addr=%s status=%s msg=%s",
                    map_info.id,
                    robot_id,
                    addr,
                    getattr(resp, "status", ""),
                    getattr(resp, "message", "") or "设备未响应",
                )
            return resp
        except grpc.aio.AioRpcError as e:
            logger.warning(
                "notify_map_saved rpc error map_id=%s robot_id=%s addr=%s code=%s details=%s",
                map_info.id,
                robot_id,
                addr,
                e.code(),
                e.details(),
            )
            return map_pb2.NotifyMapSavedResponse(
                status="ERROR", message=f"gRPC 调用失败: {e.code().name}"
            )
        except Exception as e:  # noqa: BLE001 - 兜底，不抛
            logger.exception(
                "notify_map_saved raised map_id=%s robot_id=%s addr=%s",
                map_info.id,
                robot_id,
                addr,
            )
            return map_pb2.NotifyMapSavedResponse(
                status="ERROR", message=f"gRPC 调用异常: {e}"
            )

    @classmethod
    async def notify_map_saved(
        cls,
        map_info: map_pb2.MapInfo,
        targets: List[Tuple[int, str]],
    ) -> map_pb2.NotifyMapSavedResponse:
        """通知导览服务地图已保存，推送完整 MapInfo——按 robot.middleware 广播

        targets: [(robot_id, host:port), ...]，由调用方按 Robot.map_id 反查得到。
        任一成功即整体 status="OK"；无 target 返回 SKIPPED；全部失败返回 ERROR。
        每个目标独立调用 notify_map_saved_one，互不影响。
        """
        if not settings.GRPC.ENABLED:
            return map_pb2.NotifyMapSavedResponse(
                status="DISABLED", message="gRPC 未启用"
            )
        if not targets:
            return map_pb2.NotifyMapSavedResponse(
                status="SKIPPED", message="无绑定该地图的机器人"
            )

        success_any = False
        last_msg = "全部失败"
        for robot_id, addr in targets:
            resp = await cls.notify_map_saved_one(map_info, robot_id, addr)
            if getattr(resp, "status", "") == "OK":
                success_any = True
            else:
                last_msg = getattr(resp, "message", "") or "设备未响应"

        if success_any:
            return map_pb2.NotifyMapSavedResponse(status="OK", message="ok")
        return map_pb2.NotifyMapSavedResponse(status="ERROR", message=last_msg)

    @classmethod
    async def search_maps(cls) -> list[map_pb2.MapSummary]:
        """拉取导览服务已知的所有地图摘要（id + version）

        无 robot 上下文，仍走全局单例 channel（settings.GRPC.MAP_SERVICE_ADDR）。
        """
        if not settings.GRPC.ENABLED:
            return []
        resp: map_pb2.SearchMapsResponse = await cls._stub_().SearchMaps(
            map_pb2.SearchMapsRequest(),
            timeout=settings.GRPC.TIMEOUT_SECONDS,
        )
        return list(resp.maps)

    @classmethod
    async def switch_map(
        cls, map_id: str | int, version: str | int, addr: str
    ) -> map_pb2.SwitchMapResponse:
        """切换机器人当前地图到指定 id + version（发往该 robot 的 middleware addr）

        addr 为空（middleware 未配置）时返回 DISABLED 哨兵，由调用方决定是否记日志。
        """
        if not settings.GRPC.ENABLED:
            return map_pb2.SwitchMapResponse(
                status="DISABLED", message="gRPC 未启用"
            )
        if not addr:
            return map_pb2.SwitchMapResponse(
                status="DISABLED", message="middleware 地址未配置"
            )
        stub = await cls._get_stub_for_addr(addr)
        return await stub.SwitchMap(
            map_pb2.SwitchMapRequest(id=str(map_id), version=str(version)),
            timeout=settings.GRPC.TIMEOUT_SECONDS,
        )
