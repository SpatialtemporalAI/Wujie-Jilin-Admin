#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
商户开放 API 调用日志管理接口（后台，JWT 鉴权 + 权限校验）
"""
import io
import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, Query, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from database.db_manager import get_session
from core.response import ResponseModel, ResponsePageModel, response_base
from app.models.common.page import PageRequest, get_page_params, get_paginated_results
from core.utils.excel_export import build_excel_bytes, SYNC_EXPORT_MAX_ROWS
from modules.admin.deps.auth.user_manager import current_user
from modules.admin.deps.auth.permission import require_permission
from modules.admin.exports import get_export_config
from database.models.sys.user import SysUser
from modules.merchant.services.call_log_service import CallLogService
from modules.merchant.schemas.call_log import (
    CallLogQueryParams,
    CallLogResponse,
    CallLogDetailResponse,
)

logger = logging.getLogger(__name__)

call_log_router = APIRouter(
    prefix="/merchant/call-log",
    tags=["开放商户/调用日志"],
    dependencies=[Depends(current_user)],
)


@call_log_router.get(
    "/list",
    response_model=ResponsePageModel[CallLogResponse],
    summary="获取商户调用日志列表",
    dependencies=[Depends(require_permission("merchant:call-log:list"))],
)
async def get_call_log_list(
    query_params: CallLogQueryParams = Depends(),
    page_params: PageRequest = Depends(get_page_params),
    user: SysUser = Depends(current_user),
    db: AsyncSession = Depends(get_session),
):
    """分页查询商户开放 API 调用日志列表"""
    query = CallLogService.build_call_log_query(query_params)
    page_data = await get_paginated_results(
        db=db,
        page_params=page_params,
        query=query,
        schema=CallLogResponse,
    )
    return response_base.page(data=page_data)


@call_log_router.get("/export", summary="导出商户调用日志 Excel")
async def export_call_logs(
    merchant_id: int | None = Query(None, description="商户ID"),
    action: str | None = Query(None, description="动作"),
    success: bool | None = Query(None, description="是否成功"),
    start_time: str | None = Query(None, description="开始时间"),
    end_time: str | None = Query(None, description="结束时间"),
    api_key: str | None = Query(None, description="API Key（脱敏值模糊匹配）"),
    user: SysUser = Depends(current_user),
    db: AsyncSession = Depends(get_session),
):
    """导出商户调用日志为 Excel 文件"""
    query_params = CallLogQueryParams(
        merchant_id=merchant_id,
        action=action,
        success=success,
        start_time=start_time,
        end_time=end_time,
        api_key=api_key,
    )
    config = get_export_config("merchant_call_log")
    query = config.build_query_fn(query_params).limit(SYNC_EXPORT_MAX_ROWS)
    result = await db.execute(query)
    rows = result.scalars().all()

    excel_bytes = build_excel_bytes(config.columns, rows, sheet_name=config.name)
    filename = f"merchant_call_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@call_log_router.delete(
    "/batch/delete",
    response_model=ResponseModel,
    summary="批量删除调用日志",
    dependencies=[Depends(require_permission("merchant:call-log:delete"))],
)
async def batch_delete_logs(
    log_ids: List[int] = Body(..., description="日志ID列表"),
    user: SysUser = Depends(current_user),
    db: AsyncSession = Depends(get_session),
):
    """批量删除调用日志"""
    count = await CallLogService.batch_delete_logs(db, log_ids)
    return response_base.success(data={"deleted": count}, msg="批量删除成功")


@call_log_router.delete(
    "/clear",
    response_model=ResponseModel,
    summary="清理过期调用日志",
    dependencies=[Depends(require_permission("merchant:call-log:delete"))],
)
async def clear_logs(
    days: int = Query(30, description="清理多少天前的日志"),
    user: SysUser = Depends(current_user),
    db: AsyncSession = Depends(get_session),
):
    """清理指定天数前的调用日志"""
    count = await CallLogService.clear_logs(db, days)
    return response_base.success(data={"deleted": count}, msg=f"已清理 {days} 天前的日志")


@call_log_router.get(
    "/{log_id}",
    response_model=ResponseModel[CallLogDetailResponse],
    summary="获取调用日志详情",
    dependencies=[Depends(require_permission("merchant:call-log:list"))],
)
async def get_call_log_detail(
    log_id: int,
    user: SysUser = Depends(current_user),
    db: AsyncSession = Depends(get_session),
):
    """获取单条调用日志详情（含脱敏后的请求参数/响应结果）"""
    log = await CallLogService.get_log(db, log_id)
    return response_base.success(
        data=CallLogDetailResponse.model_validate(log),
        msg="获取调用日志详情成功",
    )


@call_log_router.delete(
    "/{log_id}",
    response_model=ResponseModel,
    summary="删除单条调用日志",
    dependencies=[Depends(require_permission("merchant:call-log:delete"))],
)
async def delete_log(
    log_id: int,
    user: SysUser = Depends(current_user),
    db: AsyncSession = Depends(get_session),
):
    """删除单条调用日志"""
    count = await CallLogService.batch_delete_logs(db, [log_id])
    return response_base.success(data={"deleted": count}, msg="删除成功")
