#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from database.models.base import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String, Enum as SaEnum, ForeignKey
from typing import TYPE_CHECKING, List
import enum

if TYPE_CHECKING:
    from .robot_model import RobotModel
    from .robot_status_record import RobotStatusRecord


class RobotStatus(str, enum.Enum):
    """机器人状态枚举"""

    ONLINE = "online"
    OFFLINE = "offline"
    INACTIVE = "inactive"


class Robot(Base):
    """
    机器人表
    """

    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="机器人名称")
    model_id: Mapped[int] = mapped_column(
        ForeignKey("robot_model.id"),
        nullable=False,
        comment="型号ID",
    )
    serial_number: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, comment="序列号"
    )
    status: Mapped[RobotStatus] = mapped_column(
        SaEnum(RobotStatus, values_callable=lambda e: [x.value for x in e]),
        default=RobotStatus.INACTIVE,
        comment="状态：online-在线，offline-离线，inactive-未激活",
    )

    robot_model: Mapped["RobotModel"] = relationship(
        back_populates="robots",
        lazy="noload",
        init=False,
    )
    status_records: Mapped[List["RobotStatusRecord"]] = relationship(
        back_populates="robot",
        lazy="noload",
        init=False,
    )
