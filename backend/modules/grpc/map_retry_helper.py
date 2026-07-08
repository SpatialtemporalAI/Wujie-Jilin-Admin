"""
地图类 gRPC 推送的重试 helper

被 retry_service._ROUTING 路由调用，把 grpc_retry_task 中 map 类任务
（保存地图 NotifyMapSaved / 切换地图 SwitchMap）重新下发到对应 robot。

与 config client 一样自包含（自行开 session 解析地址），返回统一 RetryCallResult：
- success=True  → 本次推送成功（任务置 completed）
- success=False → 失败（按退避重试或标 dead）
- cancel=True   → 地图已删除等终态，任务置 cancelled（不再重试也不标 dead）

设计要点：
- NotifyMapSaved 重试时按 map_id 重新查库重建 map_info（不存全量快照），
  规避 image_url 是带时效 HMAC 签名 URL、存快照会过期的问题；同时自然推送最新版本。
- 每个已配置 target（middleware/agent）独立下发；任一已配置 target 失败 → 整体失败。
- 无任何 target 配置时返回 success=True（空操作完成，避免无地址时无限重试）。
"""
import logging

from sqlalchemy import select

from database.manager.async_manager import get_session
from database.models.business.scene_map import SceneMap
from database.models.business.scene_map_annotation import SceneMapAnnotation
from modules.admin.services.sys.file_service import FileService
from modules.grpc.addr_provider import get_config_addr_provider
from modules.grpc.client import MapServiceClient
from modules.grpc.converter import scene_map_to_map_info
from modules.grpc.result import RetryCallResult

logger = logging.getLogger(__name__)


class MapRetryHelper:
    """地图类 gRPC 推送重试 helper（类方法风格，无需实例化）"""

    @classmethod
    async def notify_map_saved(
        cls, robot_id: int, map_id: int, version: int
    ) -> RetryCallResult:
        """重试保存地图推送：重建 map_info → 下发到 robot 的 middleware/agent"""
        # 1. 重建 map_info（自行开 session）
        map_info = None
        async for db in get_session():
            fresh = (
                await db.execute(
                    select(SceneMap).where(
                        SceneMap.id == map_id,
                        SceneMap.deleted_at.is_(None),
                    )
                )
            ).scalar_one_or_none()
            if fresh is None:
                return RetryCallResult(
                    success=False, cancel=True, message="地图已删除"
                )

            file_id = fresh.nav_image_id or fresh.image_id
            image_url = ""
            if file_id:
                image_url = await FileService.get_file_url(db, file_id) or ""

            annotations = (
                await db.execute(
                    select(SceneMapAnnotation)
                    .where(
                        SceneMapAnnotation.map_id == map_id,
                        SceneMapAnnotation.deleted_at.is_(None),
                    )
                    .order_by(SceneMapAnnotation.id.asc())
                )
            ).scalars().all()

            map_info = scene_map_to_map_info(fresh, image_url, annotations=annotations)
            break

        # 2. 下发到 middleware / agent
        attempted = 0
        failed: list[str] = []
        for target in ("middleware", "agent"):
            addr = await get_config_addr_provider().get_addr(robot_id, target)
            if not addr:
                continue
            attempted += 1
            resp = await MapServiceClient.notify_map_saved_one(
                map_info, robot_id, addr
            )
            if getattr(resp, "status", "") != "OK":
                failed.append(
                    f"{target}: {getattr(resp, 'message', '') or '设备未响应'}"
                )

        if not attempted:
            return RetryCallResult(success=True, message="无已配置 target，跳过")
        if failed:
            return RetryCallResult(success=False, message="; ".join(failed))
        return RetryCallResult(success=True)

    @classmethod
    async def switch_map(
        cls, robot_id: int, map_id: int, version: int
    ) -> RetryCallResult:
        """重试切换地图推送：下发 SwitchMap 到 robot 的 middleware/agent"""
        attempted = 0
        failed: list[str] = []
        for target in ("middleware", "agent"):
            addr = await get_config_addr_provider().get_addr(robot_id, target)
            if not addr:
                continue
            attempted += 1
            resp = await MapServiceClient.switch_map(map_id, version, addr)
            if getattr(resp, "status", "") != "OK":
                failed.append(
                    f"{target}: {getattr(resp, 'message', '') or '设备未响应'}"
                )

        if not attempted:
            return RetryCallResult(success=True, message="无已配置 target，跳过")
        if failed:
            return RetryCallResult(success=False, message="; ".join(failed))
        return RetryCallResult(success=True)
