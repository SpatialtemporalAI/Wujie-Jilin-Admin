#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import json
import logging
import math
import os
from io import BytesIO

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models.business.scene_map import SceneMap
from modules.admin.services.sys.file_service import FileService

logger = logging.getLogger(__name__)


OBSTACLE_TYPES = {"obstacle-circle", "obstacle-square", "obstacle-triangle"}
RESTRICTED_TYPES = {"restricted", "禁区"}


class SceneMapNavImageService:
    """导航地图图片生成服务"""

    @staticmethod
    def schedule_regenerate(map_id: int, user_id: int) -> None:
        """同步包装：用 asyncio.create_task 启动后台任务，即发即忘"""
        asyncio.create_task(SceneMapNavImageService._regenerate(map_id, user_id))

    @staticmethod
    async def _regenerate(map_id: int, user_id: int) -> None:
        from database.manager.async_manager import async_db_manager

        try:
            async with async_db_manager.get_session_cr() as db:
                stmt = (
                    select(SceneMap)
                    .where(
                        SceneMap.id == map_id,
                        SceneMap.deleted_at.is_(None),
                    )
                    .options(selectinload(SceneMap.objects))
                )
                result = await db.execute(stmt)
                map_obj = result.unique().scalar_one_or_none()
                if map_obj is None:
                    logger.warning("nav_image regenerate skipped: map %s not found", map_id)
                    return

                if map_obj.image_id is None:
                    logger.warning("nav_image regenerate skipped: map %s has no image_id", map_id)
                    return

                drawable = [
                    o for o in map_obj.objects
                    if o.type in OBSTACLE_TYPES or o.type in RESTRICTED_TYPES
                ]

                if not drawable:
                    if map_obj.nav_image_id != map_obj.image_id:
                        map_obj.nav_image_id = map_obj.image_id
                        await db.commit()
                else:
                    source_file, image_bytes = await FileService.get_file_content(db, map_obj.image_id)

                    rendered_bytes, ext, mime = SceneMapNavImageService._render(
                        image_bytes, source_file.extension, source_file.mime_type, drawable
                    )

                    base_name = os.path.splitext(source_file.original_name or "map")[0]
                    new_name = f"{base_name}_nav.{ext}"

                    new_file = await FileService.upload_file(
                        db=db,
                        file_data=rendered_bytes,
                        original_name=new_name,
                        mime_type=mime,
                        created_by=user_id,
                    )

                    map_obj.nav_image_id = new_file.id
                    await db.commit()
                    logger.info(
                        "nav_image regenerated for map %s: nav_image_id=%s",
                        map_id,
                        new_file.id,
                    )

                # nav_image_id 已就绪后，推送 NotifyMapSaved 给导览服务
                try:
                    await SceneMapNavImageService._notify_map_saved(db, map_obj)
                except Exception as notify_exc:
                    logger.warning(
                        "notify_map_saved failed for map %s: %s",
                        map_id,
                        notify_exc,
                    )
        except Exception as exc:
            logger.error(
                "nav_image regenerate failed for map %s: %s",
                map_id,
                exc,
                exc_info=True,
            )

    @staticmethod
    async def _notify_map_saved(db: AsyncSession, map_obj: SceneMap) -> None:
        """推送 MapInfo 给导览服务（NotifyMapSaved）

        在 _regenerate 内部 nav_image_id 已 commit 后调用，确保推送时图片已就绪。
        失败仅记日志，不抛出。
        """
        import grpc
        from sqlalchemy.orm import selectinload

        from modules.grpc.client import MapServiceClient
        from modules.grpc.converter import scene_map_to_map_info
        from modules.admin.services.sys.file_service import FileService

        # 重新加载带 annotations 的 map_obj（_regenerate 中只加载了 objects）
        stmt = (
            select(SceneMap)
            .where(
                SceneMap.id == map_obj.id,
                SceneMap.deleted_at.is_(None),
            )
            .options(selectinload(SceneMap.annotations))
        )
        fresh = (await db.execute(stmt)).unique().scalar_one_or_none()
        if fresh is None:
            logger.warning("notify_map_saved skipped: map %s not found", map_obj.id)
            return

        file_id = fresh.nav_image_id or fresh.image_id
        image_url = ""
        if file_id:
            image_url = await FileService.get_file_url(db, file_id) or ""

        map_info = scene_map_to_map_info(fresh, image_url)
        try:
            resp = await MapServiceClient.notify_map_saved(map_info)
            logger.info(
                "notify_map_saved ok map=%s version=%s status=%s msg=%s",
                fresh.id,
                fresh.version,
                resp.status,
                resp.message,
            )
        except grpc.aio.AioRpcError as exc:
            logger.warning(
                "notify_map_saved rpc failed map=%s code=%s details=%s",
                fresh.id,
                exc.code(),
                exc.details(),
            )

    @staticmethod
    def _render(
        image_bytes: bytes,
        extension: str,
        mime_type: str,
        objects: list,
    ) -> tuple[bytes, str, str]:
        from PIL import Image, ImageDraw

        img = Image.open(BytesIO(image_bytes))
        ext = (extension or "png").lower()
        if ext in ("jpg", "jpeg"):
            save_format = "JPEG"
            out_ext = "jpg"
            out_mime = "image/jpeg"
        elif ext == "webp":
            save_format = "WEBP"
            out_ext = "webp"
            out_mime = "image/webp"
        else:
            save_format = "PNG"
            out_ext = "png"
            out_mime = "image/png"

        if save_format == "JPEG":
            if img.mode != "RGB":
                img = img.convert("RGB")
        elif img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA")

        draw = ImageDraw.Draw(img)

        for obj in objects:
            try:
                SceneMapNavImageService._draw_object(draw, obj)
            except Exception as exc:
                logger.warning("draw object id=%s type=%s failed: %s", getattr(obj, "id", None), getattr(obj, "type", None), exc)

        out = BytesIO()
        save_kwargs = {}
        if save_format == "JPEG":
            save_kwargs["quality"] = 92

        img.save(out, format=save_format, **save_kwargs)
        return out.getvalue(), out_ext, out_mime

    @staticmethod
    def _draw_object(draw, obj) -> None:
        x = float(obj.x)
        y = float(obj.y)
        w = float(obj.width)
        h = float(obj.height)
        angle_deg = float(obj.angle or 0)

        if w <= 0 or h <= 0:
            if obj.type in RESTRICTED_TYPES and obj.points:
                points = SceneMapNavImageService._parse_points(obj.points)
                if points:
                    draw.polygon(points, fill="black")
            return

        if obj.type == "obstacle-circle":
            if angle_deg == 0:
                draw.ellipse([x, y, x + w, y + h], fill="black")
            else:
                points = SceneMapNavImageService._ellipse_points(x, y, w, h, angle_deg)
                draw.polygon(points, fill="black")
            return

        if obj.type == "obstacle-square":
            corners = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
            rotated = SceneMapNavImageService._rotate_points(corners, angle_deg, x, y)
            draw.polygon(rotated, fill="black")
            return

        if obj.type == "obstacle-triangle":
            tri = [(x + w / 2, y), (x, y + h), (x + w, y + h)]
            rotated = SceneMapNavImageService._rotate_points(tri, angle_deg, x, y)
            draw.polygon(rotated, fill="black")
            return

        if obj.type in RESTRICTED_TYPES:
            if obj.points:
                points = SceneMapNavImageService._parse_points(obj.points)
                if points:
                    points = [(x + px, y + py) for px, py in points]
                    rotated = SceneMapNavImageService._rotate_points(points, angle_deg, x, y)
                    draw.polygon(rotated, fill="black")
                    return
            corners = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
            rotated = SceneMapNavImageService._rotate_points(corners, angle_deg, x, y)
            draw.polygon(rotated, fill="black")

    @staticmethod
    def _rotate_points(points, angle_deg: float, cx: float, cy: float):
        if angle_deg == 0:
            return points
        rad = math.radians(angle_deg)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)
        rotated = []
        for px, py in points:
            dx = px - cx
            dy = py - cy
            rotated.append((cx + dx * cos_a - dy * sin_a, cy + dx * sin_a + dy * cos_a))
        return rotated

    @staticmethod
    def _ellipse_points(x: float, y: float, w: float, h: float, angle_deg: float, segments: int = 36):
        cx = x + w / 2
        cy = y + h / 2
        rx = w / 2
        ry = h / 2
        points = []
        for i in range(segments):
            theta = i * 2 * math.pi / segments
            points.append((cx + rx * math.cos(theta), cy + ry * math.sin(theta)))
        return SceneMapNavImageService._rotate_points(points, angle_deg, x, y)

    @staticmethod
    def _parse_points(raw: str):
        try:
            data = json.loads(raw)
        except (TypeError, ValueError):
            return None
        if not isinstance(data, list):
            return None
        result = []
        for p in data:
            if isinstance(p, dict) and "x" in p and "y" in p:
                result.append((float(p["x"]), float(p["y"])))
            elif isinstance(p, (list, tuple)) and len(p) >= 2:
                result.append((float(p[0]), float(p[1])))
        return result if len(result) >= 3 else None
