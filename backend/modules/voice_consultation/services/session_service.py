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

# 统计起点：总交互「截止上周日累计」窗口的下限
_STATS_EPOCH_START = datetime(2020, 1, 1, tzinfo=timezone_module.utc)


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
        """统计：总量/今日交互（全量口径不随筛选） + 当日平均时长（环比昨日） + 意图（按轮次）/触发分布（随筛选）"""
        service = VoiceConsultationSessionService

        # 卡片统计只认全量数据（仅排除软删除），不跟随用户筛选条件
        base_conditions = [VoiceConsultationSession.deleted_at.is_(None)]

        # 筛选条件（含时间范围），仅用于意图/触发分布图表
        def filter_conditions() -> list:
            conditions = list(base_conditions)
            if query_params.robot_id:
                conditions.append(VoiceConsultationSession.robot_id == query_params.robot_id)
            if query_params.trigger_method:
                conditions.append(VoiceConsultationSession.trigger_method == query_params.trigger_method)
            if query_params.status:
                conditions.append(VoiceConsultationSession.status == query_params.status)
            if query_params.keyword:
                conditions.append(
                    VoiceConsultationSession.question_summary.like(f"%{query_params.keyword}%")
                )
            if query_params.start_time:
                start = service._parse_time(query_params.start_time)
                if start:
                    conditions.append(VoiceConsultationSession.occurred_at >= start)
            if query_params.end_time:
                end = service._parse_time(query_params.end_time)
                if end:
                    conditions.append(VoiceConsultationSession.occurred_at <= end)
            return conditions

        # 1) 全量总量
        total_stmt = select(func.count(VoiceConsultationSession.id)).where(and_(*base_conditions))
        total = (await db.execute(total_stmt)).scalar() or 0

        # 时间边界（Asia/Shanghai 本地自然日，转 UTC 比较）
        now_local = timezone.now()
        today_start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        today_start = today_start_local.astimezone(timezone_module.utc)
        yesterday_start = today_start - timedelta(days=1)
        # 截止到上周日：本周一的 0 点即上周日结束；周一为一周起点
        last_sunday_end = today_start - timedelta(days=today_start_local.weekday())

        async def count_between(start: datetime, end: datetime) -> int:
            stmt = select(func.count(VoiceConsultationSession.id)).where(
                and_(
                    *base_conditions,
                    VoiceConsultationSession.occurred_at >= start,
                    VoiceConsultationSession.occurred_at < end,
                )
            )
            return (await db.execute(stmt)).scalar() or 0

        # 2) 总交互环比：全量总量 vs 截止到上周日的累计量
        total_before_last_week = await count_between(_STATS_EPOCH_START, last_sunday_end)
        total_delta_pct = (
            round((total - total_before_last_week) / total_before_last_week * 100, 1)
            if total_before_last_week
            else None
        )

        # 3) 今日交互 vs 昨日
        today_count = await count_between(today_start, today_start + timedelta(days=1))
        yesterday_count = await count_between(yesterday_start, today_start)
        today_delta_pct = (
            round((today_count - yesterday_count) / yesterday_count * 100, 1)
            if yesterday_count
            else None
        )

        # 4) 平均问诊时长：当日均值，环比昨日均值（固定自然日窗口）
        async def avg_between(start: datetime, end: datetime) -> float | None:
            stmt = select(func.avg(VoiceConsultationSession.duration_seconds)).where(
                and_(
                    *base_conditions,
                    VoiceConsultationSession.occurred_at >= start,
                    VoiceConsultationSession.occurred_at < end,
                )
            )
            value = (await db.execute(stmt)).scalar()
            return float(value) if value is not None else None

        today_avg = await avg_between(today_start, today_start + timedelta(days=1))
        yesterday_avg = await avg_between(yesterday_start, today_start)
        avg_duration_delta_pct = (
            round((today_avg - yesterday_avg) / yesterday_avg * 100, 1)
            if today_avg is not None and yesterday_avg
            else None
        )

        # 5) 意图分布 / 触发方式分布（跟随用户筛选窗口，Python 侧补零）
        chart_conditions = filter_conditions()

        def ordered_distribution(count_map: dict, all_types: set[str]) -> list[dict]:
            """按既定枚举顺序输出，含未知 code 兜底追加"""
            ordered = [t for t in sorted(all_types)] + [t for t in count_map if t not in all_types]
            return [{"type": t, "count": count_map.get(t, 0)} for t in ordered]

        # 意图分布：统计轮次表 intent_type（空意图轮次不计入），随会话筛选窗口
        intent_stmt = (
            select(VoiceConsultationTurn.intent_type, func.count())
            .join(
                VoiceConsultationSession,
                VoiceConsultationTurn.session_id == VoiceConsultationSession.id,
            )
            .where(
                and_(
                    *chart_conditions,
                    VoiceConsultationTurn.deleted_at.is_(None),
                    VoiceConsultationTurn.intent_type.is_not(None),
                )
            )
            .group_by(VoiceConsultationTurn.intent_type)
        )
        intent_rows = (await db.execute(intent_stmt)).all()
        intent_distribution = ordered_distribution({row[0]: row[1] for row in intent_rows}, INTENT_TYPES)

        # 触发方式分布：会话表统计
        trigger_stmt = (
            select(VoiceConsultationSession.trigger_method, func.count(VoiceConsultationSession.id))
            .where(and_(*chart_conditions))
            .group_by(VoiceConsultationSession.trigger_method)
        )
        trigger_rows = (await db.execute(trigger_stmt)).all()
        trigger_distribution = ordered_distribution({row[0]: row[1] for row in trigger_rows}, TRIGGER_METHODS)

        return VoiceConsultationStatsResponse(
            total=total,
            total_delta_pct=total_delta_pct,
            today_count=today_count,
            today_delta_pct=today_delta_pct,
            avg_duration=round(today_avg, 1) if today_avg is not None else None,
            avg_duration_delta_pct=avg_duration_delta_pct,
            intent_distribution=intent_distribution,
            trigger_distribution=trigger_distribution,
        )
