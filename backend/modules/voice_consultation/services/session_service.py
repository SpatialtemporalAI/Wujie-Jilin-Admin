#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
语音问诊会话管理服务
"""
import logging
from datetime import datetime, timedelta, timezone as timezone_module

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.exception.errors import NotFoundError
from database.models.business.robot import Robot
from database.models.business.voice_consultation_session import VoiceConsultationSession
from database.models.business.voice_consultation_turn import VoiceConsultationTurn
from database.utils.timezone import timezone
from modules.voice_consultation.schemas.session import (
    INTENT_TYPES,
    TRIGGER_METHODS,
    VoiceConsultationSessionQueryParams,
    VoiceConsultationStatsResponse,
)

logger = logging.getLogger(__name__)


class VoiceConsultationSessionService:
    """语音问诊会话管理服务类"""

    @staticmethod
    def _parse_time(value: str) -> datetime | None:
        """解析 ISO 时间字符串为 UTC aware datetime"""
        try:
            dt = datetime.fromisoformat(value)
            return (
                dt.astimezone(timezone_module.utc)
                if dt.tzinfo
                else dt.replace(tzinfo=timezone_module.utc)
            )
        except ValueError:
            return None

    @staticmethod
    def build_session_query(query_params: VoiceConsultationSessionQueryParams, time_field=None):
        """构建语音问诊会话查询"""
        time_field = time_field or VoiceConsultationSession.occurred_at
        conditions = [VoiceConsultationSession.deleted_at.is_(None)]

        if query_params.robot_id:
            conditions.append(VoiceConsultationSession.robot_id == query_params.robot_id)
        if query_params.trigger_method:
            conditions.append(VoiceConsultationSession.trigger_method == query_params.trigger_method)
        if query_params.status:
            conditions.append(VoiceConsultationSession.status == query_params.status)
        if query_params.intent_type:
            conditions.append(VoiceConsultationSession.intent_type == query_params.intent_type)
        if query_params.keyword:
            conditions.append(VoiceConsultationSession.question_summary.like(f"%{query_params.keyword}%"))
        if query_params.start_time:
            start = VoiceConsultationSessionService._parse_time(query_params.start_time)
            if start:
                conditions.append(time_field >= start)
        if query_params.end_time:
            end = VoiceConsultationSessionService._parse_time(query_params.end_time)
            if end:
                conditions.append(time_field <= end)

        base_query = select(VoiceConsultationSession)
        if conditions:
            base_query = base_query.where(and_(*conditions))

        base_query = base_query.order_by(VoiceConsultationSession.occurred_at.desc())
        return base_query

    @staticmethod
    async def fill_robot_names(db: AsyncSession, records: list) -> None:
        """批量填充机器人名称到 records（每条需有 robot_id 属性）。

        单表查询（列表/导出）取不到 robot_name，统一在此按 robot_id 批量回填；
        列表端点与导出 enrich_fn 复用同一实现。
        """
        if not records:
            return
        robot_ids = {record.robot_id for record in records}
        result = await db.execute(select(Robot).where(Robot.id.in_(robot_ids)))
        robot_map = {r.id: r.name for r in result.scalars().all()}
        for record in records:
            record.robot_name = robot_map.get(record.robot_id)

    @staticmethod
    async def get_session_with_turns(db: AsyncSession, session_id: int) -> VoiceConsultationSession:
        """获取单条会话（含按轮次序号排序的轮次明细）"""
        result = await db.execute(
            select(VoiceConsultationSession).where(
                and_(VoiceConsultationSession.id == session_id, VoiceConsultationSession.deleted_at.is_(None))
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise NotFoundError(msg=f"语音问诊会话 {session_id} 不存在")

        turn_result = await db.execute(
            select(VoiceConsultationTurn)
            .where(
                and_(
                    VoiceConsultationTurn.session_id == session_id,
                    VoiceConsultationTurn.deleted_at.is_(None),
                )
            )
            .order_by(VoiceConsultationTurn.turn_no.asc())
        )
        session.turns = list(turn_result.scalars().all())
        return session

    @staticmethod
    async def get_stats(
        db: AsyncSession, query_params: VoiceConsultationSessionQueryParams
    ) -> VoiceConsultationStatsResponse:
        """统计：总量/今日/平均时长（带环比） + 意图分布 + 触发方式分布"""
        service = VoiceConsultationSessionService

        # 筛选条件（不含时间范围，时间范围单独拼接滑动窗口）
        def filter_conditions() -> list:
            conditions = [VoiceConsultationSession.deleted_at.is_(None)]
            if query_params.robot_id:
                conditions.append(VoiceConsultationSession.robot_id == query_params.robot_id)
            if query_params.trigger_method:
                conditions.append(VoiceConsultationSession.trigger_method == query_params.trigger_method)
            if query_params.status:
                conditions.append(VoiceConsultationSession.status == query_params.status)
            if query_params.intent_type:
                conditions.append(VoiceConsultationSession.intent_type == query_params.intent_type)
            return conditions

        time_conditions = []
        if query_params.start_time:
            start = service._parse_time(query_params.start_time)
            if start:
                time_conditions.append(VoiceConsultationSession.occurred_at >= start)
        if query_params.end_time:
            end = service._parse_time(query_params.end_time)
            if end:
                time_conditions.append(VoiceConsultationSession.occurred_at <= end)

        conditions = filter_conditions() + time_conditions

        # 1) 筛选范围内总量 + 平均时长
        summary_stmt = select(
            func.count(VoiceConsultationSession.id),
            func.avg(VoiceConsultationSession.duration_seconds),
        ).where(and_(*conditions))
        total, avg_duration = (await db.execute(summary_stmt)).one()
        total = total or 0
        avg_duration = float(avg_duration) if avg_duration is not None else None

        # 2) 今日交互 + 上周同日（今日边界用 Asia/Shanghai 本地自然日，转 UTC 比较）
        now_local = timezone.now()
        today_start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        today_start = today_start_local.astimezone(timezone_module.utc)
        last_week_start = today_start - timedelta(days=7)
        last_week_end = today_start

        async def count_between(start: datetime, end: datetime) -> int:
            stmt = select(func.count(VoiceConsultationSession.id)).where(
                and_(
                    *conditions,
                    VoiceConsultationSession.occurred_at >= start,
                    VoiceConsultationSession.occurred_at < end,
                )
            )
            return (await db.execute(stmt)).scalar() or 0

        today_count = await count_between(today_start, today_start + timedelta(days=1))
        last_week_same_day = await count_between(last_week_start, last_week_end)
        today_delta_pct = (
            round((today_count - last_week_same_day) / last_week_same_day * 100, 1)
            if last_week_same_day
            else None
        )

        # 3) 平均时长环比：近 7 天 vs 前 7 天（不受用户筛选的时间范围影响，固定滑动窗口）
        async def avg_between(start: datetime, end: datetime) -> float | None:
            stmt = select(func.avg(VoiceConsultationSession.duration_seconds)).where(
                and_(
                    *filter_conditions(),
                    VoiceConsultationSession.occurred_at >= start,
                    VoiceConsultationSession.occurred_at < end,
                )
            )
            value = (await db.execute(stmt)).scalar()
            return float(value) if value is not None else None

        recent_avg = await avg_between(today_start - timedelta(days=6), today_start + timedelta(days=1))
        prior_avg = await avg_between(today_start - timedelta(days=13), today_start - timedelta(days=6))
        avg_duration_delta_pct = (
            round((recent_avg - prior_avg) / prior_avg * 100, 1)
            if recent_avg is not None and prior_avg
            else None
        )

        # 4) 意图分布 / 触发方式分布（筛选窗口内 group_by，Python 侧补零）
        async def group_distribution(column, all_types: set[str]) -> list[dict]:
            stmt = (
                select(column, func.count(VoiceConsultationSession.id))
                .where(and_(*conditions))
                .group_by(column)
            )
            rows = (await db.execute(stmt)).all()
            count_map = {row[0]: row[1] for row in rows}
            # 按既定枚举顺序输出，含未知 code 兜底追加
            ordered = [t for t in sorted(all_types)] + [t for t in count_map if t not in all_types]
            return [{"type": t, "count": count_map.get(t, 0)} for t in ordered]

        intent_distribution = await group_distribution(VoiceConsultationSession.intent_type, INTENT_TYPES)
        trigger_distribution = await group_distribution(
            VoiceConsultationSession.trigger_method, TRIGGER_METHODS
        )

        return VoiceConsultationStatsResponse(
            total=total,
            today_count=today_count,
            today_delta_pct=today_delta_pct,
            avg_duration=round(avg_duration, 1) if avg_duration is not None else None,
            avg_duration_delta_pct=avg_duration_delta_pct,
            intent_distribution=intent_distribution,
            trigger_distribution=trigger_distribution,
        )
