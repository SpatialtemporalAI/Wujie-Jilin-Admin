#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
机器人参数配置服务
处理语音合成配置与人脸识别TTS配置的业务逻辑

DB 写入成功后会调用 gRPC 推送（ConfigService），将最新配置同步给机器人侧立即生效。
推送采用最终一致语义：
- ENABLED=false → 静默跳过，返回 grpc_status=disabled
- 推送成功 → 返回 grpc_status=synced
- 推送失败 → 写入 grpc_retry_task 表等待后台调度重试，返回 grpc_status=pending_retry
所有 5 个保存方法返回 (orm_obj, grpc_status)。
"""
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, Select
from typing import Any, Awaitable, Callable, List, Optional, Tuple

from database.models.business.robot_voice_config import RobotVoiceConfig
from database.models.business.robot_face_recognition import RobotFaceRecognition
from core.config import settings
from core.exception.errors import NotFoundError
from app.models.common.page import PageRequest, get_paginated_results
from modules.grpc.config_client import (
    BatteryConfigClient,
    FaceRecognitionClient,
    SpeedConfigClient,
    VoiceConfigClient,
)
from modules.grpc.retry_service import GrpcRetryService
from modules.robot.schemas.robot_config import (
    RobotVoiceConfigSchema,
    RobotFaceRecognitionCreate,
    RobotFaceRecognitionUpdate,
)

logger = logging.getLogger(__name__)


class RobotConfigService:
    """
    机器人参数配置服务类
    """

    # ==================== gRPC 推送工具 ====================

    @staticmethod
    async def _push_with_retry(
        db: AsyncSession,
        *,
        rpc_call: Callable[[], Awaitable[Any]],
        service_name: str,
        method_name: str,
        payload: dict,
        robot_id: Optional[int] = None,
    ) -> str:
        """通用推送入口：调用 RPC，失败则入 grpc_retry_task 表。

        Returns:
            "synced" / "pending_retry" / "disabled"
        """
        if not settings.GRPC.ENABLED:
            return "disabled"
        try:
            resp = await rpc_call()
        except Exception as e:  # noqa: BLE001 - client 已吞，这里是双保险
            logger.exception(
                "grpc push raised service=%s method=%s", service_name, method_name
            )
            await GrpcRetryService.save_pending(
                db,
                service_name=service_name,
                method_name=method_name,
                payload=payload,
                robot_id=robot_id,
                last_error=f"调用异常: {e}",
            )
            return "pending_retry"

        if getattr(resp, "success", False):
            return "synced"

        await GrpcRetryService.save_pending(
            db,
            service_name=service_name,
            method_name=method_name,
            payload=payload,
            robot_id=robot_id,
            last_error=getattr(resp, "message", "") or "设备未响应",
        )
        return "pending_retry"

    @staticmethod
    def _aggregate_status(statuses: List[str]) -> str:
        """聚合多次 RPC 的状态：任一 pending_retry 则 pending_retry；否则取最坏值"""
        if not statuses:
            return "disabled" if not settings.GRPC.ENABLED else "synced"
        if "pending_retry" in statuses:
            return "pending_retry"
        if "synced" in statuses:
            return "synced"
        return "disabled"

    # ==================== 语音配置 ====================
    @staticmethod
    async def get_voice_config(db: AsyncSession, robot_id: int) -> RobotVoiceConfig:
        """
        获取指定机器人的语音配置，不存在则返回默认空对象
        """
        try:
            result = await db.execute(
                select(RobotVoiceConfig)
                .where(RobotVoiceConfig.robot_id == robot_id)
                .where(RobotVoiceConfig.deleted_at.is_(None))
            )
            config = result.scalar_one_or_none()
            if not config:
                logger.info("机器人 %d 语音配置不存在，返回默认空对象", robot_id)
                return RobotVoiceConfig(
                    robot_id=robot_id,
                    wake_word_enabled=False,
                    wake_word="",
                    tts_voice="female",
                    tts_speed=1.0,
                    tts_volume=80,
                )
            return config
        except Exception as e:
            logger.error("获取语音配置失败: %s", str(e), exc_info=True)
            raise

    @staticmethod
    async def save_voice_config(
        db: AsyncSession, schema: RobotVoiceConfigSchema
    ) -> Tuple[RobotVoiceConfig, str]:
        """
        保存语音配置（按 robot_id upsert）

        DB 写入成功后按字段变化智能推送：
        - 唤醒词开关或内容变化 → NotifyWakeWordChanged
        - TTS 音色/语速/音量变化 → NotifyTTSConfigChanged
        新建记录时全量推送。

        Returns: (orm_obj, grpc_status) grpc_status ∈ synced/pending_retry/disabled
        """
        try:
            logger.info("保存语音配置，请求数据: %s", schema.model_dump(exclude_none=True))

            result = await db.execute(
                select(RobotVoiceConfig)
                .where(RobotVoiceConfig.robot_id == schema.robot_id)
                .where(RobotVoiceConfig.deleted_at.is_(None))
            )
            existing = result.scalar_one_or_none()

            # 计算字段变化（用于决定调哪些 gRPC）
            changed = {"wake", "tts"}  # 新建时全推
            if existing:
                changed = set()
                if (
                    existing.wake_word_enabled != schema.wake_word_enabled
                    or (existing.wake_word or "") != (schema.wake_word or "")
                ):
                    changed.add("wake")
                if (
                    existing.tts_voice != schema.tts_voice
                    or existing.tts_speed != schema.tts_speed
                    or existing.tts_volume != schema.tts_volume
                ):
                    changed.add("tts")

            if existing:
                existing.wake_word_enabled = schema.wake_word_enabled
                existing.wake_word = schema.wake_word
                existing.tts_voice = schema.tts_voice
                existing.tts_speed = schema.tts_speed
                existing.tts_volume = schema.tts_volume
                await db.commit()
                await db.refresh(existing)
                logger.info("更新语音配置成功，ID: %d", existing.id)
                saved = existing
            else:
                config = RobotVoiceConfig(
                    robot_id=schema.robot_id,
                    wake_word_enabled=schema.wake_word_enabled,
                    wake_word=schema.wake_word,
                    tts_voice=schema.tts_voice,
                    tts_speed=schema.tts_speed,
                    tts_volume=schema.tts_volume,
                )
                db.add(config)
                await db.commit()
                await db.refresh(config)
                logger.info("创建语音配置成功，ID: %d", config.id)
                saved = config

            # DB 已落库，下面是尽力推送 + 失败入重试队列
            statuses: List[str] = []
            if "wake" in changed:
                wake_payload = {
                    "robot_id": saved.robot_id,
                    "wake_word_enabled": bool(saved.wake_word_enabled),
                    "wake_word": saved.wake_word or "",
                }
                statuses.append(
                    await RobotConfigService._push_with_retry(
                        db,
                        rpc_call=lambda: VoiceConfigClient.notify_wake_word(
                            **wake_payload
                        ),
                        service_name="voice",
                        method_name="NotifyWakeWordChanged",
                        payload=wake_payload,
                        robot_id=saved.robot_id,
                    )
                )
            if "tts" in changed:
                tts_payload = {
                    "robot_id": saved.robot_id,
                    "tts_voice": saved.tts_voice,
                    "tts_speed": float(saved.tts_speed),
                    "tts_volume": int(saved.tts_volume),
                }
                statuses.append(
                    await RobotConfigService._push_with_retry(
                        db,
                        rpc_call=lambda: VoiceConfigClient.notify_tts(**tts_payload),
                        service_name="voice",
                        method_name="NotifyTTSConfigChanged",
                        payload=tts_payload,
                        robot_id=saved.robot_id,
                    )
                )

            return saved, RobotConfigService._aggregate_status(statuses)

        except Exception as e:
            await db.rollback()
            logger.error("保存语音配置失败: %s", str(e), exc_info=True)
            raise

    # ==================== 人脸识别TTS配置 ====================

    @staticmethod
    def build_face_query() -> Select:
        """
        构建人脸识别TTS查询对象
        """
        return (
            select(RobotFaceRecognition)
            .where(RobotFaceRecognition.deleted_at.is_(None))
            .order_by(RobotFaceRecognition.id.desc())
        )

    @staticmethod
    async def get_face_list(
        db: AsyncSession, page_params: PageRequest
    ) -> Tuple[List[RobotFaceRecognition], int]:
        """
        获取人脸识别TTS配置列表（分页）
        """
        try:
            query = RobotConfigService.build_face_query()
            page_data = await get_paginated_results(
                db=db,
                page_params=page_params,
                query=query,
                schema=None,
            )
            return page_data.records, page_data.total
        except Exception as e:
            logger.error("获取人脸识别TTS列表失败: %s", str(e), exc_info=True)
            raise

    @staticmethod
    async def get_face(db: AsyncSession, face_id: int) -> RobotFaceRecognition:
        """
        获取单个人脸识别TTS配置
        """
        try:
            result = await db.execute(
                select(RobotFaceRecognition)
                .where(RobotFaceRecognition.id == face_id)
                .where(RobotFaceRecognition.deleted_at.is_(None))
            )
            face = result.scalar_one_or_none()
            if not face:
                raise NotFoundError(msg=f"人脸识别配置 {face_id} 不存在")
            return face
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("获取人脸识别TTS配置失败: %s", str(e), exc_info=True)
            raise

    @staticmethod
    async def create_face(
        db: AsyncSession, schema: RobotFaceRecognitionCreate
    ) -> Tuple[RobotFaceRecognition, str]:
        """创建人脸识别TTS配置，返回 (orm_obj, grpc_status)"""
        try:
            logger.info(
                "创建人脸识别TTS配置，请求数据: %s",
                schema.model_dump(exclude_none=True),
            )
            face = RobotFaceRecognition(
                person_name=schema.person_name,
                photo_url=schema.photo_url,
                broadcast_text=schema.broadcast_text,
            )
            db.add(face)
            await db.commit()
            await db.refresh(face)
            logger.info("创建人脸识别TTS配置成功，ID: %d", face.id)
            # 推送新增人员（全量字段）
            payload = {
                "operation": 1,  # FACE_OPERATION_CREATE
                "face_id": face.id,
                "person_name": face.person_name,
                "photo_url": face.photo_url,
                "broadcast_text": face.broadcast_text,
            }
            status = await RobotConfigService._push_with_retry(
                db,
                rpc_call=lambda: FaceRecognitionClient.notify_changed(**payload),
                service_name="face_recognition",
                method_name="NotifyFaceRecognitionChanged",
                payload=payload,
                robot_id=None,
            )
            return face, status
        except Exception as e:
            await db.rollback()
            logger.error("创建人脸识别TTS配置失败: %s", str(e), exc_info=True)
            raise

    @staticmethod
    async def update_face(
        db: AsyncSession, face_id: int, schema: RobotFaceRecognitionUpdate
    ) -> Tuple[RobotFaceRecognition, str]:
        """更新人脸识别TTS配置，返回 (orm_obj, grpc_status)"""
        try:
            logger.info(
                "更新人脸识别TTS配置，ID: %d，请求数据: %s",
                face_id,
                schema.model_dump(exclude_none=True),
            )
            face = await RobotConfigService.get_face(db, face_id)
            update_data = schema.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(face, field, value)
            await db.commit()
            await db.refresh(face)
            logger.info("更新人脸识别TTS配置成功，ID: %d", face.id)
            # 推送更新（全量字段）
            payload = {
                "operation": 2,  # FACE_OPERATION_UPDATE
                "face_id": face.id,
                "person_name": face.person_name,
                "photo_url": face.photo_url,
                "broadcast_text": face.broadcast_text,
            }
            status = await RobotConfigService._push_with_retry(
                db,
                rpc_call=lambda: FaceRecognitionClient.notify_changed(**payload),
                service_name="face_recognition",
                method_name="NotifyFaceRecognitionChanged",
                payload=payload,
                robot_id=None,
            )
            return face, status
        except NotFoundError:
            raise
        except Exception as e:
            await db.rollback()
            logger.error("更新人脸识别TTS配置失败: %s", str(e), exc_info=True)
            raise

    @staticmethod
    async def delete_face(db: AsyncSession, face_id: int) -> str:
        """删除人脸识别TTS配置（软删除），返回 grpc_status"""
        try:
            logger.info("删除人脸识别TTS配置，ID: %d", face_id)
            face = await RobotConfigService.get_face(db, face_id)
            face.soft_delete()
            await db.commit()
            logger.info("删除人脸识别TTS配置成功，ID: %d", face_id)
            # 推送删除（仅需 face_id）
            payload = {
                "operation": 3,  # FACE_OPERATION_DELETE
                "face_id": face_id,
                "person_name": "",
                "photo_url": "",
                "broadcast_text": "",
            }
            status = await RobotConfigService._push_with_retry(
                db,
                rpc_call=lambda: FaceRecognitionClient.notify_changed(**payload),
                service_name="face_recognition",
                method_name="NotifyFaceRecognitionChanged",
                payload=payload,
                robot_id=None,
            )
            return status
        except NotFoundError:
            raise
        except Exception as e:
            await db.rollback()
            logger.error("删除人脸识别TTS配置失败: %s", str(e), exc_info=True)
            raise

    # ==================== 行走速度 / 电量阈值 ====================

    @staticmethod
    async def update_speed_level(
        db: AsyncSession, robot_id: int, speed_level: str | None
    ) -> Tuple["Robot", str]:
        """更新机器人行走速度等级，返回 (orm_obj, grpc_status)"""
        try:
            from database.models.business.robot import Robot

            result = await db.execute(
                select(Robot).where(Robot.id == robot_id, Robot.deleted_at.is_(None))
            )
            robot = result.scalar_one_or_none()
            if not robot:
                raise NotFoundError(msg=f"机器人 {robot_id} 不存在")
            robot.speed_level = speed_level
            await db.commit()
            await db.refresh(robot)
            # 推送速度等级变更
            payload = {"robot_id": robot_id, "speed_level": speed_level or ""}
            status = await RobotConfigService._push_with_retry(
                db,
                rpc_call=lambda: SpeedConfigClient.notify_speed_level(**payload),
                service_name="speed",
                method_name="NotifySpeedLevelChanged",
                payload=payload,
                robot_id=robot_id,
            )
            return robot, status
        except NotFoundError:
            raise
        except Exception as e:
            await db.rollback()
            logger.error("更新机器人行走速度失败: %s", str(e), exc_info=True)
            raise

    @staticmethod
    async def update_battery_threshold(
        db: AsyncSession, robot_id: int, battery_threshold: int
    ) -> Tuple["Robot", str]:
        """更新机器人电量报警阈值，返回 (orm_obj, grpc_status)"""
        try:
            from database.models.business.robot import Robot

            result = await db.execute(
                select(Robot).where(Robot.id == robot_id, Robot.deleted_at.is_(None))
            )
            robot = result.scalar_one_or_none()
            if not robot:
                raise NotFoundError(msg=f"机器人 {robot_id} 不存在")
            robot.battery_threshold = battery_threshold
            await db.commit()
            await db.refresh(robot)
            # 推送电量阈值变更
            payload = {"robot_id": robot_id, "battery_threshold": int(battery_threshold)}
            status = await RobotConfigService._push_with_retry(
                db,
                rpc_call=lambda: BatteryConfigClient.notify_battery_threshold(**payload),
                service_name="battery",
                method_name="NotifyBatteryThresholdChanged",
                payload=payload,
                robot_id=robot_id,
            )
            return robot, status
        except NotFoundError:
            raise
        except Exception as e:
            await db.rollback()
            logger.error("更新机器人电量阈值失败: %s", str(e), exc_info=True)
            raise
