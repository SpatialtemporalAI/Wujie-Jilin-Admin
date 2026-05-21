#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from core.models.base import Base
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import String, Text, Integer, Float


class SysOperationLog(Base):
    """
    系统操作日志表
    记录用户的关键业务操作
    """

    user_id: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True, comment="操作人ID"
    )
    username: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="操作人用户名"
    )
    module: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="操作模块"
    )
    action: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="操作类型"
    )
    description: Mapped[str] = mapped_column(
        String(255), nullable=True, comment="操作描述"
    )
    method: Mapped[str] = mapped_column(
        String(10), nullable=True, comment="HTTP方法"
    )
    path: Mapped[str] = mapped_column(
        String(255), nullable=True, comment="请求路径"
    )
    ip: Mapped[str] = mapped_column(
        String(50), nullable=True, comment="客户端IP"
    )
    request_params: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="请求参数"
    )
    response_code: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="响应状态码"
    )
    response_result: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="响应结果"
    )
    elapsed_ms: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="耗时(毫秒)"
    )
