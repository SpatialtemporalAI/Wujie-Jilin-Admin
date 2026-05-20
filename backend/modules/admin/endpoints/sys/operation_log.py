#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
操作日志管理接口
"""
import logging
from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from database.db_manager import get_session
from core.response import ResponseModel, response_base
from app.models.common.page import get_page_params
from modules.admin.deps.auth.user_manager import current_user
from app.models.sys.user import SysUser
from modules.admin.services.sys.operation_log_service import OperationLogService
from modules.admin.schemas.sys.operation_log import (
    OperationLogQueryParams,
    OperationLogResponse,
    OperationLogDetailResponse,
)

logger = logging.getLogger(__name__)

operation_log_router = APIRouter(prefix="/operation-log", tags=["系统管理/操作日志"])


def _to_response(log) -> dict:
    def format_datetime(dt):
        if dt:
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        return None

    return {
        "id": log.id,
        "user_id": log.user_id,
        "username": log.username,
        "module": log.module,
        "action": log.action,
        "description": log.description,
        "method": log.method,
        "path": log.path,
        "ip": log.ip,
        "response_code": log.response_code,
        "elapsed_ms": log.elapsed_ms,
        "created_at": format_datetime(log.created_at),
    }


@operation_log_router.get(
    "/list",
    response_model=ResponseModel,
    summary="获取操作日志列表",
)
async def get_log_list(
    module: str | None = Query(None, description="操作模块"),
    action: str | None = Query(None, description="操作类型"),
    user_id: int | None = Query(None, description="操作人ID"),
    username: str | None = Query(None, description="操作人用户名"),
    start_time: str | None = Query(None, description="开始时间"),
    end_time: str | None = Query(None, description="结束时间"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    user: SysUser = Depends(current_user),
    db: AsyncSession = Depends(get_session),
):
    query_params = OperationLogQueryParams(
        module=module,
        action=action,
        user_id=user_id,
        username=username,
        start_time=start_time,
        end_time=end_time,
        page=page,
        page_size=page_size,
    )
    logs, total = await OperationLogService.get_log_list(db, query_params)
    items = [_to_response(log) for log in logs]
    return response_base.success(
        data={"items": items, "total": total, "page": page, "page_size": page_size},
        msg="获取操作日志列表成功",
    )


@operation_log_router.get(
    "/{log_id}",
    response_model=ResponseModel[OperationLogDetailResponse],
    summary="获取操作日志详情",
)
async def get_log_detail(
    log_id: int,
    user: SysUser = Depends(current_user),
    db: AsyncSession = Depends(get_session),
):
    log = await OperationLogService.get_log(db, log_id)
    data = _to_response(log)
    data["request_params"] = log.request_params
    return response_base.success(data=data, msg="获取操作日志详情成功")


@operation_log_router.delete(
    "/{log_id}",
    response_model=ResponseModel,
    summary="删除单条操作日志",
)
async def delete_log(
    log_id: int,
    user: SysUser = Depends(current_user),
    db: AsyncSession = Depends(get_session),
):
    ids = [log_id]
    count = await OperationLogService.batch_delete_logs(db, ids)
    return response_base.success(data={"deleted": count}, msg="删除成功")


@operation_log_router.delete(
    "/batch/delete",
    response_model=ResponseModel,
    summary="批量删除操作日志",
)
async def batch_delete_logs(
    log_ids: List[int] = Body(..., description="日志ID列表"),
    user: SysUser = Depends(current_user),
    db: AsyncSession = Depends(get_session),
):
    count = await OperationLogService.batch_delete_logs(db, log_ids)
    return response_base.success(data={"deleted": count}, msg="批量删除成功")


@operation_log_router.delete(
    "/clear",
    response_model=ResponseModel,
    summary="清理过期操作日志",
)
async def clear_logs(
    days: int = Query(30, description="清理多少天前的日志"),
    user: SysUser = Depends(current_user),
    db: AsyncSession = Depends(get_session),
):
    count = await OperationLogService.clear_logs(db, days)
    return response_base.success(
        data={"deleted": count}, msg=f"已清理 {days} 天前的日志"
    )
