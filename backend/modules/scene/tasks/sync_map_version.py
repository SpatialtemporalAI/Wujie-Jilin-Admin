"""
定时任务：同步导览服务地图版本

每分钟调用 MapService.SearchMaps，拉取导览服务各地图版本号，
回填到 scene_map.target_version，用于在前端展示「同步状态」。
"""
import logging

from sqlalchemy import select

from database.models.business.scene_map import SceneMap
from modules.grpc.client import MapServiceClient
from modules.scheduler.core.registry import scheduled_task

logger = logging.getLogger(__name__)


@scheduled_task(
    cron="* * * * *",
    name="同步导览服务地图版本",
    description="调用 SearchMaps 拉取导览服务各地图版本号并回填 scene_map.target_version",
    task_key="scene.sync_map_target_version",
    is_system=True,
    concurrent_policy="skip",
)
async def sync_map_target_version():
    from database.db_manager import get_session

    try:
        summaries = await MapServiceClient.search_maps()
    except Exception as exc:
        # 导览服务不可用时每分钟都会失败，用 debug 降噪
        logger.debug("search_maps rpc failed: %s", exc)
        return {"synced": 0, "error": str(exc)}

    if not summaries:
        return {"synced": 0, "note": "no maps or grpc disabled"}

    remote_map: dict[int, int] = {}
    for s in summaries:
        try:
            remote_map[int(s.id)] = int(s.version)
        except (ValueError, TypeError):
            logger.warning(
                "invalid remote summary id=%s version=%s", s.id, s.version
            )

    if not remote_map:
        return {"synced": 0}

    updated = 0
    async for db in get_session():
        stmt = select(SceneMap).where(
            SceneMap.deleted_at.is_(None),
            SceneMap.id.in_(list(remote_map.keys())),
        )
        result = await db.execute(stmt)
        for m in result.scalars():
            new_v = remote_map.get(m.id)
            if new_v is not None and m.target_version != new_v:
                m.target_version = new_v
                updated += 1
        await db.commit()

    return {"synced": updated, "remote_total": len(remote_map)}
