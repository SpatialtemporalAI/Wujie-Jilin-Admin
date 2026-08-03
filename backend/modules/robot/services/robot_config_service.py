#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
机器人参数配置服务
处理语音合成配置与人脸识别TTS配置的业务逻辑

- 语音 / 速度 / 电量：DB 写入后调用 gRPC 推送（ConfigService）同步给机器人侧，
  采用最终一致语义（ENABLED=false 跳过 / 推送失败入 grpc_retry_task 重试队列）。
- 人脸识别：不走 gRPC，DB 写入后直接调用阿里云 facebody（FaceService），把该记录注册为
  人脸库 _FACE_DB_NAME 中的一个 entity。注册失败则回滚本地记录，保证本地与阿里云一致。
所有保存方法返回 (orm_obj, grpc_status)。
"""
import logging
import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, Select
from typing import Any, Awaitable, Callable, List, Optional, Tuple

from database.models.business.robot_voice_config import (
    RobotVoiceConfig,
    DEFAULT_WAKE_WORD_ENABLED,
    DEFAULT_WAKE_WORD,
    DEFAULT_TTS_VOICE,
    DEFAULT_TTS_SPEED,
    DEFAULT_TTS_VOLUME,
)
from database.models.business.robot_face_recognition import RobotFaceRecognition
from core.config import settings
from core.exception.errors import GatewayError, NotFoundError, RequestError
from app.models.common.page import PageRequest, get_paginated_results
from modules.grpc.config_client import (
    BatteryConfigClient,
    SpeedConfigClient,
    VoiceConfigClient,
)
from modules.grpc.push_dedup import DEDUP_WINDOW_SECONDS, should_suppress
from modules.grpc.retry_service import GrpcRetryService
from modules.face.services.face_service import FaceService
from modules.admin.services.sys.file_service import FileService
from modules.robot.schemas.robot_config import (
    RobotVoiceConfigSchema,
    RobotFaceRecognitionCreate,
    RobotFaceRecognitionUpdate,
)

logger = logging.getLogger(__name__)

# 参数配置·人脸识别直连的阿里云人脸库名称
_FACE_DB_NAME = "lvya"

# 匹配 photo_url 中的 file_id：/admin/sys/file/{id}/preview
_PHOTO_FILE_ID_RE = re.compile(r"/file/(\d+)(?:/preview)?(?:[/?#]|$)")


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
        """通用推送入口：先取消同键旧 pending → 检测在线 → 调 RPC，失败/离线则入 grpc_retry_task 表。

        覆盖语义：调 RPC 前先 cancel_superseded，无论本次成败旧同键 pending 都被取消，
        避免定时任务把旧值补推造成设备端数据回退。
        在线前置：离线直接入队等待上线（不浪费一次注定失败的 RPC）。

        Returns:
            "synced" / "pending_retry" / "disabled"
        """
        if not settings.GRPC.ENABLED:
            return "disabled"

        # 0. 实时推送去重门：同机器人 + 同方法 + 字节级相同载荷在窗口内只推一次，
        #    挡掉双击 / 多标签页 / 并发请求造成的 1s 内重复（预约式，check+set 间无 await）。
        #    不同载荷（如速度 low→high）不拦截，正常下发。
        if should_suppress(service_name, method_name, robot_id, payload):
            logger.info(
                "grpc push suppressed(dedup %.1fs) service=%s method=%s robot_id=%s",
                DEDUP_WINDOW_SECONDS,
                service_name,
                method_name,
                robot_id,
            )
            return "synced"

        # 1. 取消同业务键旧 pending（覆盖：旧值不再补推）
        await GrpcRetryService.cancel_superseded(
            db,
            service_name=service_name,
            method_name=method_name,
            robot_id=robot_id,
        )

        # 2. 离线直接入队等待上线
        if not await GrpcRetryService.is_robot_online(db, robot_id):
            await GrpcRetryService.save_pending(
                db,
                service_name=service_name,
                method_name=method_name,
                payload=payload,
                robot_id=robot_id,
                last_error="机器人离线，等待上线后重试",
            )
            return "pending_retry"

        # 3. 在线则推送
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
                logger.info("机器人 %d 语音配置不存在，返回默认对象", robot_id)
                return RobotVoiceConfig(
                    robot_id=robot_id,
                    wake_word_enabled=DEFAULT_WAKE_WORD_ENABLED,
                    wake_word=DEFAULT_WAKE_WORD,
                    tts_voice=DEFAULT_TTS_VOICE,
                    tts_speed=DEFAULT_TTS_SPEED,
                    tts_volume=DEFAULT_TTS_VOLUME,
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
    def _file_id_from_photo_url(photo_url: str) -> int:
        """从 photo_url（/admin/sys/file/{id}/preview）解析出 file_id"""
        match = _PHOTO_FILE_ID_RE.search(photo_url or "")
        if not match:
            raise RequestError(msg="人像图片解析失败")
        return int(match.group(1))

    @staticmethod
    async def _upload_photo_to_aliyun_oss(
        db: AsyncSession, photo_url: str
    ) -> str:
        """读取本地存储的人像字节并上传到阿里云 OSS，返回 OSS URL"""
        file_id = RobotConfigService._file_id_from_photo_url(photo_url)
        sys_file, content = await FileService.get_file_content(db, file_id)
        return await FaceService.upload_bytes_to_oss(
            content, sys_file.extension or "jpg"
        )

    @staticmethod
    async def create_face(
        db: AsyncSession, schema: RobotFaceRecognitionCreate
    ) -> Tuple[RobotFaceRecognition, str]:
        """创建人脸识别TTS配置并注册到阿里云人脸库 lvya，返回 (orm_obj, grpc_status)。

        本地记录与阿里云 entity 保持一致：任一阿里云步骤失败则回滚本地记录（不留残桩）。
        entity_id = str(face.id)，face_id 为阿里云返回的人脸图片ID。
        """
        try:
            logger.info(
                "创建人脸识别TTS配置，请求数据: %s",
                schema.model_dump(exclude_none=True),
            )
            # 先上传 OSS（本地尚未落库，失败直接抛，无需回滚）
            oss_url = await RobotConfigService._upload_photo_to_aliyun_oss(
                db, schema.photo_url
            )

            face = RobotFaceRecognition(
                person_name=schema.person_name,
                photo_url=schema.photo_url,
                broadcast_text=schema.broadcast_text,
            )
            db.add(face)
            await db.flush()  # 拿到 face.id 作为 entity_id
            entity_id = str(face.id)

            # 注册阿里云实体 + 入库人脸图；入库失败则 best-effort 补偿删除刚建的实体
            await FaceService.add_face_entity(_FACE_DB_NAME, entity_id)
            try:
                aliyun_face_id = await FaceService.add_face_image(
                    _FACE_DB_NAME, entity_id, oss_url
                )
            except Exception:
                try:
                    await FaceService.delete_face_entity(_FACE_DB_NAME, entity_id)
                except Exception as comp_exc:  # noqa: BLE001
                    logger.warning(
                        "补偿删除阿里云实体失败 entity_id=%s: %s",
                        entity_id,
                        comp_exc,
                    )
                raise

            face.entity_id = entity_id
            face.face_id = aliyun_face_id
            await db.commit()
            await db.refresh(face)
            logger.info(
                "创建人脸识别TTS配置成功，ID: %d, entity_id=%s",
                face.id,
                face.entity_id,
            )
            return face, "synced"
        except (NotFoundError, RequestError, GatewayError):
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error("创建人脸识别TTS配置失败: %s", str(e), exc_info=True)
            raise

    @staticmethod
    async def update_face(
        db: AsyncSession, face_id: int, schema: RobotFaceRecognitionUpdate
    ) -> Tuple[RobotFaceRecognition, str]:
        """更新人脸识别TTS配置；换图则在阿里云侧替换人脸图，返回 (orm_obj, grpc_status)。

        阿里云注册类步骤失败 → 回滚本地；删旧图 best-effort（失败仅告警，不回滚已注册新图）。
        """
        try:
            logger.info(
                "更新人脸识别TTS配置，ID: %d，请求数据: %s",
                face_id,
                schema.model_dump(exclude_none=True),
            )
            face = await RobotConfigService.get_face(db, face_id)
            update_data = schema.model_dump(exclude_unset=True)

            photo_changed = "photo_url" in update_data and (
                update_data["photo_url"] != face.photo_url
            )
            old_face_id = face.face_id if photo_changed else None

            for field, value in update_data.items():
                setattr(face, field, value)

            if photo_changed:
                # 上传新图 + 入库到同一 entity；先入库新图，再 best-effort 删旧图
                oss_url = await RobotConfigService._upload_photo_to_aliyun_oss(
                    db, face.photo_url
                )
                entity_id = face.entity_id or str(face.id)
                if not face.entity_id:
                    # 旧记录未注册过：先建实体
                    await FaceService.add_face_entity(_FACE_DB_NAME, entity_id)
                    face.entity_id = entity_id
                new_face_id = await FaceService.add_face_image(
                    _FACE_DB_NAME, entity_id, oss_url
                )
                face.face_id = new_face_id
                if old_face_id:
                    try:
                        await FaceService.delete_face(_FACE_DB_NAME, old_face_id)
                    except Exception as del_exc:  # noqa: BLE001
                        logger.warning(
                            "删除旧人脸图失败 face_id=%s entity_id=%s: %s",
                            old_face_id,
                            entity_id,
                            del_exc,
                        )

            await db.commit()
            await db.refresh(face)
            logger.info("更新人脸识别TTS配置成功，ID: %d", face.id)
            return face, "synced"
        except NotFoundError:
            raise
        except (RequestError, GatewayError):
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error("更新人脸识别TTS配置失败: %s", str(e), exc_info=True)
            raise

    @staticmethod
    async def delete_face(db: AsyncSession, face_id: int) -> str:
        """删除人脸识别TTS配置（软删除）；best-effort 删除阿里云实体，返回 grpc_status。

        删除以本地为准：阿里云删除偶发失败仅告警，不阻塞本地删除
        （与 create/update 的回滚语义区分）。
        """
        try:
            logger.info("删除人脸识别TTS配置，ID: %d", face_id)
            face = await RobotConfigService.get_face(db, face_id)
            entity_id = face.entity_id
            face.soft_delete()
            await db.commit()
            logger.info("删除人脸识别TTS配置成功，ID: %d", face_id)
            # best-effort 删除阿里云实体（本地已删，阿里云失败仅告警）
            if entity_id:
                try:
                    await FaceService.delete_face_entity(_FACE_DB_NAME, entity_id)
                except Exception as del_exc:  # noqa: BLE001
                    logger.warning(
                        "删除阿里云实体失败 entity_id=%s face_id=%d: %s",
                        entity_id,
                        face_id,
                        del_exc,
                    )
            return "synced"
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
