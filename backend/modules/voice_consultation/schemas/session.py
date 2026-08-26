#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Annotated

from pydantic import BeforeValidator, Field, field_serializer

from app.models.common.base import BaseEntity, BaseRespEntity, OptionalIntField, parse_optional_enum

# 枚举取值（与外部写入方约定的 code，中文标签由前端 i18n 映射）
INTENT_TYPES = {
    "indoor_navigation",
    "triage_qa",
    "medical_guide",
    "health_check_notice",
    "insurance_guide",
    "admission_notice",
    "medication_consult",
    "general_chat",
}
TRIGGER_METHODS = {"wake_word", "face_recognition"}
SESSION_STATUSES = {"in_progress", "completed", "interrupted"}

IntentTypeField = Annotated[str | None, BeforeValidator(parse_optional_enum(INTENT_TYPES))]
TriggerMethodField = Annotated[str | None, BeforeValidator(parse_optional_enum(TRIGGER_METHODS))]
SessionStatusField = Annotated[str | None, BeforeValidator(parse_optional_enum(SESSION_STATUSES))]


class VoiceConsultationSessionQueryParams(BaseEntity):
    """语音问诊会话查询参数"""

    robot_id: OptionalIntField = Field(None, description="机器人ID")
    trigger_method: TriggerMethodField = Field(None, description="触发方式：wake_word/face_recognition")
    status: SessionStatusField = Field(None, description="状态：in_progress/completed/interrupted")
    intent_type: IntentTypeField = Field(None, description="意图类型")
    keyword: str | None = Field(None, description="关键词，模糊匹配提问摘要")
    start_time: str | None = Field(None, description="开始时间")
    end_time: str | None = Field(None, description="结束时间")


class VoiceConsultationSessionResponse(BaseRespEntity):
    """语音问诊会话列表响应"""

    id: int
    robot_id: int
    robot_name: str | None = Field(None, description="机器人名称")
    occurred_at: datetime | None = Field(None, description="交互发生时间")
    trigger_method: str
    turn_count: int
    question_summary: str | None
    duration_seconds: int | None
    status: str
    intent_type: str
    created_at: datetime | None
    updated_at: datetime | None

    # 覆盖 BaseRespEntity 的 status 序列化器（后者将 status 当作布尔值转 "1"/"2"），
    # 语音问诊状态是 in_progress/completed/interrupted 字符串枚举，需保持原值。
    @field_serializer("status")
    def serialize_status_output(self, value):
        return value.value if hasattr(value, "value") else value


class VoiceConsultationTurnResponse(BaseRespEntity):
    """语音问诊轮次明细响应"""

    id: int
    turn_no: int
    question: str | None
    answer: str | None
    intent_type: str | None
    duration_seconds: int | None
    occurred_at: datetime | None


class VoiceConsultationSessionDetailResponse(VoiceConsultationSessionResponse):
    """语音问诊会话详情响应（含轮次明细）"""

    turns: list[VoiceConsultationTurnResponse] = Field(default_factory=list, description="轮次明细，按轮次序号排序")


class VoiceConsultationDistributionItem(BaseRespEntity):
    """分布统计项"""

    type: str = Field(description="枚举 code")
    count: int = Field(description="数量")


class VoiceConsultationStatsResponse(BaseRespEntity):
    """语音问诊统计响应（卡片统计为全量口径不随筛选，分布图表随筛选）"""

    total: int = Field(description="全量总交互数（不随筛选）")
    total_delta_pct: float | None = Field(None, description="总量较截止上周日累计的百分比变化")
    today_count: int = Field(description="今日交互数（不随筛选）")
    today_delta_pct: float | None = Field(None, description="今日较昨日百分比变化")
    avg_duration: float | None = Field(None, description="全量平均会话时长（秒，不随筛选）")
    avg_duration_delta_pct: float | None = Field(None, description="当日均值较昨日均值的百分比变化")
    intent_distribution: list[VoiceConsultationDistributionItem] = Field(description="意图分布（随筛选），8 项含零值")
    trigger_distribution: list[VoiceConsultationDistributionItem] = Field(description="触发方式分布（随筛选），2 项含零值")
