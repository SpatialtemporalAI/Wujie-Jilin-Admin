#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from database.models.base import Base
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import String, Integer, ForeignKey, Boolean


class RobotVoiceConfig(Base):
    """
    机器人语音配置表
    按机器人存储唤醒词与TTS参数
    """

    robot_id: Mapped[int] = mapped_column(
        ForeignKey("robot.id"),
        nullable=False,
        unique=True,
        comment="机器人ID",
    )
    wake_word_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        server_default="false",
        comment="是否启用唤醒词：True-启用，False-禁用",
    )
    wake_word: Mapped[str | None] = mapped_column(
        String(20), nullable=True, default=None, comment="唤醒词"
    )
    tts_voice: Mapped[str | None] = mapped_column(
        String(50), nullable=True, default=None, comment="音色"
    )
    tts_speed: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=None, comment="语速"
    )
    tts_volume: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=None, comment="音量"
    )
