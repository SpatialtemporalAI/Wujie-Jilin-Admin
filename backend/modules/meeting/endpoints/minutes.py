#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
会议管理 - 会议纪要接口
"""
import logging

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.common.page import PageRequest, get_page_params, get_paginated_results
from core.response import ResponseModel, ResponsePageModel, response_base
from database.db_manager import get_session
from database.models.sys.user import SysUser
from modules.admin.deps.auth.permission import require_permission
from modules.admin.deps.auth.user_manager import current_user
from modules.meeting.schemas.minutes import (
    MinuteDetailResponse,
    MinuteExportData,
    MinuteListItem,
    MinuteQueryParams,
    MinuteTrashClearResponse,
    SegmentSpeakerUpdate,
)
from modules.meeting.services.minute_service import MinuteService

logger = logging.getLogger(__name__)

minutes_router = APIRouter(
    prefix="/minutes",
    tags=["会议管理/会议纪要"],
    dependencies=[Depends(current_user)],
)


@minutes_router.get(
    "/list",
    response_model=ResponsePageModel[MinuteListItem],
    summary="会议纪要列表",
    dependencies=[Depends(require_permission("meeting:minutes:list"))],
)
async def get_minute_list(
    query_params: MinuteQueryParams = Depends(),
    page_params: PageRequest = Depends(get_page_params),
    user: SysUser = Depends(current_user),
    db: AsyncSession = Depends(get_session),
):
    """分页查询会议纪要（不含回收站）"""
    query = MinuteService.build_query(query_params, trash=False)
    page_data = await get_paginated_results(
        db=db,
        page_params=page_params,
        query=query,
        schema=MinuteListItem,
    )
    if page_data.records:
        await MinuteService.fill_robot_info(db, page_data.records)
        await MinuteService.fill_speakers(db, page_data.records)
    return response_base.page(data=page_data)


@minutes_router.get(
    "/trash",
    response_model=ResponsePageModel[MinuteListItem],
    summary="回收站列表",
    dependencies=[Depends(require_permission("meeting:minutes:delete"))],
)
async def get_minute_trash(
    query_params: MinuteQueryParams = Depends(),
    page_params: PageRequest = Depends(get_page_params),
    user: SysUser = Depends(current_user),
    db: AsyncSession = Depends(get_session),
):
    """分页查询回收站中的会议纪要"""
    query = MinuteService.build_query(query_params, trash=True)
    page_data = await get_paginated_results(
        db=db,
        page_params=page_params,
        query=query,
        schema=MinuteListItem,
    )
    if page_data.records:
        await MinuteService.fill_robot_info(db, page_data.records)
        await MinuteService.fill_speakers(db, page_data.records)
    return response_base.page(data=page_data)


@minutes_router.delete(
    "/trash/clear",
    response_model=ResponseModel[MinuteTrashClearResponse],
    summary="清空回收站",
    dependencies=[Depends(require_permission("meeting:minutes:delete"))],
)
async def clear_minute_trash(
    user: SysUser = Depends(current_user),
    db: AsyncSession = Depends(get_session),
):
    """彻底删除回收站中的所有会议纪要"""
    purged_count = await MinuteService.clear_trash(db)
    return response_base.success(
        data=MinuteTrashClearResponse(purged_count=purged_count),
        msg=f"已彻底删除 {purged_count} 条会议纪要",
    )


@minutes_router.get(
    "/{minute_id}",
    response_model=ResponseModel[MinuteDetailResponse],
    summary="会议纪要详情",
    dependencies=[Depends(require_permission("meeting:minutes:detail"))],
)
async def get_minute_detail(
    minute_id: int = Path(..., description="会议纪要ID"),
    user: SysUser = Depends(current_user),
    db: AsyncSession = Depends(get_session),
):
    """获取会议纪要详情（发言人 + 逐字稿）"""
    data = await MinuteService.get_detail(db, minute_id)
    return response_base.success(data=data, msg="获取会议纪要详情成功")


@minutes_router.put(
    "/segments/{segment_id}/speaker",
    response_model=ResponseModel,
    summary="改派逐字稿发言人",
    dependencies=[Depends(require_permission("meeting:minutes:edit"))],
)
async def update_segment_speaker(
    body: SegmentSpeakerUpdate,
    segment_id: int = Path(..., description="逐字稿片段ID"),
    user: SysUser = Depends(current_user),
    db: AsyncSession = Depends(get_session),
):
    """人工修正低置信片段的发言人归属"""
    await MinuteService.update_segment_speaker(db, segment_id, body.speaker_id)
    return response_base.success(msg="发言人改派成功")


@minutes_router.get(
    "/{minute_id}/export",
    response_model=ResponseModel[MinuteExportData],
    summary="导出会议纪要",
    dependencies=[Depends(require_permission("meeting:minutes:export"))],
)
async def export_minute(
    minute_id: int = Path(..., description="会议纪要ID"),
    fmt: str = Query("md", alias="format", description="导出格式：md/txt"),
    user: SysUser = Depends(current_user),
    db: AsyncSession = Depends(get_session),
):
    """导出会议纪要内容（前端据 content 生成文件下载）"""
    data = await MinuteService.export(db, minute_id, fmt=fmt)
    return response_base.success(data=data, msg="导出成功")


@minutes_router.delete(
    "/{minute_id}",
    response_model=ResponseModel,
    summary="删除会议纪要（移入回收站）",
    dependencies=[Depends(require_permission("meeting:minutes:delete"))],
)
async def delete_minute(
    minute_id: int = Path(..., description="会议纪要ID"),
    user: SysUser = Depends(current_user),
    db: AsyncSession = Depends(get_session),
):
    """软删除会议纪要"""
    await MinuteService.soft_delete(db, minute_id)
    return response_base.success(msg="已移入回收站")


@minutes_router.post(
    "/{minute_id}/restore",
    response_model=ResponseModel,
    summary="恢复会议纪要",
    dependencies=[Depends(require_permission("meeting:minutes:delete"))],
)
async def restore_minute(
    minute_id: int = Path(..., description="会议纪要ID"),
    user: SysUser = Depends(current_user),
    db: AsyncSession = Depends(get_session),
):
    """从回收站恢复会议纪要"""
    await MinuteService.restore(db, minute_id)
    return response_base.success(msg="恢复成功")


@minutes_router.delete(
    "/{minute_id}/purge",
    response_model=ResponseModel,
    summary="彻底删除会议纪要",
    dependencies=[Depends(require_permission("meeting:minutes:delete"))],
)
async def purge_minute(
    minute_id: int = Path(..., description="会议纪要ID"),
    user: SysUser = Depends(current_user),
    db: AsyncSession = Depends(get_session),
):
    """彻底删除会议纪要及其发言人/逐字稿"""
    await MinuteService.purge(db, minute_id)
    return response_base.success(msg="彻底删除成功")
