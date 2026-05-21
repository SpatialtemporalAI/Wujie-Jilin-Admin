#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
登录日志管理接口
"""
import logging
from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from database.db_manager import get_session
from core.response import ResponseModel, response_base
from modules.admin.deps.auth.user_manager import current_user
from app.models.sys.user import SysUser
from modules.admin.services.sys.login_log_service import LoginLogService
from modules.admin.schemas.sys.login_log import (
    LoginLogQueryParams,
    LoginLogResponse,
    LoginLogDetailResponse,
)

logger = logging.getLogger(__name__)

login_log_router = APIRouter(prefix="/login-log", tags=["系统管理/登录日志"])


def _to_response(log) -> dict:
    def format_datetime(dt):
        if dt:
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        return None

    return {
        "id": log.id,
        "username": log.username,
        "ip": log.ip,
        "status": log.status,
        "detail": log.detail,
        "user_agent": log.user_agent,
        "login_time": format_datetime(log.login_time),
        "created_at": format_datetime(log.created_at),
    }


@login_log_router.get(
    "/list",
    response_model=ResponseModel,
    summary="获取登录日志列表",
)
async def get_log_list(
    username: str | None = Query(None, description="登录用户名"),
    ip: str | None = Query(None, description="客户端IP"),
    status: bool | None = Query(None, description="登录状态"),
    start_time: str | None = Query(None, description="开始时间"),
    end_time: str | None = Query(None, description="结束时间"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    user: SysUser = Depends(current_user),
    db: AsyncSession = Depends(get_session),
):
    query_params = LoginLogQueryParams(
        username=username,
        ip=ip,
        status=status,
        start_time=start_time,
        end_time=end_time,
        page=page,
        page_size=page_size,
    )
    logs, total = await LoginLogService.get_log_list(db, query_params)
    items = [_to_response(log) for log in logs]
    return response_base.success(
        data={"items": items, "total": total, "page": page, "page_size": page_size},
        msg="获取登录日志列表成功",
    )


@login_log_router.get(
    "/{log_id}",
    response_model=ResponseModel[LoginLogDetailResponse],
    summary="获取登录日志详情",
)
async def get_log_detail(
    log_id: int,
    user: SysUser = Depends(current_user),
    db: AsyncSession = Depends(get_session),
):
    log = await LoginLogService.get_log(db, log_id)
    data = _to_response(log)
    return response_base.success(data=data, msg="获取登录日志详情成功")


@login_log_router.delete(
    "/{log_id}",
    response_model=ResponseModel,
    summary="删除单条登录日志",
)
async def delete_log(
    log_id: int,
    user: SysUser = Depends(current_user),
    db: AsyncSession = Depends(get_session),
):
    count = await LoginLogService.batch_delete_logs(db, [log_id])
    return response_base.success(data={"deleted": count}, msg="删除成功")


@login_log_router.delete(
    "/batch/delete",
    response_model=ResponseModel,
    summary="批量删除登录日志",
)
async def batch_delete_logs(
    log_ids: List[int] = Body(..., description="日志ID列表"),
    user: SysUser = Depends(current_user),
    db: AsyncSession = Depends(get_session),
):
    count = await LoginLogService.batch_delete_logs(db, log_ids)
    return response_base.success(data={"deleted": count}, msg="批量删除成功")


@login_log_router.delete(
    "/clear",
    response_model=ResponseModel,
    summary="清理过期登录日志",
)
async def clear_logs(
    days: int = Query(30, description="清理多少天前的日志"),
    user: SysUser = Depends(current_user),
    db: AsyncSession = Depends(get_session),
):
    count = await LoginLogService.clear_logs(db, days)
    return response_base.success(
        data={"deleted": count}, msg=f"已清理 {days} 天前的日志"
    )
