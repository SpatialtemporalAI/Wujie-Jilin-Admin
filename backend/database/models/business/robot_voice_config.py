#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from database.models.base import Base
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import String, Integer


class RobotVoiceConfig(Base):
    """
    机器人语音配置表
    全局单条配置，用于存储唤醒词与TTS参数
    """

    wake_word: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="唤醒词"
    )
    tts_voice: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="音色"
    )
    tts_speed: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="语速"
    )
    tts_volume: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="音量"
    )
