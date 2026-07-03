#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
任务管理接口
"""
import logging
from fastapi import APIRouter, Depends, Path, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

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
from database.models.business.task import Task, task_robot_association
from database.models.business.task_point import TaskPoint
from database.models.business.task_execution_record import TaskExecutionRecord
from database.models.business.robot import Robot
from database.models.business.scene_map import SceneMap

from modules.task.services.task_service import TaskService
from modules.task.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskQueryParams,
    TaskResponseData,
    TaskToggleEnabled,
    TaskPointResponse,
    TaskRobotBrief,
)

logger = logging.getLogger(__name__)


async def _fill_task_map_name(db: AsyncSession, records: list[TaskResponseData]) -> None:
    map_ids = {record.map_id for record in records if record.map_id is not None}
    if not map_ids:
        return
    result = await db.execute(
        select(SceneMap.id, SceneMap.name).where(
            SceneMap.id.in_(map_ids),
            SceneMap.deleted_at.is_(None),
        )
    )
    name_map = {row.id: row.name for row in result.all()}
    for record in records:
        if record.map_id is not None:
            record.map_name = name_map.get(record.map_id)


async def _build_task_robot_briefs(db: AsyncSession, robots: list[Robot]) -> list[TaskRobotBrief]:
    map_ids = {robot.map_id for robot in robots if robot.map_id is not None}
    map_name_map: dict[int, str] = {}
    if map_ids:
        map_result = await db.execute(
            select(SceneMap.id, SceneMap.name).where(
                SceneMap.id.in_(map_ids),
                SceneMap.deleted_at.is_(None),
            )
        )
        map_name_map = {row.id: row.name for row in map_result.all()}

    return [
        TaskRobotBrief(
            id=robot.id,
            name=robot.name,
            status=robot.status.value if hasattr(robot.status, 'value') else str(robot.status),
            map_id=robot.map_id,
            map_name=map_name_map.get(robot.map_id) if robot.map_id is not None else None,
        )
        for robot in robots
    ]


task_router = APIRouter(
    prefix="/manage", tags=["任务管理"], dependencies=[Depends(current_user)]
)


async def _build_task_response(task_obj: Task, db: AsyncSession, include_details: bool = False) -> TaskResponseData:
    """构建任务响应数据"""
    data = TaskResponseData.model_validate(task_obj)

    # 获取点位数量
    if task_obj.points is not None:
        data.point_count = len(task_obj.points)
        if include_details:
            data.points = [TaskPointResponse.model_validate(p) for p in task_obj.points]
    else:
        count_result = await db.execute(
            select(TaskPoint).where(
                TaskPoint.task_id == task_obj.id,
                TaskPoint.deleted_at.is_(None),
            )
        )
        points = count_result.scalars().all()
        data.point_count = len(points)
        if include_details:
            data.points = [TaskPointResponse.model_validate(p) for p in points]

    # 活跃执行数（running/pending）
    from sqlalchemy import func
    active_result = await db.execute(
        select(func.count())
        .select_from(TaskExecutionRecord)
        .where(
            TaskExecutionRecord.task_id == task_obj.id,
            TaskExecutionRecord.status.in_(["running", "pending"]),
            TaskExecutionRecord.deleted_at.is_(None),
        )
    )
    data.active_execution_count = active_result.scalar() or 0

    # 获取关联机器人
    if task_obj.robots is not None:
        data.robots = await _build_task_robot_briefs(db, list(task_obj.robots))
    else:
        robot_result = await db.execute(
            select(Robot)
            .join(task_robot_association, Robot.id == task_robot_association.c.robot_id)
            .where(task_robot_association.c.task_id == task_obj.id)
            .where(Robot.deleted_at.is_(None))
        )
        robots = robot_result.scalars().all()
        data.robots = await _build_task_robot_briefs(db, list(robots))

    await _fill_task_map_name(db, [data])

    return data


@task_router.get(
    "/list",
    response_model=ResponsePageModel[TaskResponseData],
    dependencies=[Depends(require_permission("task:list"))],
)
async def get_task_list(
    query_params: TaskQueryParams = Depends(),
    page_params: PageRequest = Depends(get_page_params),
    db: AsyncSession = Depends(get_session),
):
    """获取任务列表（分页）"""
    try:
        query = TaskService.build_query(query_params)
        page_data = await get_paginated_results(
            db=db,
            page_params=page_params,
            query=query,
            schema=TaskResponseData,
        )

        # 补充点位数量和机器人信息
        if page_data.records:
            from sqlalchemy import func

            task_ids = [record.id for record in page_data.records]

            # 批量查询活跃执行数（running/pending），避免 N+1
            active_count_map: dict[int, int] = {}
            if task_ids:
                active_result = await db.execute(
                    select(TaskExecutionRecord.task_id, func.count())
                    .where(
                        TaskExecutionRecord.task_id.in_(task_ids),
                        TaskExecutionRecord.status.in_(["running", "pending"]),
                        TaskExecutionRecord.deleted_at.is_(None),
                    )
                    .group_by(TaskExecutionRecord.task_id)
                )
                active_count_map = {
                    row[0]: row[1] for row in active_result.all()
                }

            for record in page_data.records:
                task_id = record.id

                # 活跃执行数
                record.active_execution_count = active_count_map.get(task_id, 0)

                # 点位数量
                count_q = select(func.count()).select_from(TaskPoint).where(
                    TaskPoint.task_id == task_id, TaskPoint.deleted_at.is_(None)
                )
                count_result = await db.execute(count_q)
                record.point_count = count_result.scalar() or 0

                # 机器人信息
                robot_result = await db.execute(
                    select(Robot)
                    .join(task_robot_association, Robot.id == task_robot_association.c.robot_id)
                    .where(task_robot_association.c.task_id == task_id)
                    .where(Robot.deleted_at.is_(None))
                )
                robots = robot_result.scalars().all()
                record.robots = await _build_task_robot_briefs(db, list(robots))

            await _fill_task_map_name(db, list(page_data.records))

        return response_base.page(data=page_data)

    except Exception as e:
        logger.error("获取任务列表失败: %s", str(e), exc_info=True)
        raise


@task_router.get(
    "/{task_id}",
    response_model=ResponseModel[TaskResponseData],
)
async def get_task(
    task_id: int = Path(..., description="任务ID"),
    db: AsyncSession = Depends(get_session),
):
    """获取单个任务详情"""
    try:
        task_obj = await TaskService.get_with_relations(db, task_id)
        response_data = await _build_task_response(task_obj, db, include_details=True)
        return response_base.success(data=response_data)

    except Exception as e:
        logger.error("获取任务详情失败: %s", str(e), exc_info=True)
        raise


@task_router.post(
    "/add",
    response_model=ResponseModel[TaskResponseData],
    dependencies=[Depends(require_permission("task:add"))],
)
@log_operation(module="task", action="create", description="创建任务")
async def create_task(
    request: Request,
    task_in: TaskCreate,
    db: AsyncSession = Depends(get_session),
    user: SysUser = Depends(current_user),
):
    """创建任务"""
    try:
        task_obj = await TaskService.create(db, task_in)
        response_data = await _build_task_response(task_obj, db, include_details=True)
        return response_base.success(data=response_data, msg="创建成功")

    except Exception as e:
        logger.error("创建任务失败: %s", str(e), exc_info=True)
        raise


@task_router.put(
    "/{task_id}",
    response_model=ResponseModel[TaskResponseData],
    dependencies=[Depends(require_permission("task:edit"))],
)
@log_operation(module="task", action="update", description="更新任务")
async def update_task(
    request: Request,
    task_in: TaskUpdate,
    task_id: int = Path(..., description="任务ID"),
    db: AsyncSession = Depends(get_session),
    user: SysUser = Depends(current_user),
):
    """更新任务"""
    try:
        task_obj = await TaskService.update(db, task_id, task_in)
        response_data = await _build_task_response(task_obj, db, include_details=True)
        return response_base.success(data=response_data, msg="更新成功")

    except Exception as e:
        logger.error("更新任务失败: %s", str(e), exc_info=True)
        raise


@task_router.delete(
    "/{task_id}",
    response_model=ResponseModel,
    dependencies=[Depends(require_permission("task:delete"))],
)
@log_operation(module="task", action="delete", description="删除任务")
async def delete_task(
    request: Request,
    task_id: int = Path(..., description="任务ID"),
    db: AsyncSession = Depends(get_session),
    user: SysUser = Depends(current_user),
):
    """删除任务"""
    try:
        await TaskService.delete(db, task_id)
        return response_base.success(msg="删除成功")

    except Exception as e:
        logger.error("删除任务失败: %s", str(e), exc_info=True)
        raise


@task_router.put(
    "/{task_id}/toggle",
    response_model=ResponseModel[TaskResponseData],
    dependencies=[Depends(require_permission("task:edit"))],
)
async def toggle_task_enabled(
    toggle_in: TaskToggleEnabled,
    task_id: int = Path(..., description="任务ID"),
    db: AsyncSession = Depends(get_session),
):
    """切换任务启用/禁用"""
    try:
        task_obj = await TaskService.toggle_enabled(db, task_id, toggle_in.enabled)
        response_data = await _build_task_response(task_obj, db)
        return response_base.success(data=response_data, msg="操作成功")

    except Exception as e:
        logger.error("切换任务启用状态失败: %s", str(e), exc_info=True)
        raise
