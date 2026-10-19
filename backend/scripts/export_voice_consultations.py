#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
导出全部语音问诊会话及其轮次明细（一对多平铺）

每个轮次一行，会话字段在每行重复；没有轮次的会话也会导出一行（轮次列为空）。
用法：
    python scripts/export_voice_consultations.py [-o 输出文件.xlsx]
"""
import argparse
import os
import sys
from datetime import datetime
from itertools import groupby

# 添加 backend 目录到 Python 搜索路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from core.config import settings
from core.utils.excel_export import ExportColumn, build_excel_bytes
# 导入整个模型包，确保所有 mapper 完成注册（SceneMap 等存在跨包 relationship）
import database.models.sys  # noqa: F401
from database.models.business import (  # noqa: F401
    Robot,
    VoiceConsultationSession,
    VoiceConsultationTurn,
)
from database.utils.timezone import timezone

TRIGGER_LABELS = {
    "wake_word": "唤醒词",
    "face_recognition": "人脸识别",
}
STATUS_LABELS = {
    "in_progress": "进行中",
    "completed": "已完成",
    "interrupted": "已中断",
}
INTENT_LABELS = {
    "indoor_navigation": "院内问路",
    "triage_qa": "分诊问答",
    "medical_guide": "就医指南",
    "health_check_notice": "体检须知",
    "insurance_guide": "医保指南",
    "admission_notice": "住院须知",
    "general_chat": "闲聊问答",
}

# 会话字段 + 轮次字段，一对多平铺
COLUMNS = [
    ExportColumn("session_id", "会话ID", width=20),
    ExportColumn("robot_name", "机器人", width=18),
    ExportColumn("session_occurred_at", "会话时间", width=22),
    ExportColumn("trigger_method", "触发方式", width=12,
                 transform=lambda v: TRIGGER_LABELS.get(v, v)),
    ExportColumn("session_status", "会话状态", width=10,
                 transform=lambda v: STATUS_LABELS.get(v, v)),
    ExportColumn("session_intent_type", "会话意图", width=12,
                 transform=lambda v: INTENT_LABELS.get(v, v)),
    ExportColumn("turn_count", "轮次数", width=8),
    ExportColumn("question_summary", "提问摘要", width=40),
    ExportColumn("session_duration_seconds", "会话时长(秒)", width=12),
    ExportColumn("turn_no", "轮次序号", width=10),
    ExportColumn("question", "用户提问", width=50),
    ExportColumn("answer", "机器人回答", width=60),
    ExportColumn("turn_intent_type", "本轮意图", width=12,
                 transform=lambda v: INTENT_LABELS.get(v, v)),
    ExportColumn("turn_duration_seconds", "本轮耗时(秒)", width=12),
    ExportColumn("turn_occurred_at", "本轮时间", width=22),
]


def fetch_rows() -> list[dict]:
    sync_url = settings.DATABASE.build_url(async_mode=False)
    engine = create_engine(sync_url, echo=False)
    Session = sessionmaker(bind=engine)
    try:
        with Session() as session:
            # 会话 LEFT JOIN 轮次，一条轮次一行；无轮次的会话保留一行
            stmt = (
                select(VoiceConsultationSession, VoiceConsultationTurn, Robot.name)
                .outerjoin(
                    VoiceConsultationTurn,
                    (VoiceConsultationTurn.session_id == VoiceConsultationSession.id)
                    & (VoiceConsultationTurn.deleted_at.is_(None)),
                )
                .outerjoin(Robot, Robot.id == VoiceConsultationSession.robot_id)
                .where(VoiceConsultationSession.deleted_at.is_(None))
                .order_by(VoiceConsultationSession.id, VoiceConsultationTurn.turn_no)
            )
            rows = []
            for s, t, robot_name in session.execute(stmt).all():
                rows.append({
                    "session_id": str(s.id),
                    "robot_name": robot_name or "",
                    "session_occurred_at": timezone.ftime(s.occurred_at),
                    "trigger_method": s.trigger_method,
                    "session_status": s.status,
                    "session_intent_type": s.intent_type,
                    "turn_count": s.turn_count,
                    "question_summary": s.question_summary,
                    "session_duration_seconds": s.duration_seconds,
                    "turn_no": t.turn_no if t else None,
                    "question": t.question if t else None,
                    "answer": t.answer if t else None,
                    "turn_intent_type": t.intent_type if t else None,
                    "turn_duration_seconds": t.duration_seconds if t else None,
                    "turn_occurred_at": timezone.ftime(t.occurred_at) if t and t.occurred_at else None,
                })
            return rows
    finally:
        engine.dispose()


def main():
    parser = argparse.ArgumentParser(description="导出语音问诊会话及轮次明细到 Excel")
    default_name = f"voice_consultations_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
    parser.add_argument("-o", "--output", default=default_name, help="输出文件路径（.xlsx）")
    args = parser.parse_args()

    rows = fetch_rows()
    if not rows:
        print("没有可导出的问诊会话数据")
        return

    data = build_excel_bytes(COLUMNS, rows, sheet_name="问诊对话明细")
    with open(args.output, "wb") as f:
        f.write(data)

    session_count = sum(1 for _ in groupby(rows, key=lambda r: r["session_id"]))
    print(f"导出完成: {args.output}")
    print(f"会话数: {session_count}，总行数(轮次): {len(rows)}")


if __name__ == "__main__":
    main()
