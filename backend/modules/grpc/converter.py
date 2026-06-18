"""
SceneMap -> proto MapInfo 转换器

字段映射约定（已与用户确认）：
- image_url: nav_image_id 优先（含障碍物），fallback image_id；都没有则空串
- origin_x/y: 直接等同 SceneMap.start_point_x/y
- version: int -> str（与 proto string 对齐）
- labels: 由 SceneMap.annotations 映射而来
"""
from app.grpc.generated.map import map_pb2

from database.models.business.scene_map import SceneMap


def scene_map_to_map_info(map_obj: SceneMap, image_url: str) -> map_pb2.MapInfo:
    """把 SceneMap + annotations 转换为 proto MapInfo"""
    labels = [
        map_pb2.MapLabel(
            id=str(a.id),
            name=a.name,
            type=a.type,
            x=float(a.x),
            y=float(a.y),
            angle=float(a.angle or 0),
        )
        for a in (map_obj.annotations or [])
    ]
    return map_pb2.MapInfo(
        id=str(map_obj.id),
        version=str(map_obj.version or 0),
        map=map_pb2.MapMeta(
            image_url=image_url or "",
            resolution=float(map_obj.resolution or 1),
            origin_x=float(map_obj.start_point_x or 0),
            origin_y=float(map_obj.start_point_y or 0),
        ),
        labels=labels,
    )
