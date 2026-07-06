#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
商户开放 API 业务服务
在现有任务/语音 service 之上封装：机器人授权校验 + 一次性导航任务构建 + 控制转发。
"""
import logging
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.business.merchant import Merchant
from database.models.business.merchant_robot import merchant_robot_association
from database.models.business.robot import Robot
from database.models.business.robot_voice_config import RobotVoiceConfig
from database.models.business.scene_map import SceneMap
from database.models.business.scene_map_annotation import SceneMapAnnotation
from database.models.business.task import Task, task_robot_association
from database.models.business.task_execution_record import TaskExecutionRecord
from core.exception.errors import NotFoundError, ForbiddenError, ConflictError
from modules.task.services.task_execution_record_service import (
    TaskExecutionRecordService,
)
from modules.task.services.task_service import TaskService
from modules.scene.services.scene_map_annotation_service import (
    SceneMapAnnotationService,
)
from modules.grpc.config_client import VoiceConfigClient
from modules.grpc.navigation_client import NavigationClient
from modules.merchant.schemas.openapi import OpenApiResult, TtsParams

logger = logging.getLogger(__name__)

# TTS 默认参数（机器人无配置且请求未指定时使用）
_DEFAULT_TTS_VOICE = "female"
_DEFAULT_TTS_SPEED = 1.0
_DEFAULT_TTS_VOLUME = 80


class OpenApiService:
    """商户开放 API 业务"""

    @staticmethod
    async def resolve_robot(
        db: AsyncSession, merchant: Merchant, robot_sn: str
    ) -> Robot:
        """按序列号解析机器人并校验已绑定到当前商户"""
        result = await db.execute(
            select(Robot)
            .where(Robot.serial_number == robot_sn)
            .where(Robot.deleted_at.is_(None))
        )
        robot = result.scalar_one_or_none()
        if not robot:
            raise NotFoundError(msg=f"机器人 {robot_sn} 不存在")

        bound = await db.execute(
            select(merchant_robot_association.c.robot_id).where(
                merchant_robot_association.c.merchant_id == merchant.id,
                merchant_robot_association.c.robot_id == robot.id,
            )
        )
        if bound.first() is None:
            raise ForbiddenError(msg="该机器人未绑定到当前商户")
        return robot

    @staticmethod
    async def _merchant_robot_ids(
        db: AsyncSession, merchant: Merchant
    ) -> List[int]:
        """商户绑定的全部机器人ID集合"""
        result = await db.execute(
            select(merchant_robot_association.c.robot_id).where(
                merchant_robot_association.c.merchant_id == merchant.id
            )
        )
        return [row[0] for row in result.all()]

    @staticmethod
    async def _merchant_scene_ids(
        db: AsyncSession, merchant: Merchant
    ) -> List[int]:
        """商户可访问的场景地图ID集合（其机器人绑定的 map_id 去重、去 NULL）"""
        robot_ids = await OpenApiService._merchant_robot_ids(db, merchant)
        if not robot_ids:
            return []
        result = await db.execute(
            select(Robot.map_id)
            .where(
                Robot.id.in_(robot_ids),
                Robot.map_id.is_not(None),
                Robot.deleted_at.is_(None),
            )
            .distinct()
        )
        return [row[0] for row in result.all()]

    @staticmethod
    async def _load_annotations(
        db: AsyncSession, point_ids: List[int]
    ) -> List[SceneMapAnnotation]:
        """按顺序加载并校验点位"""
        if not point_ids:
            raise NotFoundError(msg="点位列表不能为空")
        result = await db.execute(
            select(SceneMapAnnotation)
            .where(
                SceneMapAnnotation.id.in_(point_ids),
                SceneMapAnnotation.deleted_at.is_(None),
            )
        )
        found = {a.id: a for a in result.scalars().all()}
        ordered: List[SceneMapAnnotation] = []
        for pid in point_ids:
            ann = found.get(pid)
            if ann is None:
                raise NotFoundError(msg=f"点位 {pid} 不存在")
            ordered.append(ann)
        return ordered

    @staticmethod
    def _assert_points_on_robot_map(
        robot: Robot, annotations: List[SceneMapAnnotation]
    ) -> None:
        """导航前校验：机器人已绑定地图，且所有点位都属于该地图"""
        if robot.map_id is None:
            raise ForbiddenError(msg="机器人未绑定场景地图，无法导航")
        for ann in annotations:
            if ann.map_id != robot.map_id:
                raise ForbiddenError(msg=f"点位 {ann.id} 不在机器人所在地图")

    @staticmethod
    def _annotation_to_point(ann: SceneMapAnnotation) -> dict:
        """SceneMapAnnotation → NavigationClient 所需的 point dict"""
        return {
            "point_id": ann.id,
            "name": ann.name,
            "x": ann.x,
            "y": ann.y,
            "angle": ann.angle,
        }

    @staticmethod
    async def goto_point(
        db: AsyncSession, merchant: Merchant, robot_sn: str, point_id: int
    ) -> OpenApiResult:
        robot = await OpenApiService.resolve_robot(db, merchant, robot_sn)
        annotations = await OpenApiService._load_annotations(db, [point_id])
        OpenApiService._assert_points_on_robot_map(robot, annotations)
        resp = await NavigationClient.navigate_to_point(
            robot.id, robot.map_id, OpenApiService._annotation_to_point(annotations[0])
        )
        success = bool(getattr(resp, "success", False))
        message = getattr(resp, "message", "") or ("单点导航已下发" if success else "导航下发失败")
        return OpenApiResult(success=success, message=message)

    @staticmethod
    async def navigate_route(
        db: AsyncSession, merchant: Merchant, robot_sn: str, point_ids: List[int]
    ) -> OpenApiResult:
        robot = await OpenApiService.resolve_robot(db, merchant, robot_sn)
        annotations = await OpenApiService._load_annotations(db, point_ids)
        OpenApiService._assert_points_on_robot_map(robot, annotations)
        points = [OpenApiService._annotation_to_point(a) for a in annotations]
        resp = await NavigationClient.navigate_route(robot.id, robot.map_id, points)
        success = bool(getattr(resp, "success", False))
        message = (
            getattr(resp, "message", "")
            or (f"多点导航已下发（{len(annotations)} 个点位）" if success else "导航下发失败")
        )
        return OpenApiResult(success=success, message=message)

    @staticmethod
    async def execute_task(
        db: AsyncSession, merchant: Merchant, robot_sn: str, task_id: int
    ) -> OpenApiResult:
        robot = await OpenApiService.resolve_robot(db, merchant, robot_sn)
        await TaskService.get(db, task_id)  # 校验任务存在
        await TaskExecutionRecordService.start_execution(db, task_id, [robot.id])
        return OpenApiResult(
            success=True,
            message="任务已启动",
            data={"task_id": task_id, "action": "started"},
        )

    @staticmethod
    async def _get_active_record(
        db: AsyncSession, robot_id: int, statuses: List[str]
    ) -> TaskExecutionRecord:
        result = await db.execute(
            select(TaskExecutionRecord)
            .where(
                TaskExecutionRecord.robot_id == robot_id,
                TaskExecutionRecord.status.in_(statuses),
                TaskExecutionRecord.deleted_at.is_(None),
            )
            .order_by(TaskExecutionRecord.id.desc())
            .limit(1)
        )
        record = result.scalar_one_or_none()
        if not record:
            raise NotFoundError(msg="该机器人当前没有可操作的任务执行记录")
        return record

    @staticmethod
    async def pause_task(
        db: AsyncSession, merchant: Merchant, robot_sn: str
    ) -> OpenApiResult:
        robot = await OpenApiService.resolve_robot(db, merchant, robot_sn)
        record = await OpenApiService._get_active_record(db, robot.id, ["running", "pending"])
        await TaskExecutionRecordService.pause_execution(db, record.id)
        return OpenApiResult(success=True, message="任务已暂停", data={"record_id": record.id})

    @staticmethod
    async def resume_task(
        db: AsyncSession, merchant: Merchant, robot_sn: str
    ) -> OpenApiResult:
        robot = await OpenApiService.resolve_robot(db, merchant, robot_sn)
        record = await OpenApiService._get_active_record(db, robot.id, ["paused"])
        await TaskExecutionRecordService.resume_execution(db, record.id)
        return OpenApiResult(success=True, message="任务已恢复", data={"record_id": record.id})

    @staticmethod
    async def stop_task(
        db: AsyncSession, merchant: Merchant, robot_sn: str
    ) -> OpenApiResult:
        robot = await OpenApiService.resolve_robot(db, merchant, robot_sn)
        record = await OpenApiService._get_active_record(
            db, robot.id, ["running", "paused", "pending"]
        )
        await TaskExecutionRecordService.stop_execution(db, record.id)
        return OpenApiResult(success=True, message="任务已停止", data={"record_id": record.id})

    @staticmethod
    async def speak(
        db: AsyncSession,
        merchant: Merchant,
        robot_sn: str,
        text: str,
        tts_params: Optional[TtsParams],
    ) -> OpenApiResult:
        robot = await OpenApiService.resolve_robot(db, merchant, robot_sn)
        if not text or not text.strip():
            raise NotFoundError(msg="播报文本不能为空")

        # 加载机器人语音配置作为默认值
        cfg_result = await db.execute(
            select(RobotVoiceConfig).where(RobotVoiceConfig.robot_id == robot.id)
        )
        cfg = cfg_result.scalar_one_or_none()

        voice = (
            (tts_params.voice if tts_params and tts_params.voice else None)
            or (cfg.tts_voice if cfg else None)
            or _DEFAULT_TTS_VOICE
        )
        speed = (
            tts_params.speed
            if tts_params and tts_params.speed is not None
            else (cfg.tts_speed if cfg and cfg.tts_speed is not None else _DEFAULT_TTS_SPEED)
        )
        volume = (
            tts_params.volume
            if tts_params and tts_params.volume is not None
            else (cfg.tts_volume if cfg and cfg.tts_volume is not None else _DEFAULT_TTS_VOLUME)
        )

        resp = await VoiceConfigClient.test_tts(robot.id, voice, speed, volume, text)
        success = bool(getattr(resp, "success", False))
        message = getattr(resp, "message", "") or ("播报成功" if success else "播报失败")
        return OpenApiResult(success=success, message=message)

    @staticmethod
    async def list_scenes(
        db: AsyncSession, merchant: Merchant, robot_sn: Optional[str] = None
    ) -> OpenApiResult:
        """获取商户可访问的场景列表"""
        if robot_sn:
            robot = await OpenApiService.resolve_robot(db, merchant, robot_sn)
            map_ids = [robot.map_id] if robot.map_id is not None else []
        else:
            map_ids = await OpenApiService._merchant_scene_ids(db, merchant)

        scenes: List[dict] = []
        if map_ids:
            result = await db.execute(
                select(SceneMap)
                .where(
                    SceneMap.id.in_(map_ids),
                    SceneMap.deleted_at.is_(None),
                )
                .order_by(SceneMap.id.desc())
            )
            scenes = [
                {
                    "id": m.id,
                    "name": m.name,
                    "width": m.width,
                    "height": m.height,
                    "status": m.status,
                    "version": m.version,
                }
                for m in result.scalars().all()
            ]
        return OpenApiResult(
            success=True, message=f"共 {len(scenes)} 个场景", data={"scenes": scenes}
        )

    @staticmethod
    async def list_points(
        db: AsyncSession, merchant: Merchant, map_id: int
    ) -> OpenApiResult:
        """获取指定场景下的点位列表"""
        scene_ids = await OpenApiService._merchant_scene_ids(db, merchant)
        if map_id not in scene_ids:
            raise ForbiddenError(msg="该场景未绑定到当前商户的机器人")

        annotations = await SceneMapAnnotationService.get_list(db, map_id)
        points = [
            {
                "id": a.id,
                "name": a.name,
                "type": a.type,
                "x": a.x,
                "y": a.y,
                "angle": a.angle,
            }
            for a in annotations
        ]
        return OpenApiResult(
            success=True, message=f"共 {len(points)} 个点位", data={"points": points}
        )

    @staticmethod
    async def list_tasks(
        db: AsyncSession,
        merchant: Merchant,
        robot_sn: Optional[str] = None,
        map_id: Optional[int] = None,
        task_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> OpenApiResult:
        """获取关联到商户机器人的任务列表"""
        if robot_sn:
            robot = await OpenApiService.resolve_robot(db, merchant, robot_sn)
            robot_ids = [robot.id]
        else:
            robot_ids = await OpenApiService._merchant_robot_ids(db, merchant)

        task_ids: List[int] = []
        if robot_ids:
            result = await db.execute(
                select(task_robot_association.c.task_id).where(
                    task_robot_association.c.robot_id.in_(robot_ids)
                )
            )
            task_ids = list({row[0] for row in result.all()})

        tasks: List[dict] = []
        if task_ids:
            stmt = select(Task).where(
                Task.id.in_(task_ids),
                Task.deleted_at.is_(None),
            )
            if map_id is not None:
                stmt = stmt.where(Task.map_id == map_id)
            if task_type:
                stmt = stmt.where(Task.task_type == task_type)
            if status:
                stmt = stmt.where(Task.status == status)
            stmt = stmt.order_by(Task.id.desc())
            result = await db.execute(stmt)
            tasks = [
                {
                    "id": t.id,
                    "name": t.name,
                    "task_type": t.task_type,
                    "status": t.status,
                    "enabled": t.enabled,
                    "map_id": t.map_id,
                    "last_run_at": t.last_run_at.isoformat() if t.last_run_at else None,
                    "next_run_at": t.next_run_at.isoformat() if t.next_run_at else None,
                }
                for t in result.scalars().all()
            ]
        return OpenApiResult(
            success=True, message=f"共 {len(tasks)} 个任务", data={"tasks": tasks}
        )
