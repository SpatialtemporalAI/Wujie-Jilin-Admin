#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
任务执行记录接口（独立版本，对应 task_execution_record 表）
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

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
from database.models.business.scene_map import SceneMap

from modules.task.services.task_execution_record_service import (
    TaskExecutionRecordService,
)
from modules.task.schemas.task_execution_record import (
    TaskExecutionRecordQueryParams,
    TaskExecutionRecordStartIn,
    TaskExecutionRecordResponseData,
    TaskExecutionRecordDetailResponseData,
)

logger = logging.getLogger(__name__)

task_execution_record_router = APIRouter(
    prefix="/execution-record",
    tags=["任务执行记录"],
    dependencies=[Depends(current_user)],
)


async def _fill_relations(record: TaskExecutionRecordResponseData, db: AsyncSession) -> None:
    """填充机器人名/场景名/用户名"""
    if record.robot_id is not None:
        robot_result = await db.execute(
            select(Robot.name).where(
                Robot.id == record.robot_id, Robot.deleted_at.is_(None)
            )
        )
        record.robot_name = robot_result.scalar_one_or_none()

    if record.scene_id is not None:
        scene_result = await db.execute(
            select(SceneMap.name).where(
                SceneMap.id == record.scene_id, SceneMap.deleted_at.is_(None)
            )
        )
        record.scene_name = scene_result.scalar_one_or_none()

    if record.user_id is not None:
        user_result = await db.execute(
            select(SysUser.username).where(SysUser.id == record.user_id)
        )
        record.user_name = user_result.scalar_one_or_none()


@task_execution_record_router.post(
    "/{task_id}/start",
    response_model=ResponseModel[TaskExecutionRecordResponseData],
    dependencies=[Depends(require_permission("task:execution:start"))],
)
@log_operation(module="task", action="start", description="启动任务（新执行记录表）")
async def start_task_execution_record(
    task_id: int,
    payload: TaskExecutionRecordStartIn,
    db: AsyncSession = Depends(get_session),
    user: SysUser = Depends(current_user),
):
    """启动任务执行（创建执行记录）"""
    try:
        records = await TaskExecutionRecordService.start_execution(
            db=db,
            task_id=task_id,
            robot_ids=payload.robot_ids,
            user_id=user.id,
            source=payload.source,
        )
        # 返回首条记录作为响应
        data = TaskExecutionRecordResponseData.model_validate(records[0])
        await _fill_relations(data, db)
        return response_base.success(data=data, msg="任务已启动")
    except Exception as e:
        logger.error("启动任务执行失败: %s", str(e), exc_info=True)
        raise


@task_execution_record_router.post(
    "/start-or-resume/{task_id}",
    response_model=ResponseModel,
    dependencies=[Depends(require_permission("task:execution:start"))],
)
@log_operation(module="task", action="start", description="启动或恢复任务")
async def start_or_resume_task_execution_record(
    task_id: int,
    payload: TaskExecutionRecordStartIn,
    request: Request,
    db: AsyncSession = Depends(get_session),
    user: SysUser = Depends(current_user),
):
    """
    启动或恢复任务：
    - 若该任务存在 paused 状态的执行记录，则批量恢复
    - 否则按 robot_ids 创建新的执行记录
    """
    try:
        result = await TaskExecutionRecordService.start_or_resume_execution(
            db=db,
            task_id=task_id,
            robot_ids=payload.robot_ids,
            user_id=user.id,
            source=payload.source,
        )
        if result["action"] == "resumed":
            msg = f"已恢复 {result['count']} 条暂停的执行"
        else:
            msg = f"已启动 {result['count']} 条新执行"
        return response_base.success(msg=msg)
    except Exception as e:
        logger.error("启动或恢复任务失败: %s", str(e), exc_info=True)
        raise


@task_execution_record_router.post(
    "/{record_id}/pause",
    response_model=ResponseModel[TaskExecutionRecordResponseData],
    dependencies=[Depends(require_permission("task:execution:control"))],
)
async def pause_execution_record(
    record_id: int,
    db: AsyncSession = Depends(get_session),
):
    """暂停执行"""
    try:
        record = await TaskExecutionRecordService.pause_execution(db, record_id)
        data = TaskExecutionRecordResponseData.model_validate(record)
        await _fill_relations(data, db)
        return response_base.success(data=data, msg="任务已暂停")
    except Exception as e:
        logger.error("暂停任务执行失败: %s", str(e), exc_info=True)
        raise


@task_execution_record_router.post(
    "/pause-by-task/{task_id}",
    response_model=ResponseModel,
    dependencies=[Depends(require_permission("task:execution:control"))],
)
@log_operation(module="task", action="pause", description="按任务批量暂停执行")
async def pause_executions_by_task(
    task_id: int,
    request: Request,
    db: AsyncSession = Depends(get_session),
    user: SysUser = Depends(current_user),
):
    """按任务 ID 批量暂停该任务下所有 running/pending 执行记录"""
    try:
        count = await TaskExecutionRecordService.pause_executions_by_task(db, task_id)
        msg = f"已暂停 {count} 条执行" if count > 0 else "该任务当前没有可暂停的执行"
        return response_base.success(msg=msg)
    except Exception as e:
        logger.error("按任务暂停执行失败: %s", str(e), exc_info=True)
        raise


@task_execution_record_router.post(
    "/{record_id}/resume",
    response_model=ResponseModel[TaskExecutionRecordResponseData],
    dependencies=[Depends(require_permission("task:execution:control"))],
)
async def resume_execution_record(
    record_id: int,
    db: AsyncSession = Depends(get_session),
):
    """恢复执行"""
    try:
        record = await TaskExecutionRecordService.resume_execution(db, record_id)
        data = TaskExecutionRecordResponseData.model_validate(record)
        await _fill_relations(data, db)
        return response_base.success(data=data, msg="任务已恢复")
    except Exception as e:
        logger.error("恢复任务执行失败: %s", str(e), exc_info=True)
        raise


@task_execution_record_router.post(
    "/{record_id}/stop",
    response_model=ResponseModel[TaskExecutionRecordResponseData],
    dependencies=[Depends(require_permission("task:execution:control"))],
)
@log_operation(module="task", action="stop", description="停止任务（新执行记录表）")
async def stop_execution_record(
    record_id: int,
    db: AsyncSession = Depends(get_session),
):
    """停止执行"""
    try:
        record = await TaskExecutionRecordService.stop_execution(db, record_id)
        data = TaskExecutionRecordResponseData.model_validate(record)
        await _fill_relations(data, db)
        return response_base.success(data=data, msg="任务已停止")
    except Exception as e:
        logger.error("停止任务执行失败: %s", str(e), exc_info=True)
        raise


@task_execution_record_router.get(
    "/active",
    response_model=ResponsePageModel[TaskExecutionRecordResponseData],
    dependencies=[Depends(require_permission("task:list"))],
)
async def get_active_execution_records(
    query_params: TaskExecutionRecordQueryParams = Depends(),
    page_params: PageRequest = Depends(get_page_params),
    db: AsyncSession = Depends(get_session),
):
    """获取活跃执行列表（running/paused）"""
    try:
        query = TaskExecutionRecordService.build_active_query(query_params)
        page_data = await get_paginated_results(
            db=db,
            page_params=page_params,
            query=query,
            schema=TaskExecutionRecordResponseData,
        )

        if page_data.records:
            for record in page_data.records:
                await _fill_relations(record, db)

        return response_base.page(data=page_data)
    except Exception as e:
        logger.error("获取活跃执行列表失败: %s", str(e), exc_info=True)
        raise


@task_execution_record_router.get(
    "/history",
    response_model=ResponsePageModel[TaskExecutionRecordResponseData],
    dependencies=[Depends(require_permission("task:list"))],
)
async def get_execution_record_history(
    query_params: TaskExecutionRecordQueryParams = Depends(),
    page_params: PageRequest = Depends(get_page_params),
    db: AsyncSession = Depends(get_session),
):
    """获取历史执行记录（completed/failed/cancelled）"""
    try:
        query = TaskExecutionRecordService.build_history_query(query_params)
        page_data = await get_paginated_results(
            db=db,
            page_params=page_params,
            query=query,
            schema=TaskExecutionRecordResponseData,
        )

        if page_data.records:
            for record in page_data.records:
                await _fill_relations(record, db)

        return response_base.page(data=page_data)
    except Exception as e:
        logger.error("获取历史执行记录失败: %s", str(e), exc_info=True)
        raise


@task_execution_record_router.get(
    "/detail/{record_id}",
    response_model=ResponseModel[TaskExecutionRecordDetailResponseData],
    dependencies=[Depends(require_permission("task:list"))],
)
async def get_execution_record_detail(
    record_id: int,
    db: AsyncSession = Depends(get_session),
):
    """获取执行详情（含完整 task_definition 和 progress）"""
    try:
        record = await TaskExecutionRecordService.get_execution_detail(db, record_id)
        data = TaskExecutionRecordDetailResponseData.model_validate(record)
        await _fill_relations(data, db)
        return response_base.success(data=data)
    except Exception as e:
        logger.error("获取执行详情失败: %s", str(e), exc_info=True)
        raise
