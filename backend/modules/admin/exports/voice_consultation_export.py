#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from core.utils.excel_export import ExportColumn
from database.utils.timezone import timezone
from modules.admin.exports import ModuleExportConfig, register_export
from modules.voice_consultation.schemas.session import (
    INTENT_TYPES,
    SESSION_STATUSES,
    TRIGGER_METHODS,
    VoiceConsultationSessionQueryParams,
)
from modules.voice_consultation.services.session_service import VoiceConsultationSessionService

INTENT_LABELS = {
    "indoor_navigation": "院内问路",
    "triage_qa": "分诊问答",
    "medical_guide": "就医指南",
    "health_check_notice": "体检须知",
    "insurance_guide": "医保指南",
    "admission_notice": "住院须知",
}
TRIGGER_LABELS = {
    "wake_word": "唤醒词",
    "face_recognition": "人脸识别",
}
STATUS_LABELS = {
    "in_progress": "进行中",
    "completed": "已完成",
    "interrupted": "已中断",
}

_voice_consultation_columns = [
    ExportColumn("id", "ID", width=20, transform=str),
    ExportColumn(
        "occurred_at",
        "时间",
        width=22,
        transform=timezone.ftime,
    ),
    ExportColumn(
        "trigger_method",
        "触发",
        width=12,
        transform=lambda v: TRIGGER_LABELS.get(v, v),
    ),
    ExportColumn("robot_name", "机器人", width=18),
    ExportColumn("turn_count", "轮次", width=8),
    ExportColumn("question_summary", "提问摘要", width=40),
    ExportColumn("duration_seconds", "时长(秒)", width=10),
    ExportColumn(
        "status",
        "状态",
        width=10,
        transform=lambda v: STATUS_LABELS.get(v, v),
    ),
    ExportColumn(
        "intent_type",
        "意图类型",
        width=14,
        transform=lambda v: INTENT_LABELS.get(v, v),
    ),
    ExportColumn(
        "created_at",
        "入库时间",
        width=22,
        transform=timezone.ftime,
    ),
]

register_export(ModuleExportConfig(
    name="语音问诊记录",
    module_key="voice_consultation",
    columns=_voice_consultation_columns,
    build_query_fn=VoiceConsultationSessionService.build_session_query,
    query_params_class=VoiceConsultationSessionQueryParams,
    enrich_fn=VoiceConsultationSessionService.fill_robot_names,
))
