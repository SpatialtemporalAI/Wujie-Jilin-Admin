#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
会议声纹注册服务
"""
import logging

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.common.base import parse_optional_int_value
from core.exception.errors import NotFoundError
from database.models.business.meeting_voiceprint import MeetingVoiceprint
from database.models.business.robot import Robot
from database.models.business.robot_model import RobotModel
from modules.admin.services.sys.file_service import FileService
from modules.grpc.config_client import GrpcMethodUnsupported, VoiceprintClient
from modules.meeting.schemas.voiceprint import (
    VoiceprintOverviewData,
    VoiceprintQueryParams,
    VoiceprintResponse,
    VoiceprintRobotItem,
)
from modules.robot.services.robot_service import RobotService

logger = logging.getLogger(__name__)


class VoiceprintService:
    """声纹注册服务类"""

    @staticmethod
    def build_query(query_params: VoiceprintQueryParams):
        """构建声纹记录查询"""
        conditions = [MeetingVoiceprint.deleted_at.is_(None)]

        robot_id = parse_optional_int_value(query_params.robot_id)
        if robot_id is not None:
            conditions.append(MeetingVoiceprint.robot_id == robot_id)
        if query_params.keyword:
            conditions.append(MeetingVoiceprint.role_name.contains(query_params.keyword))
        if query_params.status:
            conditions.append(MeetingVoiceprint.status == query_params.status)

        return (
            select(MeetingVoiceprint)
            .where(and_(*conditions))
            .order_by(MeetingVoiceprint.created_at.desc())
        )

    @staticmethod
    async def fill_robot_names(db: AsyncSession, records: list) -> None:
        """批量回填机器人名称"""
        if not records:
            return
        robot_ids = {record.robot_id for record in records}
        result = await db.execute(select(Robot.id, Robot.name).where(Robot.id.in_(robot_ids)))
        robot_map = {row[0]: row[1] for row in result.all()}
        for record in records:
            record.robot_name = robot_map.get(record.robot_id)

    @staticmethod
    async def list_robots(db: AsyncSession) -> list[VoiceprintRobotItem]:
        """声纹页可选机器人（含型号名称、会议模式、已注册声纹数）"""
        result = await db.execute(
            select(Robot).where(Robot.deleted_at.is_(None)).order_by(Robot.id.desc())
        )
        robots = result.scalars().all()
        if not robots:
            return []

        model_ids = {robot.model_id for robot in robots}
        model_result = await db.execute(
            select(RobotModel.id, RobotModel.name).where(RobotModel.id.in_(model_ids))
        )
        model_map = {row[0]: row[1] for row in model_result.all()}

        robot_ids = [robot.id for robot in robots]
        count_result = await db.execute(
            select(MeetingVoiceprint.robot_id, func.count(MeetingVoiceprint.id))
            .where(
                MeetingVoiceprint.robot_id.in_(robot_ids),
                MeetingVoiceprint.deleted_at.is_(None),
                MeetingVoiceprint.status == "success",
            )
            .group_by(MeetingVoiceprint.robot_id)
        )
        count_map = {row[0]: row[1] for row in count_result.all()}

        return [
            VoiceprintRobotItem(
                id=robot.id,
                name=robot.name,
                serial_number=robot.serial_number,
                model_name=model_map.get(robot.model_id),
                robot_status=robot.status.value if hasattr(robot.status, "value") else str(robot.status),
                meeting_mode=bool(robot.meeting_mode),
                registered_count=count_map.get(robot.id, 0),
            )
            for robot in robots
        ]

    @staticmethod
    async def get_overview(db: AsyncSession, robot_id: int) -> VoiceprintOverviewData:
        """声纹页概览：会议模式 + 已注册声纹数量"""
        robot = await RobotService.get(db, robot_id)
        count = await VoiceprintService.count_registered(db, robot_id)
        return VoiceprintOverviewData(
            meeting_mode=bool(robot.meeting_mode),
            registered_count=count,
        )

    @staticmethod
    async def count_registered(db: AsyncSession, robot_id: int) -> int:
        """统计某机器人成功注册的声纹数"""
        result = await db.execute(
            select(func.count(MeetingVoiceprint.id)).where(
                MeetingVoiceprint.robot_id == robot_id,
                MeetingVoiceprint.deleted_at.is_(None),
                MeetingVoiceprint.status == "success",
            )
        )
        return result.scalar() or 0

    @staticmethod
    async def get_record(db: AsyncSession, record_id: int) -> MeetingVoiceprint:
        """获取未删除的声纹记录"""
        result = await db.execute(
            select(MeetingVoiceprint).where(
                MeetingVoiceprint.id == record_id,
                MeetingVoiceprint.deleted_at.is_(None),
            )
        )
        record = result.scalar_one_or_none()
        if not record:
            raise NotFoundError(msg=f"声纹记录 {record_id} 不存在")
        return record

    @staticmethod
    async def register(
        db: AsyncSession,
        *,
        robot_id: int,
        role_name: str,
        role_type: str,
        method: str,
        file_data: bytes,
        original_name: str,
        mime_type: str,
        transcript_hint: str,
        user_id: int,
    ) -> MeetingVoiceprint:
        """浏览器录音上传 -> 存储 -> 下发 agent 建模 -> 落库（失败也保留记录）"""
        await RobotService.get(db, robot_id)

        sys_file = await FileService.upload_file(
            db=db,
            file_data=file_data,
            original_name=original_name,
            mime_type=mime_type,
            created_by=user_id,
        )
        sample_url = await FileService.get_file_url(db, sys_file.id)
        audio_format = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else "webm"

        record = MeetingVoiceprint(
            robot_id=robot_id,
            role_name=role_name,
            role_type=role_type,
            method=method,
            status="processing",
            transcript=transcript_hint or None,
            sample_file_id=sys_file.id,
            sample_url=sample_url,
            created_by=user_id,
        )
        db.add(record)
        await db.commit()

        try:
            resp = await VoiceprintClient.register_voiceprint(
                robot_id=robot_id,
                role_name=role_name,
                role_type=role_type,
                method=method,
                audio=file_data,
                audio_format=audio_format,
                transcript_hint=transcript_hint,
            )
        except GrpcMethodUnsupported:
            record.status = "failed"
            record.error_msg = "机器人端暂不支持声纹注册，请升级机器人程序后重试"
            await db.commit()
            return record
        except Exception as exc:  # noqa: BLE001 - 失败也要落库，便于前端提示
            logger.exception("声纹注册下发失败 robot_id=%s", robot_id)
            record.status = "failed"
            record.error_msg = f"声纹注册下发失败: {exc}"[:500]
            await db.commit()
            return record

        if resp is None:
            record.status = "failed"
            record.error_msg = "机器人当前不可达或 agent 未启用，请确认机器人在线后重试"
            await db.commit()
            return record

        record.voiceprint_id = resp.voiceprint_id or None
        record.transcript = resp.transcript or transcript_hint or None
        record.score = resp.score or None
        record.clarity = resp.clarity or None
        record.match_score = resp.match or None
        record.noise_level = resp.noise_level or None
        record.status = "success" if resp.success else "failed"
        if not resp.success:
            record.error_msg = (resp.message or "声纹注册失败")[:500]
        await db.commit()
        return record

    @staticmethod
    async def delete(db: AsyncSession, record_id: int) -> None:
        """删除声纹：先尽力删除 agent 侧声纹，再软删除平台记录"""
        record = await VoiceprintService.get_record(db, record_id)
        if record.voiceprint_id:
            try:
                await VoiceprintClient.delete_voiceprint(record.robot_id, record.voiceprint_id)
            except GrpcMethodUnsupported:
                logger.warning("agent 未实现 DeleteVoiceprint，仅删除平台记录 id=%s", record_id)
            except Exception:  # noqa: BLE001 - 远端失败不阻塞本地删除
                logger.exception("删除 agent 声纹失败 id=%s", record_id)
        record.soft_delete()
        await db.commit()

    @staticmethod
    def to_response(record: MeetingVoiceprint) -> VoiceprintResponse:
        """ORM -> 响应模型（保留动态补充的 robot_name）"""
        return VoiceprintResponse.model_validate(record)
