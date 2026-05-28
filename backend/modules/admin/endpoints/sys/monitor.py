#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
系统监控接口
"""
import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.db_manager import get_session
from core.response import ResponseModel, response_base
from modules.admin.deps.auth.user_manager import current_user
from modules.admin.deps.auth.permission import require_permission
from modules.admin.services.sys.monitor_service import MonitorService
from modules.admin.schemas.sys.monitor import (
    SystemMetricsResponse,
    ApiStatsQueryParams,
    ApiStatsResponse,
)

logger = logging.getLogger(__name__)

monitor_router = APIRouter(prefix="/monitor", tags=["系统管理/监控仪表盘"])


@monitor_router.get(
    "/metrics",
    response_model=ResponseModel[SystemMetricsResponse],
    summary="获取系统实时指标",
    dependencies=[Depends(require_permission("sys:monitor:view"))],
)
async def get_system_metrics(
    user=Depends(current_user),
):
    """获取CPU、内存、磁盘等系统实时指标"""
    data = await MonitorService.get_system_metrics()
    return response_base.success(data=data)


@monitor_router.get(
    "/api-stats",
    response_model=ResponseModel[list[ApiStatsResponse]],
    summary="获取API统计信息",
    dependencies=[Depends(require_permission("sys:monitor:view"))],
)
async def get_api_stats(
    query_params: ApiStatsQueryParams = Depends(),
    user=Depends(current_user),
    db: AsyncSession = Depends(get_session),
):
    """从操作日志中按时间窗口聚合API响应时间和错误率"""
    data = await MonitorService.get_api_stats(db=db, minutes=query_params.minutes)
    return response_base.success(data=data)
