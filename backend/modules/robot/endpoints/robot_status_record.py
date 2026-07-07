#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
机器人状态记录相关接口
"""
import logging
from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from database.db_manager import get_session
from core.response.response_schema import (
    ResponseModel,
    ResponsePageModel,
    response_base,
)
from app.models.common.page import PageRequest, get_page_params, get_paginated_results
from modules.admin.deps.auth.user_manager import current_user
from modules.admin.deps.auth.permission import (
    require_permission,
    require_any_permission,
)

from modules.robot.services.robot_status_record_service import RobotStatusRecordService
from modules.robot.schemas.robot_status_record import (
    RobotStatusRecordQueryParams,
    RobotStatusRecordResponseData,
    RobotLocationItem,
)

logger = logging.getLogger(__name__)

robot_status_record_router = APIRouter(
    prefix="/manage", tags=["机器人状态记录"], dependencies=[Depends(current_user)]
)


@robot_status_record_router.get(
    "/{robot_id}/status/list",
    response_model=ResponsePageModel[RobotStatusRecordResponseData],
    dependencies=[Depends(require_permission("robot:manage:list"))],
)
async def get_robot_status_record_list(
    robot_id: int = Path(..., description="机器人ID"),
    page_params: PageRequest = Depends(get_page_params),
    db: AsyncSession = Depends(get_session),
):
    """
    获取机器人状态记录列表（分页）
    """
    try:
        logger.info("获取机器人状态记录列表接口被调用，机器人ID: %d", robot_id)

        query_params = RobotStatusRecordQueryParams(robot_id=robot_id)
        query = RobotStatusRecordService.build_query(query_params)

        page_data = await get_paginated_results(
            db=db,
            page_params=page_params,
            query=query,
            schema=RobotStatusRecordResponseData,
        )

        logger.info(
            "获取机器人状态记录列表接口成功，机器人ID: %d，共 %d 条记录",
            robot_id,
            page_data.total,
        )
        return response_base.page(data=page_data)

    except Exception as e:
        logger.error("获取机器人状态记录列表接口失败: %s", str(e), exc_info=True)
        raise


@robot_status_record_router.get(
    "/{robot_id}/status/latest",
    response_model=ResponseModel[Optional[RobotStatusRecordResponseData]],
)
async def get_robot_status_latest(
    robot_id: int = Path(..., description="机器人ID"),
    db: AsyncSession = Depends(get_session),
):
    """
    获取机器人最新状态记录
    """
    try:
        logger.info("获取机器人最新状态记录接口被调用，机器人ID: %d", robot_id)

        record = await RobotStatusRecordService.get_latest(db, robot_id)

        if record:
            response_data = RobotStatusRecordResponseData.model_validate(record)
            logger.info("获取机器人最新状态记录接口成功，机器人ID: %d", robot_id)
            return response_base.success(data=response_data)
        else:
            logger.info("机器人无状态记录，机器人ID: %d", robot_id)
            return response_base.success(data=None, msg="暂无状态记录")

    except Exception as e:
        logger.error("获取机器人最新状态记录接口失败: %s", str(e), exc_info=True)
        raise


@robot_status_record_router.get(
    "/map/{map_id}/robot-locations",
    response_model=ResponseModel[List[RobotLocationItem]],
    dependencies=[
        Depends(
            require_any_permission("robot:manage:list", "scene:map-editor:edit")
        )
    ],
)
async def get_map_robot_locations(
    map_id: int = Path(..., description="场景地图ID"),
    db: AsyncSession = Depends(get_session),
):
    """按地图查询其绑定机器人的实时位置（地图编辑器画布展示用）

    位置数据由外部写入 DB，本接口只读。透传 location_info(JSON) 与
    location(Text 历史字段)，前端按优先级解析坐标。

    权限：该接口为地图编辑器画布专用，与 bind-map 一致，机器人管理与地图编辑器
    任一权限通过即可，避免地图编辑器用户因缺少 robot:manage:list 而跨权限报错。
    """
    try:
        items = await RobotStatusRecordService.get_map_robot_locations(db, map_id)
        return response_base.success(data=items)

    except Exception as e:
        logger.error("按地图查询机器人位置接口失败: %s", str(e), exc_info=True)
        raise
