#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
商户开放 API 业务服务
在现有任务/语音 service 之上封装：机器人授权校验 + 一次性导航任务构建 + 控制转发。
"""
import logging
from typing import List, Optional

from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.business.merchant import Merchant
from database.models.business.merchant_robot import merchant_robot_association
from database.models.business.robot import Robot
from database.models.business.robot_voice_config import RobotVoiceConfig
from database.models.business.scene_map_annotation import SceneMapAnnotation
from database.models.business.task import Task, task_robot_association
from database.models.business.task_point import TaskPoint
from database.models.business.task_execution_record import TaskExecutionRecord
from core.exception.errors import NotFoundError, ForbiddenError, ConflictError
from modules.task.services.task_execution_record_service import (
    TaskExecutionRecordService,
)
from modules.task.services.task_service import TaskService
from modules.grpc.config_client import VoiceConfigClient
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
    async def _create_nav_task(
        db: AsyncSession, robot: Robot, annotations: List[SceneMapAnnotation]
    ) -> Task:
        """构建一次性导航任务（patrol 类型）并落库，返回 Task"""
        first_name = annotations[0].name or "导航"
        task_name = f"API-{first_name}"[:20]  # Task.name 最长 20

        if robot.map_id is None:
            raise ForbiddenError(msg="机器人未绑定场景地图，无法导航")
        for ann in annotations:
            if ann.map_id != robot.map_id:
                raise ForbiddenError(msg=f"点位 {ann.id} 不在机器人所在地图")

        task_obj = Task(
            name=task_name,
            task_type="patrol",
            map_id=robot.map_id,
            enabled=True,
            status="running",
        )
        db.add(task_obj)
        await db.flush()

        for idx, ann in enumerate(annotations):
            db.add(
                TaskPoint(
                    task_id=task_obj.id,
                    sort_order=idx,
                    point_name=ann.name,
                    annotation_id=ann.id,
                    actions=[],
                )
            )
        await db.execute(
            insert(task_robot_association).values(
                task_id=task_obj.id, robot_id=robot.id
            )
        )
        await db.commit()
        await db.refresh(task_obj)
        return task_obj

    @staticmethod
    async def goto_point(
        db: AsyncSession, merchant: Merchant, robot_sn: str, point_id: int
    ) -> OpenApiResult:
        robot = await OpenApiService.resolve_robot(db, merchant, robot_sn)
        annotations = await OpenApiService._load_annotations(db, [point_id])
        task_obj = await OpenApiService._create_nav_task(db, robot, annotations)
        await TaskExecutionRecordService.start_execution(db, task_obj.id, [robot.id])
        return OpenApiResult(
            success=True,
            message="单点导航任务已下发",
            data={
                "task_id": task_obj.id,
            },
        )

    @staticmethod
    async def navigate_route(
        db: AsyncSession, merchant: Merchant, robot_sn: str, point_ids: List[int]
    ) -> OpenApiResult:
        robot = await OpenApiService.resolve_robot(db, merchant, robot_sn)
        annotations = await OpenApiService._load_annotations(db, point_ids)
        task_obj = await OpenApiService._create_nav_task(db, robot, annotations)
        await TaskExecutionRecordService.start_execution(db, task_obj.id, [robot.id])
        return OpenApiResult(
            success=True,
            message=f"多点导航任务已下发（{len(annotations)} 个点位）",
            data={
                "task_id": task_obj.id,
            },
        )

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
