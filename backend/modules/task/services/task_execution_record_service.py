#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
任务执行记录服务（独立版本）
"""
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, Select
from typing import List, Optional

from database.models.business.task import Task
from database.models.business.task_execution_record import TaskExecutionRecord
from database.utils.timezone import timezone
from core.exception.errors import NotFoundError, ConflictError
from modules.grpc.task_client import TaskConfigClient
from modules.task.schemas.task_execution_record import (
    TaskExecutionRecordQueryParams,
)

logger = logging.getLogger(__name__)


class TaskExecutionRecordService:
    """任务执行记录服务类"""

    @staticmethod
    async def start_execution(
        db: AsyncSession,
        task_id: int,
        robot_ids: List[int],
    ) -> dict:
        """启动任务：仅下发 gRPC run_now 通知到机器人 agent，不再写 task_execution_record。

        定时调度已移交外部程序负责，本服务的"启动"只做实时信号下发；
        执行记录由机器人 agent 侧维护，平台不再落库。

        Returns:
            {"total": N, "success_count": N, "failed_count": N}
            推送失败仅日志，不抛异常（与 broadcast_task_changed 约定一致）。
        """
        # 任务存在性校验（保持原 404 行为）
        task_result = await db.execute(
            select(Task).where(
                Task.id == task_id,
                Task.deleted_at.is_(None),
            )
        )
        if task_result.scalar_one_or_none() is None:
            raise NotFoundError(msg=f"任务 {task_id} 不存在")

        return await TaskConfigClient.broadcast_task_changed(
            task_id=task_id,
            operation="run_now",
            robot_ids=list(robot_ids),
        )

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
            if record.status not in ("running", "pending"):
                raise ConflictError(msg="只有运行中或等待中的任务才能暂停")
            record.status = "paused"
            await db.commit()
            await db.refresh(record)

            if record.robot_id is not None:
                try:
                    await TaskConfigClient.broadcast_task_changed(
                        task_id=record.task_id,
                        operation="pause",
                        robot_ids=[record.robot_id],
                    )
                except Exception as exc:  # noqa: BLE001 - 推送容错
                    logger.warning(
                        "grpc task broadcast pause failed task_id=%s robot_id=%s err=%s",
                        record.task_id,
                        record.robot_id,
                        exc,
                    )

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
            record.status = "pending"
            await db.commit()
            await db.refresh(record)

            if record.robot_id is not None:
                try:
                    await TaskConfigClient.broadcast_task_changed(
                        task_id=record.task_id,
                        operation="resume",
                        robot_ids=[record.robot_id],
                    )
                except Exception as exc:  # noqa: BLE001 - 推送容错
                    logger.warning(
                        "grpc task broadcast resume failed task_id=%s robot_id=%s err=%s",
                        record.task_id,
                        record.robot_id,
                        exc,
                    )

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
            if record.status not in ("running", "paused", "pending"):
                raise ConflictError(msg="只有运行中、已暂停或等待中的任务才能停止")
            record.status = "cancelled"
            record.finish_time = timezone.now()
            await db.commit()
            await db.refresh(record)

            if record.robot_id is not None:
                try:
                    await TaskConfigClient.broadcast_task_changed(
                        task_id=record.task_id,
                        operation="stop",
                        robot_ids=[record.robot_id],
                    )
                except Exception as exc:  # noqa: BLE001 - 推送容错
                    logger.warning(
                        "grpc task broadcast stop failed task_id=%s robot_id=%s err=%s",
                        record.task_id,
                        record.robot_id,
                        exc,
                    )

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

            # 批量暂停后下发 pause 到该任务关联的所有 robot
            try:
                await TaskConfigClient.broadcast_task_changed(
                    task_id=task_id,
                    operation="pause",
                    robot_ids=[r.robot_id for r in records if r.robot_id is not None],
                )
            except Exception as exc:  # noqa: BLE001 - 推送容错
                logger.warning(
                    "grpc task broadcast pause failed task_id=%s err=%s",
                    task_id,
                    exc,
                )

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
            TaskExecutionRecord.status.in_(["pending", "running", "paused"]),
            TaskExecutionRecord.deleted_at.is_(None),
        )
        if query_params:
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

        # 历史任务按结束时间倒序，空值(未记录结束时间)排最后
        return base_query.order_by(TaskExecutionRecord.finish_time.desc().nulls_last())

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
