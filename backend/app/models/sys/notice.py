#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
系统通知/公告表
存储系统公告、操作提醒、审批通知等
"""

from datetime import datetime
from typing import Optional, List

from sqlalchemy import String, Text, Boolean, DateTime, BigInteger
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import mapped_column, Mapped

from core.models.base import Base


class NoticeType:
    """通知类型常量"""
    ANNOUNCEMENT = "announcement"
    SYSTEM = "system"
    OPERATION = "operation"
    APPROVAL = "approval"


class NoticeTargetType:
    """推送目标类型常量"""
    ALL = "all"
    ROLE = "role"
    USER = "user"


class NoticePriority:
    """通知优先级常量"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class SysNotice(Base):
    """
    系统通知表
    存储系统公告、操作提醒、审批通知等
    """

    # 通知基本信息（必填字段放在前面，无 Python 默认值）
    title: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="通知标题"
    )
    content: Mapped[str] = mapped_column(
        Text, nullable=False, comment="通知内容（支持HTML）"
    )

    # 发送者信息（必填字段，无默认值，必须放在有默认值的字段之前）
    sender_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, comment="发送者用户ID"
    )
    sender_name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="发送者名称"
    )

    # 以下为有默认值的字段，必须排在所有无默认值字段之后
    type: Mapped[str] = mapped_column(
        String(50), nullable=False, default=NoticeType.SYSTEM,
        comment="通知类型：announcement-公告, system-系统, operation-操作提醒, approval-审批通知"
    )
    target_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default=NoticeTargetType.ALL,
        comment="推送范围：all-全员, role-按角色, user-按指定用户"
    )
    target_role_ids: Mapped[Optional[List[int]]] = mapped_column(
        ARRAY(BigInteger), nullable=True, default=None,
        comment="目标角色ID列表（target_type=role时有效）"
    )
    target_user_ids: Mapped[Optional[List[int]]] = mapped_column(
        ARRAY(BigInteger), nullable=True, default=None,
        comment="目标用户ID列表（target_type=user时有效）"
    )
    priority: Mapped[str] = mapped_column(
        String(20), nullable=False, default=NoticePriority.NORMAL,
        comment="优先级：low-低, normal-普通, high-高, urgent-紧急"
    )
    status: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="状态：True-已发布, False-草稿"
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None, comment="发布时间"
    )
