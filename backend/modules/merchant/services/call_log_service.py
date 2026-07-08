#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
商户开放 API 调用日志管理服务
"""
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from database.models.business.merchant_call_log import MerchantCallLog
from core.exception.errors import NotFoundError
from modules.merchant.schemas.call_log import CallLogQueryParams

logger = logging.getLogger(__name__)


class CallLogService:
    """商户开放 API 调用日志管理服务类"""

    @staticmethod
    def build_call_log_query(query_params: CallLogQueryParams):
        """构建调用日志查询（供导出和列表共用）"""
        conditions = []

        if query_params.merchant_id:
            conditions.append(MerchantCallLog.merchant_id == query_params.merchant_id)
        if query_params.action:
            conditions.append(MerchantCallLog.action == query_params.action)
        if query_params.success is not None:
            conditions.append(MerchantCallLog.success == query_params.success)
        if query_params.api_key:
            conditions.append(
                MerchantCallLog.api_key_masked.like(f"%{query_params.api_key}%")
            )
        if query_params.start_time:
            try:
                dt = datetime.fromisoformat(query_params.start_time)
                start = (
                    dt.astimezone(timezone.utc)
                    if dt.tzinfo
                    else dt.replace(tzinfo=timezone.utc)
                )
                conditions.append(MerchantCallLog.created_at >= start)
            except ValueError:
                pass
        if query_params.end_time:
            try:
                dt = datetime.fromisoformat(query_params.end_time)
                end = (
                    dt.astimezone(timezone.utc)
                    if dt.tzinfo
                    else dt.replace(tzinfo=timezone.utc)
                )
                conditions.append(MerchantCallLog.created_at <= end)
            except ValueError:
                pass

        base_query = select(MerchantCallLog)
        if conditions:
            base_query = base_query.where(and_(*conditions))

        base_query = base_query.order_by(MerchantCallLog.created_at.desc())
        return base_query

    @staticmethod
    async def get_log(db: AsyncSession, log_id: int) -> MerchantCallLog:
        """获取单条调用日志"""
        result = await db.execute(
            select(MerchantCallLog).where(MerchantCallLog.id == log_id)
        )
        log = result.scalar_one_or_none()
        if not log:
            raise NotFoundError(msg=f"调用日志 {log_id} 不存在")
        return log

    @staticmethod
    async def batch_delete_logs(db: AsyncSession, log_ids: List[int]) -> int:
        """批量删除调用日志"""
        stmt = delete(MerchantCallLog).where(MerchantCallLog.id.in_(log_ids))
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount

    @staticmethod
    async def clear_logs(db: AsyncSession, days: int = 30) -> int:
        """清理指定天数前的调用日志"""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = delete(MerchantCallLog).where(MerchantCallLog.created_at < cutoff)
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount
