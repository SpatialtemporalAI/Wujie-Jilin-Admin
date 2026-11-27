#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
会议纪要服务
"""
import logging
import uuid
from datetime import timedelta

from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.common.base import parse_optional_int_value
from core.exception.errors import NotFoundError, RequestError, ValidationError
from database.models.business.meeting_minute import MeetingMinute
from database.models.business.meeting_minute_segment import MeetingMinuteSegment
from database.models.business.meeting_minute_speaker import MeetingMinuteSpeaker
from database.models.business.robot import Robot
from database.models.business.robot_model import RobotModel
from database.utils.timezone import timezone
from modules.admin.services.sys.file_service import FileService
from modules.meeting.schemas.agent import AgentMinuteReportPayload
from modules.meeting.schemas.minutes import (
    MinuteDetailResponse,
    MinuteExportData,
    MinuteListItem,
    MinuteQueryParams,
    MinuteSegmentResponse,
    MinuteSpeakerResponse,
)
from modules.robot.services.robot_service import RobotService

logger = logging.getLogger(__name__)


class MinuteService:
    """会议纪要服务类"""

    @staticmethod
    def build_query(query_params: MinuteQueryParams, trash: bool = False):
        """构建会议纪要查询"""
        conditions = [
            MeetingMinute.deleted_at.is_not(None) if trash else MeetingMinute.deleted_at.is_(None)
        ]

        robot_id = parse_optional_int_value(query_params.robot_id)
        if robot_id is not None:
            conditions.append(MeetingMinute.robot_id == robot_id)

        if query_params.keyword:
            keyword = query_params.keyword
            speaker_minute_ids = select(MeetingMinuteSpeaker.minute_id).where(
                MeetingMinuteSpeaker.name.contains(keyword)
            )
            conditions.append(
                or_(
                    MeetingMinute.title.contains(keyword),
                    MeetingMinute.overview.contains(keyword),
                    MeetingMinute.id.in_(speaker_minute_ids),
                )
            )

        time_range = (query_params.time_range or "all").strip()
        if time_range and time_range != "all":
            now = timezone.now()
            if time_range == "today":
                start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif time_range == "7":
                start = now - timedelta(days=7)
            elif time_range == "30":
                start = now - timedelta(days=30)
            else:
                start = None
            if start is not None:
                conditions.append(MeetingMinute.started_at >= start)

        sort = (query_params.sort or "desc").strip().lower()
        order = MeetingMinute.started_at.asc() if sort == "asc" else MeetingMinute.started_at.desc()

        return select(MeetingMinute).where(and_(*conditions)).order_by(order)

    @staticmethod
    async def fill_robot_info(db: AsyncSession, records: list) -> None:
        """批量回填机器人名称与型号名称"""
        if not records:
            return
        robot_ids = {record.robot_id for record in records}
        result = await db.execute(
            select(Robot.id, Robot.name, RobotModel.name)
            .join(RobotModel, Robot.model_id == RobotModel.id)
            .where(Robot.id.in_(robot_ids))
        )
        robot_map = {row[0]: (row[1], row[2]) for row in result.all()}
        for record in records:
            name, model_name = robot_map.get(record.robot_id, (None, None))
            record.robot_name = name
            record.robot_model_name = model_name

    @staticmethod
    async def fill_speakers(db: AsyncSession, records: list) -> None:
        """批量填充分发言人列表"""
        if not records:
            return
        minute_ids = [record.id for record in records]
        result = await db.execute(
            select(MeetingMinuteSpeaker)
            .where(
                MeetingMinuteSpeaker.minute_id.in_(minute_ids),
                MeetingMinuteSpeaker.deleted_at.is_(None),
            )
            .order_by(MeetingMinuteSpeaker.sort.asc(), MeetingMinuteSpeaker.id.asc())
        )
        speaker_map: dict[int, list[MinuteSpeakerResponse]] = {}
        for speaker in result.scalars().all():
            speaker_map.setdefault(speaker.minute_id, []).append(
                MinuteSpeakerResponse.model_validate(speaker)
            )
        for record in records:
            record.speakers = speaker_map.get(record.id, [])

    @staticmethod
    async def get_minute(db: AsyncSession, minute_id: int, include_deleted: bool = True) -> MeetingMinute:
        """获取会议纪要"""
        conditions = [MeetingMinute.id == minute_id]
        if not include_deleted:
            conditions.append(MeetingMinute.deleted_at.is_(None))
        result = await db.execute(select(MeetingMinute).where(and_(*conditions)))
        minute = result.scalar_one_or_none()
        if not minute:
            raise NotFoundError(msg=f"会议纪要 {minute_id} 不存在")
        return minute

    @staticmethod
    async def get_detail(db: AsyncSession, minute_id: int) -> MinuteDetailResponse:
        """获取会议纪要详情（发言人 + 逐字稿）"""
        minute = await MinuteService.get_minute(db, minute_id, include_deleted=True)

        speaker_result = await db.execute(
            select(MeetingMinuteSpeaker)
            .where(
                MeetingMinuteSpeaker.minute_id == minute_id,
                MeetingMinuteSpeaker.deleted_at.is_(None),
            )
            .order_by(MeetingMinuteSpeaker.sort.asc(), MeetingMinuteSpeaker.id.asc())
        )
        speakers = [MinuteSpeakerResponse.model_validate(item) for item in speaker_result.scalars().all()]

        segment_result = await db.execute(
            select(MeetingMinuteSegment)
            .where(
                MeetingMinuteSegment.minute_id == minute_id,
                MeetingMinuteSegment.deleted_at.is_(None),
            )
            .order_by(MeetingMinuteSegment.seq.asc(), MeetingMinuteSegment.id.asc())
        )
        segments = [MinuteSegmentResponse.model_validate(item) for item in segment_result.scalars().all()]

        detail = MinuteDetailResponse.model_validate(minute)
        detail.speakers = speakers
        detail.segments = segments
        await MinuteService.fill_robot_info(db, [detail])
        return detail

    @staticmethod
    async def update_segment_speaker(db: AsyncSession, segment_id: int, speaker_id: int) -> None:
        """人工改派逐字稿片段发言人"""
        segment_result = await db.execute(
            select(MeetingMinuteSegment).where(
                MeetingMinuteSegment.id == segment_id,
                MeetingMinuteSegment.deleted_at.is_(None),
            )
        )
        segment = segment_result.scalar_one_or_none()
        if not segment:
            raise NotFoundError(msg=f"逐字稿片段 {segment_id} 不存在")

        speaker_result = await db.execute(
            select(MeetingMinuteSpeaker).where(
                MeetingMinuteSpeaker.id == speaker_id,
                MeetingMinuteSpeaker.minute_id == segment.minute_id,
                MeetingMinuteSpeaker.deleted_at.is_(None),
            )
        )
        speaker = speaker_result.scalar_one_or_none()
        if not speaker:
            raise ValidationError(msg="目标发言人不属于该会议")

        segment.speaker_id = speaker.id
        segment.speaker_key = speaker.speaker_key
        segment.need_confirm = False
        await db.commit()

    @staticmethod
    async def soft_delete(db: AsyncSession, minute_id: int) -> None:
        """软删除（移入回收站）"""
        minute = await MinuteService.get_minute(db, minute_id, include_deleted=False)
        minute.soft_delete()
        await db.commit()

    @staticmethod
    async def restore(db: AsyncSession, minute_id: int) -> None:
        """从回收站恢复"""
        minute = await MinuteService.get_minute(db, minute_id, include_deleted=True)
        minute.deleted_at = None
        await db.commit()

    @staticmethod
    async def purge(db: AsyncSession, minute_id: int) -> None:
        """彻底删除（含发言人、逐字稿）"""
        minute = await MinuteService.get_minute(db, minute_id, include_deleted=True)
        await MinuteService._purge_children(db, [minute.id])
        await db.delete(minute)
        await db.commit()

    @staticmethod
    async def clear_trash(db: AsyncSession) -> int:
        """清空回收站"""
        result = await db.execute(
            select(MeetingMinute.id).where(MeetingMinute.deleted_at.is_not(None))
        )
        minute_ids = [row[0] for row in result.all()]
        if not minute_ids:
            return 0
        await MinuteService._purge_children(db, minute_ids)
        await db.execute(delete(MeetingMinute).where(MeetingMinute.id.in_(minute_ids)))
        await db.commit()
        return len(minute_ids)

    @staticmethod
    async def _purge_children(db: AsyncSession, minute_ids: list[int]) -> None:
        """硬删除下属逐字稿与发言人（先片段后发言人，避免外键约束）"""
        await db.execute(
            delete(MeetingMinuteSegment).where(MeetingMinuteSegment.minute_id.in_(minute_ids))
        )
        await db.execute(
            delete(MeetingMinuteSpeaker).where(MeetingMinuteSpeaker.minute_id.in_(minute_ids))
        )

    @staticmethod
    async def export(db: AsyncSession, minute_id: int, fmt: str = "md") -> MinuteExportData:
        """导出会议纪要（md / txt）"""
        detail = await MinuteService.get_detail(db, minute_id)
        speaker_map = {speaker.id: speaker for speaker in detail.speakers}

        started_at = timezone.ftime(detail.started_at)
        duration = MinuteService._format_duration(detail.duration_seconds)
        names = "、".join(speaker.name for speaker in detail.speakers) or "-"

        conclusions = [str(item) for item in (detail.conclusions or [])]
        risks = [str(item) for item in (detail.risks or [])]

        if fmt == "txt":
            lines = [
                detail.title,
                f"会议编号：{detail.meeting_no}",
                f"会议时间：{started_at}",
                f"会议时长：{duration}",
                f"参会人员：{names}",
                "",
                "【会议概览】",
                detail.overview or "-",
                "",
                "【关键结论】",
                *([f"- {item}" for item in conclusions] or ["-"]),
                "",
                "【待确认提醒】",
                *([f"- {item}" for item in risks] or ["-"]),
                "",
                "【逐字稿】",
            ]
            for segment in detail.segments:
                speaker = speaker_map.get(segment.speaker_id)
                speaker_name = speaker.name if speaker else (segment.speaker_key or "未知")
                lines.append(f"[{segment.timecode or '--:--'}] {speaker_name}：{segment.text}")
            content = "\n".join(lines)
            mime_type = "text/plain; charset=utf-8"
            filename = f"{detail.title}.txt"
        else:
            lines = [
                f"# {detail.title}",
                "",
                f"- 会议编号：{detail.meeting_no}",
                f"- 会议时间：{started_at}",
                f"- 会议时长：{duration}",
                f"- 参会人员：{names}",
                "",
                "## 会议概览",
                "",
                detail.overview or "-",
                "",
                "## 关键结论",
                "",
                *([f"- {item}" for item in conclusions] or ["-"]),
                "",
                "## 待确认提醒",
                "",
                *([f"- {item}" for item in risks] or ["-"]),
                "",
                "## 逐字稿",
                "",
            ]
            for segment in detail.segments:
                speaker = speaker_map.get(segment.speaker_id)
                speaker_name = speaker.name if speaker else (segment.speaker_key or "未知")
                lines.append(f"**[{segment.timecode or '--:--'}] {speaker_name}**：{segment.text}")
                lines.append("")
            content = "\n".join(lines)
            mime_type = "text/markdown; charset=utf-8"
            filename = f"{detail.title}.md"

        return MinuteExportData(filename=filename, content=content, mime_type=mime_type)

    @staticmethod
    def _format_duration(seconds: int | None) -> str:
        total = int(seconds or 0)
        return f"{total // 60} 分 {total % 60} 秒"

    @staticmethod
    async def report(db: AsyncSession, payload: AgentMinuteReportPayload) -> tuple[MeetingMinute, bool]:
        """agent 上报会议纪要：按 meeting_no 幂等创建或覆盖更新，返回 (纪要, 是否新建)"""
        await RobotService.get(db, payload.robot_id)

        meeting_no = (payload.meeting_no or "").strip() or MinuteService._build_meeting_no(payload)

        existing_result = await db.execute(
            select(MeetingMinute).where(MeetingMinute.meeting_no == meeting_no)
        )
        minute = existing_result.scalar_one_or_none()
        created = minute is None

        audio_url = payload.audio_url
        if payload.audio_file_id and not audio_url:
            audio_url = await FileService.get_file_url(db, payload.audio_file_id)

        if minute is None:
            minute = MeetingMinute(
                meeting_no=meeting_no,
                title=payload.title,
                robot_id=payload.robot_id,
                started_at=payload.started_at,
                duration_seconds=payload.duration_seconds,
                overview=payload.overview,
                conclusions=payload.conclusions,
                risks=payload.risks,
                summary_generated_at=payload.summary_generated_at,
                speaker_count=len(payload.speakers),
                segment_count=len(payload.segments),
                audio_file_id=payload.audio_file_id,
                audio_url=audio_url,
            )
            db.add(minute)
            await db.commit()
        else:
            minute.deleted_at = None
            minute.title = payload.title
            minute.robot_id = payload.robot_id
            minute.started_at = payload.started_at
            minute.duration_seconds = payload.duration_seconds
            minute.overview = payload.overview
            minute.conclusions = payload.conclusions
            minute.risks = payload.risks
            minute.summary_generated_at = payload.summary_generated_at
            minute.speaker_count = len(payload.speakers)
            minute.segment_count = len(payload.segments)
            minute.audio_file_id = payload.audio_file_id
            minute.audio_url = audio_url
            # 覆盖上报：先清空旧的发言人/逐字稿，避免残留
            await MinuteService._purge_children(db, [minute.id])
            await db.commit()

        speaker_id_map: dict[str, int] = {}
        for index, item in enumerate(
            sorted(payload.speakers, key=lambda speaker: speaker.sort)
        ):
            speaker = MeetingMinuteSpeaker(
                minute_id=minute.id,
                speaker_key=item.speaker_key,
                name=item.name,
                role=item.role,
                color=item.color,
                match_score=item.match_score,
                voiceprint_id=item.voiceprint_id,
                sort=item.sort if item.sort else index,
            )
            db.add(speaker)
            await db.flush()
            speaker_id_map[item.speaker_key] = speaker.id

        for index, item in enumerate(payload.segments):
            segment = MeetingMinuteSegment(
                minute_id=minute.id,
                seq=item.seq if item.seq is not None else index + 1,
                speaker_id=speaker_id_map.get(item.speaker_key or ""),
                speaker_key=item.speaker_key,
                timecode=item.timecode,
                start_seconds=item.start_seconds,
                text=item.text,
                confidence=item.confidence,
                need_confirm=item.need_confirm,
                audio_url=item.audio_url,
            )
            db.add(segment)

        await db.commit()
        logger.info(
            "agent 上报会议纪要 meeting_no=%s robot_id=%s created=%s speakers=%s segments=%s",
            meeting_no,
            payload.robot_id,
            created,
            len(payload.speakers),
            len(payload.segments),
        )
        return minute, created

    @staticmethod
    def _build_meeting_no(payload: AgentMinuteReportPayload) -> str:
        """缺省会议编号：M-YYYYMMDD-随机短码"""
        return f"M-{payload.started_at:%Y%m%d}-{uuid.uuid4().hex[:6].upper()}"
