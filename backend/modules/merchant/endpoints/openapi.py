#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
商户开放 API（HMAC 签名鉴权）
供第三方商户调用机器人能力。
"""
import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.db_manager import get_session
from database.models.business.merchant import Merchant
from core.response.response_schema import ResponseModel
from modules.merchant.deps.auth import get_current_merchant
from modules.merchant.services.openapi_service import OpenApiService
from modules.merchant.schemas.openapi import (
    GotoPointRequest,
    NavigateRouteRequest,
    ExecuteTaskRequest,
    RobotSnRequest,
    SpeakRequest,
    ScenesRequest,
    PointsRequest,
    TasksRequest,
    OpenApiResult,
)

logger = logging.getLogger(__name__)

openapi_router = APIRouter(
    prefix="/openapi/v1",
    tags=["商户开放API"],
)


@openapi_router.post("/goto_point", response_model=ResponseModel[OpenApiResult])
async def goto_point(
    body: GotoPointRequest,
    db: AsyncSession = Depends(get_session),
    merchant: Merchant = Depends(get_current_merchant),
):
    """单点导航：前往指定点位"""
    result = await OpenApiService.goto_point(db, merchant, body.robot_sn, body.point_id)
    return ResponseModel(data=result)


@openapi_router.post("/navigate_route", response_model=ResponseModel[OpenApiResult])
async def navigate_route(
    body: NavigateRouteRequest,
    db: AsyncSession = Depends(get_session),
    merchant: Merchant = Depends(get_current_merchant),
):
    """多点导航：按顺序途经多个点位"""
    result = await OpenApiService.navigate_route(
        db, merchant, body.robot_sn, body.point_ids
    )
    return ResponseModel(data=result)


@openapi_router.post("/execute_task", response_model=ResponseModel[OpenApiResult])
async def execute_task(
    body: ExecuteTaskRequest,
    db: AsyncSession = Depends(get_session),
    merchant: Merchant = Depends(get_current_merchant),
):
    """执行任务：在指定机器人上启动/恢复任务"""
    result = await OpenApiService.execute_task(
        db, merchant, body.robot_sn, body.task_id
    )
    return ResponseModel(data=result)


@openapi_router.post("/pause_task", response_model=ResponseModel[OpenApiResult])
async def pause_task(
    body: RobotSnRequest,
    db: AsyncSession = Depends(get_session),
    merchant: Merchant = Depends(get_current_merchant),
):
    """暂停该机器人当前任务"""
    result = await OpenApiService.pause_task(db, merchant, body.robot_sn)
    return ResponseModel(data=result)


@openapi_router.post("/resume_task", response_model=ResponseModel[OpenApiResult])
async def resume_task(
    body: RobotSnRequest,
    db: AsyncSession = Depends(get_session),
    merchant: Merchant = Depends(get_current_merchant),
):
    """恢复该机器人已暂停的任务"""
    result = await OpenApiService.resume_task(db, merchant, body.robot_sn)
    return ResponseModel(data=result)


@openapi_router.post("/stop_task", response_model=ResponseModel[OpenApiResult])
async def stop_task(
    body: RobotSnRequest,
    db: AsyncSession = Depends(get_session),
    merchant: Merchant = Depends(get_current_merchant),
):
    """停止该机器人当前任务"""
    result = await OpenApiService.stop_task(db, merchant, body.robot_sn)
    return ResponseModel(data=result)


@openapi_router.post("/speak", response_model=ResponseModel[OpenApiResult])
async def speak(
    body: SpeakRequest,
    db: AsyncSession = Depends(get_session),
    merchant: Merchant = Depends(get_current_merchant),
):
    """语音播报"""
    result = await OpenApiService.speak(
        db, merchant, body.robot_sn, body.text, body.tts_params
    )
    return ResponseModel(data=result)


@openapi_router.post("/scenes", response_model=ResponseModel[OpenApiResult])
async def list_scenes(
    body: ScenesRequest,
    db: AsyncSession = Depends(get_session),
    merchant: Merchant = Depends(get_current_merchant),
):
    """获取商户可访问的场景列表（其机器人绑定的场景地图）"""
    result = await OpenApiService.list_scenes(db, merchant, body.robot_sn)
    return ResponseModel(data=result)


@openapi_router.post("/points", response_model=ResponseModel[OpenApiResult])
async def list_points(
    body: PointsRequest,
    db: AsyncSession = Depends(get_session),
    merchant: Merchant = Depends(get_current_merchant),
):
    """获取指定场景下的点位列表"""
    result = await OpenApiService.list_points(db, merchant, body.map_id)
    return ResponseModel(data=result)


@openapi_router.post("/tasks", response_model=ResponseModel[OpenApiResult])
async def list_tasks(
    body: TasksRequest,
    db: AsyncSession = Depends(get_session),
    merchant: Merchant = Depends(get_current_merchant),
):
    """获取关联到商户机器人的任务列表"""
    result = await OpenApiService.list_tasks(
        db,
        merchant,
        robot_sn=body.robot_sn,
        map_id=body.map_id,
        task_type=body.task_type,
        status=body.status,
    )
    return ResponseModel(data=result)
