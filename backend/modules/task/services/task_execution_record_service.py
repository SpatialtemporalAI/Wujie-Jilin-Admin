#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
任务执行记录服务（独立版本）
"""
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, Select
from sqlalchemy.orm import selectinload
from typing import List, Optional

from database.models.business.task import Task
from database.models.business.task_point import TaskPoint
from database.models.business.task_execution_record import TaskExecutionRecord
from database.models.business.robot import Robot
from database.models.business.scene_map import SceneMap
from database.models.sys.user import SysUser
from database.utils.timezone import timezone
from core.exception.errors import NotFoundError, ConflictError
from modules.task.schemas.task_execution_record import (
    TaskExecutionRecordQueryParams,
    TaskDefinitionSnapshot,
    TaskPointSnapshot,
    TaskActionSnapshot,
    ProgressDetail,
    PointProgressStatus,
)

logger = logging.getLogger(__name__)


class TaskExecutionRecordService:
    """任务执行记录服务类"""

    @staticmethod
    async def _build_task_definition(
        db: AsyncSession, task_id: int
    ) -> tuple[TaskDefinitionSnapshot, Optional[int], List[int]]:
        """读取任务 + 点位，构建 task_definition 快照，返回 (snapshot, scene_id, annotation_ids)"""
        result = await db.execute(
            select(Task)
            .options(selectinload(Task.points))
            .where(Task.id == task_id)
            .where(Task.deleted_at.is_(None))
        )
        task_obj = result.unique().scalar_one_or_none()
        if not task_obj:
            raise NotFoundError(msg=f"任务 {task_id} 不存在")

        annotation_ids: List[int] = []
        point_snapshots: List[TaskPointSnapshot] = []
        for pt in task_obj.points:
            actions = [
                TaskActionSnapshot(
                    action=a.get("action", "wave"),
                    voice_text=a.get("voice_text"),
                )
                for a in (pt.actions or [])
            ]
            point_snapshots.append(
                TaskPointSnapshot(
                    sort_order=pt.sort_order,
                    point_name=pt.point_name,
                    annotation_id=pt.annotation_id,
                    actions=actions,
                )
            )
            if pt.annotation_id is not None:
                annotation_ids.append(pt.annotation_id)

        snapshot = TaskDefinitionSnapshot(
            task_type=task_obj.task_type,
            task_name=task_obj.name,
            points=point_snapshots,
            broadcast_text=task_obj.broadcast_text,
        )
        return snapshot, task_obj.map_id, annotation_ids

    @staticmethod
    def _init_progress(total_points: int) -> ProgressDetail:
        """初始化 progress JSON"""
        return ProgressDetail(
            total_points=total_points,
            completed_points=0,
            current_point_index=0,
            points_status=[
                PointProgressStatus(index=i, status="pending")
                for i in range(total_points)
            ],
        )

    @staticmethod
    async def start_execution(
        db: AsyncSession,
        task_id: int,
        robot_ids: List[int],
        user_id: Optional[int] = None,
        source: str = "manual",
    ) -> List[TaskExecutionRecord]:
        """启动任务执行：为每个机器人创建一条独立执行记录"""
        try:
            task_definition, scene_id, _ = (
                await TaskExecutionRecordService._build_task_definition(db, task_id)
            )

            # 验证机器人
            robot_result = await db.execute(
                select(Robot).where(
                    Robot.id.in_(robot_ids),
                    Robot.deleted_at.is_(None),
                )
            )
            robots = robot_result.scalars().all()
            if len(robots) != len(robot_ids):
                raise NotFoundError(msg="部分机器人不存在")

            total_points = len(task_definition.points)
            created: List[TaskExecutionRecord] = []
            now = timezone.now()

            for robot_id in robot_ids:
                record = TaskExecutionRecord(
                    task_id=task_id,
                    robot_id=robot_id,
                    scene_id=scene_id,
                    user_id=user_id,
                    task_definition=task_definition.model_dump(mode="json"),
                    progress=TaskExecutionRecordService._init_progress(
                        total_points
                    ).model_dump(mode="json"),
                    progress_per=0,
                    status="running",
                    source=source,
                    start_time=now,
                )
                db.add(record)
                created.append(record)

            await db.commit()
            for rec in created:
                await db.refresh(rec)
            return created

        except (NotFoundError, ConflictError):
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error("启动任务执行失败: %s", str(e), exc_info=True)
            raise

    @staticmethod
    async def _get_record(db: AsyncSession, record_id: int) -> TaskExecutionRecord:
        result = await db.execute(
            select(TaskExecutionRecord)
            .where(TaskExecutionRecord.id == record_id)
            .where(TaskExecutionRecord.deleted_at.is_(None))
        )
        record = result.scalar_one_or_none()
        if not record:
            raise NotFoundError(msg=f"执行记录 {record_id} 不存在")
        return record

    @staticmethod
    async def pause_execution(db: AsyncSession, record_id: int) -> TaskExecutionRecord:
        try:
            record = await TaskExecutionRecordService._get_record(db, record_id)
            if record.status != "running":
                raise ConflictError(msg="只有运行中的任务才能暂停")
            record.status = "paused"
            await db.commit()
            await db.refresh(record)
            return record
        except (NotFoundError, ConflictError):
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error("暂停任务执行失败: %s", str(e), exc_info=True)
            raise

    @staticmethod
    async def resume_execution(db: AsyncSession, record_id: int) -> TaskExecutionRecord:
        try:
            record = await TaskExecutionRecordService._get_record(db, record_id)
            if record.status != "paused":
                raise ConflictError(msg="只有已暂停的任务才能恢复")
            record.status = "running"
            await db.commit()
            await db.refresh(record)
            return record
        except (NotFoundError, ConflictError):
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error("恢复任务执行失败: %s", str(e), exc_info=True)
            raise

    @staticmethod
    async def stop_execution(db: AsyncSession, record_id: int) -> TaskExecutionRecord:
        try:
            record = await TaskExecutionRecordService._get_record(db, record_id)
            if record.status not in ("running", "paused"):
                raise ConflictError(msg="只有运行中或已暂停的任务才能停止")
            record.status = "cancelled"
            record.finish_time = timezone.now()
            await db.commit()
            await db.refresh(record)
            return record
        except (NotFoundError, ConflictError):
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error("停止任务执行失败: %s", str(e), exc_info=True)
            raise

    @staticmethod
    async def pause_executions_by_task(db: AsyncSession, task_id: int) -> int:
        """按任务 ID 批量暂停该任务下所有 running/pending 的执行记录，返回暂停条数"""
        try:
            result = await db.execute(
                select(TaskExecutionRecord).where(
                    TaskExecutionRecord.task_id == task_id,
                    TaskExecutionRecord.status.in_(["running", "pending"]),
                    TaskExecutionRecord.deleted_at.is_(None),
                )
            )
            records = result.scalars().all()
            if not records:
                return 0
            now = timezone.now()
            for record in records:
                record.status = "paused"
            await db.commit()
            return len(records)
        except Exception as e:
            await db.rollback()
            logger.error("按任务暂停执行失败: %s", str(e), exc_info=True)
            raise

    @staticmethod
    def build_active_query(
        query_params: Optional[TaskExecutionRecordQueryParams] = None,
    ) -> Select:
        base_query = select(TaskExecutionRecord).where(
            TaskExecutionRecord.status.in_(["running", "paused"]),
            TaskExecutionRecord.deleted_at.is_(None),
        )
        if query_params:
            conditions = []
            if query_params.task_id is not None:
                conditions.append(TaskExecutionRecord.task_id == query_params.task_id)
            if query_params.robot_id is not None:
                conditions.append(TaskExecutionRecord.robot_id == query_params.robot_id)
            if query_params.scene_id is not None:
                conditions.append(TaskExecutionRecord.scene_id == query_params.scene_id)
            if query_params.user_id is not None:
                conditions.append(TaskExecutionRecord.user_id == query_params.user_id)
            if query_params.source:
                conditions.append(TaskExecutionRecord.source == query_params.source)
            if conditions:
                base_query = base_query.where(and_(*conditions))
        return base_query.order_by(TaskExecutionRecord.id.desc())

    @staticmethod
    def build_history_query(
        query_params: TaskExecutionRecordQueryParams,
    ) -> Select:
        base_query = select(TaskExecutionRecord).where(
            TaskExecutionRecord.status.in_(["completed", "failed", "cancelled"]),
            TaskExecutionRecord.deleted_at.is_(None),
        )

        conditions = []
        if query_params.status:
            conditions.append(TaskExecutionRecord.status == query_params.status)
        if query_params.task_id is not None:
            conditions.append(TaskExecutionRecord.task_id == query_params.task_id)
        if query_params.robot_id is not None:
            conditions.append(TaskExecutionRecord.robot_id == query_params.robot_id)
        if query_params.scene_id is not None:
            conditions.append(TaskExecutionRecord.scene_id == query_params.scene_id)
        if query_params.user_id is not None:
            conditions.append(TaskExecutionRecord.user_id == query_params.user_id)
        if query_params.source:
            conditions.append(TaskExecutionRecord.source == query_params.source)

        if conditions:
            base_query = base_query.where(and_(*conditions))

        return base_query.order_by(TaskExecutionRecord.id.desc())

    @staticmethod
    async def get_execution_detail(
        db: AsyncSession, record_id: int
    ) -> TaskExecutionRecord:
        """获取执行详情（含完整 task_definition 和 progress）"""
        result = await db.execute(
            select(TaskExecutionRecord)
            .where(TaskExecutionRecord.id == record_id)
            .where(TaskExecutionRecord.deleted_at.is_(None))
        )
        record = result.scalar_one_or_none()
        if not record:
            raise NotFoundError(msg=f"执行记录 {record_id} 不存在")
        return record
