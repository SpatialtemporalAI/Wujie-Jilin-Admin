#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
任务管理接口
"""
import logging
from fastapi import APIRouter, Depends, Path, Request, UploadFile, File
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
from modules.task.services.performance_music_service import (
    PerformanceMusicService,
    PRESET_MUSIC_FILE_IDS,
    UPLOAD_MUSIC_PREFIX,
)
from modules.task.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskQueryParams,
    TaskResponseData,
    TaskToggleEnabled,
    TaskPointResponse,
    TaskRobotBrief,
    PerformanceActionOption,
    PerformanceMusicOption,
    PerformanceMusicUploadResult,
)

logger = logging.getLogger(__name__)

# 表演任务（八段锦）预设动作与背景音乐：动作为平台预置；音乐支持预设与用户上传
_PERFORMANCE_ACTIONS: list[PerformanceActionOption] = [
    PerformanceActionOption(value="baduanjin_1", label="八段锦·第一套（双手托天理三焦）", duration_seconds=240),
    PerformanceActionOption(value="baduanjin_2", label="八段锦·第二套（左右开弓似射雕）", duration_seconds=240),
    PerformanceActionOption(value="baduanjin_3", label="八段锦·第三套（调理脾胃须单举）", duration_seconds=240),
]
_PERFORMANCE_MUSIC: list[PerformanceMusicOption] = [
    PerformanceMusicOption(value="bdj_1", label="八段锦音乐·第一套", duration_seconds=240),
    PerformanceMusicOption(value="bdj_2", label="八段锦音乐·第二套", duration_seconds=240),
    PerformanceMusicOption(value="bdj_3", label="八段锦音乐·第三套", duration_seconds=240),
    # bdj_full_12min 已从预设目录下线（2026-10-21）；VALID_PERFORMANCE_MUSIC 仍保留该校验值，
    # 以兼容引用了它的历史任务
]


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


@task_router.get(
    "/performance/actions",
    response_model=ResponseModel[list[PerformanceActionOption]],
)
async def list_performance_actions():
    """获取表演动作预设列表（八段锦，最多 3 套，可重复）"""
    return response_base.success(data=_PERFORMANCE_ACTIONS)


@task_router.get(
    "/performance/music",
    response_model=ResponseModel[list[PerformanceMusicOption]],
)
async def list_performance_music(
    db: AsyncSession = Depends(get_session),
    user: SysUser = Depends(current_user),
):
    """获取背景音乐列表：平台预设 + 当前用户上传（仅自己可见，含实际时长）

    file_id 非空即表示可试听（走 /admin/sys/file/{file_id}/preview）：
    上传音乐为自身文件；预设音乐需在 PRESET_MUSIC_FILE_IDS 配置映射，
    已映射的预设时长展示为音频文件的真实时长。
    """
    preset_durations = await PerformanceMusicService.probe_durations_by_ids(
        db, set(PRESET_MUSIC_FILE_IDS.values())
    )
    options: list[PerformanceMusicOption] = []
    for opt in _PERFORMANCE_MUSIC:
        file_id = PRESET_MUSIC_FILE_IDS.get(opt.value)
        duration = preset_durations.get(file_id) if file_id else None
        options.append(
            opt.model_copy(
                update={
                    "file_id": file_id,
                    "duration_seconds": int(round(duration)) if duration is not None else opt.duration_seconds,
                }
            )
        )
    uploads = await PerformanceMusicService.list_user_music_with_duration(db, user.id)
    options.extend(
        PerformanceMusicOption(
            value=f"{UPLOAD_MUSIC_PREFIX}{item.id}",
            label=item.original_name,
            duration_seconds=int(round(duration)) if duration is not None else None,
            file_id=item.id,
        )
        for item, duration in uploads
    )
    return response_base.success(data=options)


@task_router.post(
    "/performance/music/upload",
    response_model=ResponseModel[PerformanceMusicUploadResult],
    summary="上传表演背景音乐",
)
async def upload_performance_music(
    file: UploadFile = File(..., description="音频文件（mp3/wav，≤20MB，超过4分钟自动截取前4分钟）"),
    db: AsyncSession = Depends(get_session),
    user: SysUser = Depends(current_user),
):
    """上传表演背景音乐（仅自己可见）

    - 仅支持 mp3/wav，单文件不超过 20MB；
    - 时长超过 4 分钟的音频自动截取前 4 分钟，响应 truncated=true。
    """
    file_data = await file.read()
    sys_file, duration, truncated = await PerformanceMusicService.upload_music(
        db=db,
        file_data=file_data,
        original_name=file.filename or "unknown",
        mime_type=file.content_type or "application/octet-stream",
        user_id=user.id,
    )
    await db.commit()
    result = PerformanceMusicUploadResult(
        value=f"{UPLOAD_MUSIC_PREFIX}{sys_file.id}",
        label=sys_file.original_name,
        duration_seconds=int(duration),
        file_id=sys_file.id,
        truncated=truncated,
    )
    msg = "上传成功，音频超过 4 分钟已自动截取前 4 分钟" if truncated else "上传成功"
    return response_base.success(data=result, msg=msg)


@task_router.delete(
    "/performance/music/{file_id}",
    response_model=ResponseModel,
    summary="删除上传的表演背景音乐",
)
async def delete_performance_music(
    file_id: int = Path(..., description="文件ID（sys_file）"),
    db: AsyncSession = Depends(get_session),
    user: SysUser = Depends(current_user),
):
    """删除自己上传的表演背景音乐；被表演任务引用的不允许删除"""
    await PerformanceMusicService.delete_music(db, file_id, user.id)
    await db.commit()
    return response_base.success(msg="删除成功")
