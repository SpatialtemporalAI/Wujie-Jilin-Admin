#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from database.models.base import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import Text, ForeignKey
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .robot import Robot


class RobotStatusRecord(Base):
    """
    机器人状态记录表
    """

    robot_id: Mapped[int] = mapped_column(
        ForeignKey("robot.id"), nullable=False, comment="机器人ID"
    )
    battery: Mapped[float] = mapped_column(default=0, comment="电量百分比")
    signal: Mapped[int] = mapped_column(default=0, comment="信号强度")
    speed: Mapped[float] = mapped_column(default=0, comment="速度(m/s)")
    location: Mapped[str | None] = mapped_column(
        Text, nullable=True, default=None, comment="位置信息(JSON)"
    )

    robot: Mapped["Robot"] = relationship(
        back_populates="status_records",
        lazy="noload",
        init=False,
    )
