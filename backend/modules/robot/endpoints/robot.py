#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
机器人管理相关接口
"""
import logging
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import noload

from database.db_manager import get_session
from core.response.response_schema import (
    ResponseModel,
    ResponsePageModel,
    response_base,
)
from app.models.common.page import PageRequest, get_page_params, get_paginated_results
from core.decorators.operation_log import log_operation
from modules.admin.deps.auth.user_manager import current_user
from modules.admin.deps.auth.permission import require_permission
from database.models.sys.user import SysUser
from database.models.business.robot import Robot
from database.models.business.robot_model import RobotModel

from modules.robot.services.robot_service import RobotService
from modules.robot.schemas.robot import (
    RobotCreate,
    RobotUpdate,
    RobotQueryParams,
    RobotResponseData,
)

logger = logging.getLogger(__name__)

robot_router = APIRouter(
    prefix="/manage", tags=["机器人管理"], dependencies=[Depends(current_user)]
)


def _build_robot_response(robot_obj: Robot, db: AsyncSession = None, model_name: str = None) -> RobotResponseData:
    """
    构建机器人响应数据，附带 model_name
    """
    data = RobotResponseData.model_validate(robot_obj)
    if model_name:
        data.model_name = model_name
    return data


@robot_router.get(
    "/list",
    response_model=ResponsePageModel[RobotResponseData],
    dependencies=[Depends(require_permission("robot:manage:list"))],
)
async def get_robot_list(
    query_params: RobotQueryParams = Depends(),
    page_params: PageRequest = Depends(get_page_params),
    db: AsyncSession = Depends(get_session),
):
    """
    获取机器人列表（分页）
    """
    try:
        logger.info("获取机器人列表接口被调用")

        query = RobotService.build_query(query_params)

        page_data = await get_paginated_results(
            db=db,
            page_params=page_params,
            query=query,
            schema=RobotResponseData,
        )

        # 批量获取 model_name
        if page_data.records:
            model_ids = list(set(r.model_id for r in page_data.records))
            model_result = await db.execute(
                select(RobotModel).where(RobotModel.id.in_(model_ids))
            )
            model_map = {m.id: m.name for m in model_result.scalars().all()}
            for record in page_data.records:
                record.model_name = model_map.get(record.model_id)

        logger.info("获取机器人列表接口成功，共 %d 条记录", page_data.total)
        return response_base.page(data=page_data)

    except Exception as e:
        logger.error("获取机器人列表接口失败: %s", str(e), exc_info=True)
        raise


@robot_router.get(
    "/{robot_id}",
    response_model=ResponseModel[RobotResponseData],
)
async def get_robot(
    robot_id: int,
    db: AsyncSession = Depends(get_session),
):
    """
    获取单个机器人
    """
    try:
        logger.info("获取机器人详情接口被调用，机器人ID: %d", robot_id)

        robot_obj = await RobotService.get(db, robot_id)
        response_data = RobotResponseData.model_validate(robot_obj)

        # 获取 model_name
        model_result = await db.execute(
            select(RobotModel.name).where(RobotModel.id == robot_obj.model_id)
        )
        model_name = model_result.scalar_one_or_none()
        response_data.model_name = model_name

        logger.info("获取机器人详情接口成功，机器人ID: %d", robot_id)
        return response_base.success(data=response_data)

    except Exception as e:
        logger.error("获取机器人详情接口失败: %s", str(e), exc_info=True)
        raise


@robot_router.post(
    "/add",
    response_model=ResponseModel[RobotResponseData],
    dependencies=[Depends(require_permission("robot:manage:add"))],
)
@log_operation(module="robot", action="create", description="创建机器人")
async def create_robot(
    request: Request,
    robot_in: RobotCreate,
    db: AsyncSession = Depends(get_session),
    user: SysUser = Depends(current_user),
):
    """
    创建机器人
    """
    try:
        logger.info("创建机器人接口被调用")

        robot_obj = await RobotService.create(db, robot_in)
        response_data = RobotResponseData.model_validate(robot_obj)

        # 获取 model_name
        model_result = await db.execute(
            select(RobotModel.name).where(RobotModel.id == robot_obj.model_id)
        )
        response_data.model_name = model_result.scalar_one_or_none()

        logger.info("创建机器人接口成功，机器人ID: %d", robot_obj.id)
        return response_base.success(data=response_data, msg="创建成功")

    except Exception as e:
        logger.error("创建机器人接口失败: %s", str(e), exc_info=True)
        raise


@robot_router.put(
    "/{robot_id}",
    response_model=ResponseModel[RobotResponseData],
    dependencies=[Depends(require_permission("robot:manage:edit"))],
)
@log_operation(module="robot", action="update", description="更新机器人")
async def update_robot(
    robot_id: int,
    request: Request,
    robot_in: RobotUpdate,
    db: AsyncSession = Depends(get_session),
    user: SysUser = Depends(current_user),
):
    """
    更新机器人
    """
    try:
        logger.info("更新机器人接口被调用，机器人ID: %d", robot_id)

        robot_obj = await RobotService.update(db, robot_id, robot_in)
        response_data = RobotResponseData.model_validate(robot_obj)

        # 获取 model_name
        model_result = await db.execute(
            select(RobotModel.name).where(RobotModel.id == robot_obj.model_id)
        )
        response_data.model_name = model_result.scalar_one_or_none()

        logger.info("更新机器人接口成功，机器人ID: %d", robot_id)
        return response_base.success(data=response_data, msg="更新成功")

    except Exception as e:
        logger.error("更新机器人接口失败: %s", str(e), exc_info=True)
        raise


@robot_router.delete(
    "/{robot_id}",
    response_model=ResponseModel,
    dependencies=[Depends(require_permission("robot:manage:delete"))],
)
@log_operation(module="robot", action="delete", description="删除机器人")
async def delete_robot(
    robot_id: int,
    request: Request,
    db: AsyncSession = Depends(get_session),
    user: SysUser = Depends(current_user),
):
    """
    删除机器人
    """
    try:
        logger.info("删除机器人接口被调用，机器人ID: %d", robot_id)

        await RobotService.delete(db, robot_id)

        logger.info("删除机器人接口成功，机器人ID: %d", robot_id)
        return response_base.success(msg="删除成功")

    except Exception as e:
        logger.error("删除机器人接口失败: %s", str(e), exc_info=True)
        raise
