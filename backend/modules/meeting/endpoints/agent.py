#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
会议管理 - 机器人 agent 上报开放接口

鉴权：请求头 X-Agent-Token 与 settings.MEETING.AGENT_TOKEN 一致；
      AGENT_TOKEN 为空时不校验（仅建议开发环境）。
"""
import logging

from fastapi import APIRouter, Depends, File, Header, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.exception.errors import ForbiddenError, RequestError
from core.response import ResponseModel, response_base
from database.db_manager import get_session
from modules.admin.services.sys.file_service import FileService
from modules.meeting.schemas.agent import (
    AgentFileUploadResponse,
    AgentMinuteReportPayload,
    AgentMinuteReportResponse,
)
from modules.meeting.services.minute_service import MinuteService

logger = logging.getLogger(__name__)

agent_meeting_router = APIRouter(
    prefix="/openapi/v1/meeting",
    tags=["会议管理/agent 上报"],
)


async def verify_agent_token(
    x_agent_token: str | None = Header(None, description="agent 上报鉴权 Token"),
) -> None:
    """校验 agent 上报告警 Token（未配置时跳过）"""
    expected = (settings.MEETING.AGENT_TOKEN or "").strip()
    if not expected:
        return
    if (x_agent_token or "").strip() != expected:
        raise ForbiddenError(msg="X-Agent-Token 无效")


@agent_meeting_router.post(
    "/files",
    response_model=ResponseModel[AgentFileUploadResponse],
    summary="agent 上传会议音频",
    dependencies=[Depends(verify_agent_token)],
)
async def upload_meeting_file(
    file: UploadFile = File(..., description="会议音频文件"),
    db: AsyncSession = Depends(get_session),
):
    """上传音频到平台文件存储，返回 file_id 供纪要上报引用"""
    file_data = await file.read()
    if not file_data:
        raise RequestError(msg="上传文件为空")

    sys_file = await FileService.upload_file(
        db=db,
        file_data=file_data,
        original_name=file.filename or "meeting-audio.webm",
        mime_type=file.content_type or "application/octet-stream",
        created_by=0,
    )
    url = await FileService.get_file_url(db, sys_file.id)
    data = AgentFileUploadResponse(
        file_id=sys_file.id,
        url=url,
        original_name=sys_file.original_name,
        file_size=sys_file.file_size,
        mime_type=sys_file.mime_type,
    )
    return response_base.success(data=data, msg="文件上传成功")


@agent_meeting_router.post(
    "/minutes/report",
    response_model=ResponseModel[AgentMinuteReportResponse],
    summary="agent 上报会议纪要",
    dependencies=[Depends(verify_agent_token)],
)
async def report_meeting_minute(
    body: AgentMinuteReportPayload,
    db: AsyncSession = Depends(get_session),
):
    """按 meeting_no 幂等上报：已存在则覆盖更新，不存在则新建"""
    minute, created = await MinuteService.report(db, body)
    data = AgentMinuteReportResponse(
        id=minute.id,
        meeting_no=minute.meeting_no,
        created=created,
        speaker_count=minute.speaker_count,
        segment_count=minute.segment_count,
    )
    return response_base.success(data=data, msg="会议纪要上报成功")
