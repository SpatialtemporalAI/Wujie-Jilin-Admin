#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime

from sqlalchemy import String, Text, Integer, BigInteger, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from core.models.base import Base


class SysExportTask(Base):
    """异步导出任务表"""

    task_name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="任务名称"
    )
    module_key: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True, comment="模块标识"
    )
    template_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, comment="导出模板ID"
    )
    query_params_json: Mapped[str] = mapped_column(
        Text, nullable=False, comment="查询参数JSON"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending",
        comment="状态: pending/processing/completed/failed",
    )
    total_rows: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="导出总行数"
    )
    file_path: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="文件存储路径"
    )
    file_size: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="文件大小(字节)"
    )
    error_message: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="错误信息"
    )
    created_by: Mapped[int] = mapped_column(
        BigInteger, nullable=False, comment="创建者ID"
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="开始执行时间"
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="执行完成时间"
    )
