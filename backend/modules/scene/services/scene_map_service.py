#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
from typing import List, Tuple

from sqlalchemy import select, and_, update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload, joinedload

from core.exception.errors import NotFoundError
from database.models.business.scene_map import SceneMap
from database.models.business.scene_map_annotation import SceneMapAnnotation
from database.models.business.scene_map_object import SceneMapObject
from database.models.business.scene_map_path import SceneMapPath
from database.models.business.scene_group import SceneGroup
from modules.scene.services.scene_group_service import SceneGroupService
from database.utils.timezone import timezone
from modules.scene.schemas.scene_map import (
    SceneMapCreate,
    SceneMapUpdate,
    SceneMapQueryParams,
)

logger = logging.getLogger(__name__)


class SceneMapService:
    """场景地图管理服务"""

    @staticmethod
    def build_query(query_params: SceneMapQueryParams):
        """构建场景地图查询（关联分组名称）"""
        conditions = []
        if query_params.name:
            conditions.append(SceneMap.name.like(f"%{query_params.name}%"))
        if query_params.group_id is not None:
            conditions.append(SceneMap.group_id == query_params.group_id)
        if query_params.status is not None:
            conditions.append(SceneMap.status == query_params.status)

        stmt = (
            select(SceneMap)
            .where(SceneMap.deleted_at.is_(None))
            .options(noload(SceneMap.annotations), noload(SceneMap.objects))
        )
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(SceneMap.created_at.desc())
        return stmt

    @staticmethod
    async def get_list_with_group_name(
        db: AsyncSession, query_params: SceneMapQueryParams
    ) -> Tuple[List[dict], int]:
        """获取地图列表（含分组名称）及总数"""
        from sqlalchemy.sql import func

        stmt = SceneMapService.build_query(query_params)

        # 计算总数
        count_stmt = stmt.with_only_columns(func.count()).order_by(None)
        result = await db.execute(count_stmt)
        total = result.scalar() or 0

        # 获取数据
        result = await db.execute(stmt)
        maps = result.unique().scalars().all()

        # 批量获取分组名称
        group_ids = {m.group_id for m in maps if m.group_id is not None}
        group_map = {}
        if group_ids:
            group_stmt = select(SceneGroup).where(
                SceneGroup.id.in_(group_ids),
                SceneGroup.deleted_at.is_(None),
            )
            group_result = await db.execute(group_stmt)
            for g in group_result.scalars().all():
                group_map[g.id] = g.name

        # 组装结果
        items = []
        for m in maps:
            item_dict = {
                "id": m.id,
                "name": m.name,
                "group_id": m.group_id,
                "image_id": m.image_id,
                "nav_image_id": m.nav_image_id,
                "width": m.width,
                "height": m.height,
                "resolution": m.resolution,
                "start_point_x": m.start_point_x,
                "start_point_y": m.start_point_y,
                "status": m.status,
                "version": m.version,
                "target_version": m.target_version,
                "group_name": group_map.get(m.group_id) if m.group_id else None,
                "created_at": m.created_at,
                "updated_at": m.updated_at,
            }
            items.append(item_dict)

        return items, total

    @staticmethod
    async def get(db: AsyncSession, map_id: int) -> SceneMap:
        """获取单个地图（含标注和物体）"""
        stmt = (
            select(SceneMap)
            .where(
                SceneMap.id == map_id,
                SceneMap.deleted_at.is_(None),
            )
            .options(
                noload(SceneMap.group),
                noload(SceneMap.image),
            )
        )
        result = await db.execute(stmt)
        map_obj = result.scalar_one_or_none()
        if not map_obj:
            raise NotFoundError(msg=f"场景地图 {map_id} 不存在")
        return map_obj

    @staticmethod
    async def _resolve_group_id(db: AsyncSession, map_create: SceneMapCreate) -> int | None:
        """解析分组ID：优先使用group_id，否则按group_name查找或自动创建"""
        if map_create.group_id is not None:
            return map_create.group_id
        if not map_create.group_name:
            return None

        # 按名称查找已有分组
        stmt = select(SceneGroup).where(
            SceneGroup.name == map_create.group_name,
            SceneGroup.deleted_at.is_(None),
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            return existing.id

        # 自动创建分组
        from modules.scene.schemas.scene_group import SceneGroupCreate
        group_create = SceneGroupCreate(name=map_create.group_name, status=True)
        group_obj = await SceneGroupService.create(db, group_create)
        return group_obj.id

    @staticmethod
    async def create(db: AsyncSession, map_create: SceneMapCreate) -> SceneMap:
        """创建场景地图"""
        group_id = await SceneMapService._resolve_group_id(db, map_create)
        nav_image_id = map_create.nav_image_id
        if nav_image_id is None:
            nav_image_id = map_create.image_id
        map_obj = SceneMap(
            name=map_create.name,
            group_id=group_id,
            image_id=map_create.image_id,
            nav_image_id=nav_image_id,
            width=map_create.width,
            height=map_create.height,
            resolution=map_create.resolution,
            start_point_x=map_create.start_point_x,
            start_point_y=map_create.start_point_y,
            status=map_create.status,
        )
        db.add(map_obj)
        await db.flush()
        return map_obj

    @staticmethod
    async def update(
        db: AsyncSession, map_id: int, map_update: SceneMapUpdate
    ) -> Tuple[SceneMap, bool, bool]:
        """更新场景地图，返回 (地图对象, image_id 是否变化, start_point 是否变化)

        start_point 变化时，会同步平移该地图下的标注/物体/路径坐标（按 start_point 新旧差值直接平移，
        不涉及 resolution）。机器人坐标为独立世界系，不受影响。start_point 变化也需要重新生成 nav_image。
        """
        map_obj = await SceneMapService.get(db, map_id)
        old_image_id = map_obj.image_id

        # 记录旧值，用于判断 start_point 是否变化及计算平移偏移
        old_start_x = map_obj.start_point_x
        old_start_y = map_obj.start_point_y

        update_data = map_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(map_obj, field, value)

        await db.flush()
        image_id_changed = (
            "image_id" in update_data and map_obj.image_id != old_image_id
        )

        new_start_x = map_obj.start_point_x
        new_start_y = map_obj.start_point_y
        start_point_changed = (
            ("start_point_x" in update_data or "start_point_y" in update_data)
            and (new_start_x != old_start_x or new_start_y != old_start_y)
        )
        if start_point_changed:
            await SceneMapService._apply_start_point_offset(
                db,
                map_id=map_obj.id,
                old_start_x=old_start_x,
                old_start_y=old_start_y,
                new_start_x=new_start_x,
                new_start_y=new_start_y,
            )
            await db.flush()

        return map_obj, image_id_changed, start_point_changed

    @staticmethod
    async def _apply_start_point_offset(
        db: AsyncSession,
        *,
        map_id: int,
        old_start_x: float,
        old_start_y: float,
        new_start_x: float,
        new_start_y: float,
    ) -> None:
        """start_point 变化后，按新旧差值平移地图子元素(标注/物体/路径)坐标（不涉及 resolution/height）。

        平移公式（直接加上 start_point 新旧差值）：
            new_pixelX = old_pixelX + new_start_x - old_start_x
            new_pixelY = old_pixelY + new_start_y - old_start_y

        - 标注：平移 x、y
        - 物体：平移 x、y（points 为相对物体自身原点的偏移，随 x/y 平移即可，不单独处理）
        - 路径：仅平移中间点 points(JSON，绝对像素坐标)；起止为标注引用，随标注平移自动跟随
        - 机器人：独立世界坐标系、外部写入，不在此处理
        """
        # 标注 x/y
        await db.execute(
            sql_update(SceneMapAnnotation)
            .where(
                SceneMapAnnotation.map_id == map_id,
                SceneMapAnnotation.deleted_at.is_(None),
            )
            .values(
                x=SceneMapAnnotation.x + new_start_x - old_start_x,
                y=SceneMapAnnotation.y + new_start_y - old_start_y,
            )
        )
        # 物体 x/y
        await db.execute(
            sql_update(SceneMapObject)
            .where(
                SceneMapObject.map_id == map_id,
                SceneMapObject.deleted_at.is_(None),
            )
            .values(
                x=SceneMapObject.x + new_start_x - old_start_x,
                y=SceneMapObject.y + new_start_y - old_start_y,
            )
        )
        # 路径中间点(JSON，绝对像素坐标)
        stmt = select(SceneMapPath).where(
            SceneMapPath.map_id == map_id,
            SceneMapPath.deleted_at.is_(None),
        )
        paths = (await db.execute(stmt)).scalars().all()
        for path in paths:
            if not path.points:
                continue
            try:
                data = json.loads(path.points)
            except (TypeError, ValueError):
                continue
            if not isinstance(data, list):
                continue
            changed = False
            for pt in data:
                if isinstance(pt, dict) and "x" in pt and "y" in pt:
                    old_px, old_py = float(pt["x"]), float(pt["y"])
                    pt["x"] = old_px + new_start_x - old_start_x
                    pt["y"] = old_py + new_start_y - old_start_y
                    changed = True
                elif isinstance(pt, list) and len(pt) >= 2:
                    old_px, old_py = float(pt[0]), float(pt[1])
                    pt[0] = old_px + new_start_x - old_start_x
                    pt[1] = old_py + new_start_y - old_start_y
                    changed = True
            if changed:
                path.points = json.dumps(data)

    @staticmethod
    async def delete(db: AsyncSession, map_id: int) -> None:
        """删除场景地图（软删除）+ 同步软删关联 task + 解除 robot 绑定"""
        map_obj = await SceneMapService.get(db, map_id)

        # 先级联清理外部关联（task.map_id 是 SET NULL、robot.map_id 无级联，必须显式处理），再软删地图本身
        from modules.task.services.task_service import TaskService
        from modules.robot.services.robot_service import RobotService
        deleted_tasks = await TaskService.soft_delete_by_map_id(db, map_id)
        unbound_robots = await RobotService.unbind_map(db, map_id)
        logger.info(
            "删除场景地图 %s：级联软删 %d 个任务，解绑 %d 个机器人",
            map_id, deleted_tasks, unbound_robots,
        )

        map_obj.soft_delete()
        await db.flush()
