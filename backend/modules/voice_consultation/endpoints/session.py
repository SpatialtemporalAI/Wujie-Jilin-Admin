#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
语音问诊会话管理接口
"""
import logging

from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.common.page import PageRequest, get_page_params, get_paginated_results
from core.response import ResponseModel, ResponsePageModel, response_base
from database.db_manager import get_session
from database.models.sys.user import SysUser
from modules.admin.deps.auth.permission import require_permission
from modules.admin.deps.auth.user_manager import current_user
from modules.voice_consultation.schemas.session import (
    VoiceConsultationSessionDetailResponse,
    VoiceConsultationSessionQueryParams,
    VoiceConsultationSessionResponse,
    VoiceConsultationStatsResponse,
)
from modules.voice_consultation.services.session_service import VoiceConsultationSessionService

logger = logging.getLogger(__name__)

voice_consultation_session_router = APIRouter(
    prefix="/sessions", tags=["语音问诊/会话记录"], dependencies=[Depends(current_user)]
)


@voice_consultation_session_router.get(
    "/list",
    response_model=ResponsePageModel[VoiceConsultationSessionResponse],
    summary="获取语音问诊会话列表",
    dependencies=[Depends(require_permission("voice:consultation:list"))],
)
async def get_voice_consultation_session_list(
    query_params: VoiceConsultationSessionQueryParams = Depends(),
    page_params: PageRequest = Depends(get_page_params),
    user: SysUser = Depends(current_user),
    db: AsyncSession = Depends(get_session),
):
    """分页查询语音问诊会话列表"""
    query = VoiceConsultationSessionService.build_session_query(query_params)
    page_data = await get_paginated_results(
        db=db,
        page_params=page_params,
        query=query,
        schema=VoiceConsultationSessionResponse,
    )
    if page_data.records:
        await VoiceConsultationSessionService.fill_robot_names(db, page_data.records)
    return response_base.page(data=page_data)


@voice_consultation_session_router.get(
    "/stats",
    response_model=ResponseModel[VoiceConsultationStatsResponse],
    summary="获取语音问诊统计数据",
    dependencies=[Depends(require_permission("voice:consultation:list"))],
)
async def get_voice_consultation_stats(
    query_params: VoiceConsultationSessionQueryParams = Depends(),
    user: SysUser = Depends(current_user),
    db: AsyncSession = Depends(get_session),
):
    """查询语音问诊统计（总量/今日/平均时长带环比 + 意图分布 + 触发方式分布）"""
    stats = await VoiceConsultationSessionService.get_stats(db, query_params)
    return response_base.success(data=stats, msg="获取语音问诊统计数据成功")


@voice_consultation_session_router.get(
    "/{session_id}",
    response_model=ResponseModel[VoiceConsultationSessionDetailResponse],
    summary="获取语音问诊会话详情",
    dependencies=[Depends(require_permission("voice:consultation:detail"))],
)
async def get_voice_consultation_session_detail(
    session_id: int = Path(..., description="会话ID"),
    user: SysUser = Depends(current_user),
    db: AsyncSession = Depends(get_session),
):
    """获取单条语音问诊会话详情（含轮次明细）"""
    session = await VoiceConsultationSessionService.get_session_with_turns(db, session_id)
    response_data = VoiceConsultationSessionDetailResponse.model_validate(session)
    await VoiceConsultationSessionService.fill_robot_names(db, [response_data])
    return response_base.success(data=response_data, msg="获取语音问诊会话详情成功")
