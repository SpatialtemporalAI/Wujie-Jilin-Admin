#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
会议管理 - 声纹注册接口
"""
import logging

from fastapi import APIRouter, Depends, File, Form, Path, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.common.page import PageRequest, get_page_params, get_paginated_results
from core.exception.errors import RequestError
from core.response import ResponseModel, ResponsePageModel, response_base
from database.db_manager import get_session
from database.models.sys.user import SysUser
from modules.admin.deps.auth.permission import require_permission
from modules.admin.deps.auth.user_manager import current_user
from modules.meeting.schemas.voiceprint import (
    ROLE_TYPES,
    VOICEPRINT_METHODS,
    MeetingModeStatusData,
    MeetingModeUpdate,
    VoiceprintOverviewData,
    VoiceprintQueryParams,
    VoiceprintRegisterResponse,
    VoiceprintResponse,
    VoiceprintRobotItem,
)
from modules.meeting.services.voiceprint_service import VoiceprintService
from modules.robot.services.robot_meeting_mode_service import RobotMeetingModeService
from modules.robot.services.robot_service import RobotService

logger = logging.getLogger(__name__)

voiceprint_router = APIRouter(
    prefix="/voiceprint",
    tags=["会议管理/声纹注册"],
    dependencies=[Depends(current_user)],
)


@voiceprint_router.get(
    "/robots",
    response_model=ResponseModel[list[VoiceprintRobotItem]],
    summary="声纹页机器人列表",
    dependencies=[Depends(require_permission("meeting:voiceprint:list"))],
)
async def get_voiceprint_robots(
    user: SysUser = Depends(current_user),
    db: AsyncSession = Depends(get_session),
):
    """返回可选机器人（含型号、在线状态、会议模式、已注册声纹数）"""
    data = await VoiceprintService.list_robots(db)
    return response_base.success(data=data, msg="获取机器人列表成功")


@voiceprint_router.get(
    "/overview",
    response_model=ResponseModel[VoiceprintOverviewData],
    summary="声纹页概览",
    dependencies=[Depends(require_permission("meeting:voiceprint:list"))],
)
async def get_voiceprint_overview(
    robot_id: int = Query(..., description="机器人ID"),
    user: SysUser = Depends(current_user),
    db: AsyncSession = Depends(get_session),
):
    """会议模式状态 + 已注册声纹数量"""
    data = await VoiceprintService.get_overview(db, robot_id)
    return response_base.success(data=data, msg="获取概览成功")


@voiceprint_router.get(
    "/list",
    response_model=ResponsePageModel[VoiceprintResponse],
    summary="声纹注册记录列表",
    dependencies=[Depends(require_permission("meeting:voiceprint:list"))],
)
async def get_voiceprint_list(
    query_params: VoiceprintQueryParams = Depends(),
    page_params: PageRequest = Depends(get_page_params),
    user: SysUser = Depends(current_user),
    db: AsyncSession = Depends(get_session),
):
    """分页查询声纹注册记录"""
    query = VoiceprintService.build_query(query_params)
    page_data = await get_paginated_results(
        db=db,
        page_params=page_params,
        query=query,
        schema=VoiceprintResponse,
    )
    if page_data.records:
        await VoiceprintService.fill_robot_names(db, page_data.records)
    return response_base.page(data=page_data)


@voiceprint_router.post(
    "/register",
    response_model=ResponseModel[VoiceprintRegisterResponse],
    summary="上传录音并注册声纹",
    dependencies=[Depends(require_permission("meeting:voiceprint:add"))],
)
async def register_voiceprint(
    robot_id: int = Form(..., description="机器人ID"),
    role_name: str = Form(..., description="发言人姓名"),
    role_type: str = Form(..., description="角色类型：主持人/发言人/记录员/旁听"),
    method: str = Form("record", description="录入方式：record/stream"),
    transcript_hint: str = Form("", description="录音对应的文本提示（可选）"),
    audio: UploadFile = File(..., description="浏览器录制的音频文件"),
    user: SysUser = Depends(current_user),
    db: AsyncSession = Depends(get_session),
):
    """浏览器录音 -> 平台存储 -> 下发 agent 建模 -> 返回注册结果"""
    if role_type not in ROLE_TYPES:
        raise RequestError(msg=f"角色类型不合法，可选：{'、'.join(sorted(ROLE_TYPES))}")
    if method not in VOICEPRINT_METHODS:
        raise RequestError(msg="录入方式不合法，可选：record、stream")

    file_data = await audio.read()
    if not file_data:
        raise RequestError(msg="录音文件为空，请重新录制")

    record = await VoiceprintService.register(
        db=db,
        robot_id=robot_id,
        role_name=role_name,
        role_type=role_type,
        method=method,
        file_data=file_data,
        original_name=audio.filename or f"{role_name}.webm",
        mime_type=audio.content_type or "application/octet-stream",
        transcript_hint=transcript_hint,
        user_id=user.id,
    )
    response_data = VoiceprintRegisterResponse.model_validate(record)
    robot = await RobotService.get(db, robot_id)
    response_data.robot_name = robot.name

    if record.status == "success":
        msg = "声纹注册成功"
    else:
        msg = record.error_msg or "声纹注册失败"
    return response_base.success(data=response_data, msg=msg)


@voiceprint_router.delete(
    "/{record_id}",
    response_model=ResponseModel,
    summary="删除声纹",
    dependencies=[Depends(require_permission("meeting:voiceprint:delete"))],
)
async def delete_voiceprint(
    record_id: int = Path(..., description="声纹记录ID"),
    user: SysUser = Depends(current_user),
    db: AsyncSession = Depends(get_session),
):
    """删除平台声纹记录，并尽力删除 agent 侧声纹"""
    await VoiceprintService.delete(db, record_id)
    return response_base.success(msg="删除声纹成功")


@voiceprint_router.put(
    "/meeting-mode",
    response_model=ResponseModel[MeetingModeStatusData],
    summary="切换会议模式",
    dependencies=[Depends(require_permission("meeting:voiceprint:meeting_mode"))],
)
async def update_meeting_mode(
    body: MeetingModeUpdate,
    user: SysUser = Depends(current_user),
    db: AsyncSession = Depends(get_session),
):
    """开启/关闭机器人会议模式（实时下发 agent）"""
    robot = await RobotService.get(db, body.robot_id)
    meeting_mode = await RobotMeetingModeService.set_meeting_mode(db, robot, body.enabled)
    registered_count = await VoiceprintService.count_registered(db, body.robot_id)
    data = MeetingModeStatusData(
        meeting_mode=meeting_mode if meeting_mode is not None else bool(robot.meeting_mode),
        registered_count=registered_count,
    )
    return response_base.success(
        data=data,
        msg="已进入会议模式" if data.meeting_mode else "已退出会议模式",
    )
