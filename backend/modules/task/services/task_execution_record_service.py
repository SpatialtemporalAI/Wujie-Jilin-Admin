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
from modules.robot.services.robot_service import RobotService
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
        """启动任务：按机器人逐个下发 gRPC run_now，无需所有机器人都在线。

        - 播报任务关联多台机器人时，无需全部在线：仅向在线机器人下发，离线机器人跳过。
        - 巡逻任务仍校验执行机器人与任务在同一场景地图（配置正确性硬校验）。
        - 逐台调用 gRPC，聚合成功/失败的 robot_id；若无一成功，抛 ConflictError。
        - 定时调度已移交外部程序负责，本服务只做实时信号下发，不写执行记录。

        Returns:
            {"total": N, "success_count": N, "failed_count": N,
             "success_robot_ids": [...], "failed_robot_ids": [...]}
            failed 含离线与 gRPC 下发失败的机器人。
        """
        # 任务存在性校验（保持原 404 行为）
        task_result = await db.execute(
            select(Task).where(
                Task.id == task_id,
                Task.deleted_at.is_(None),
            )
        )
        task = task_result.scalar_one_or_none()
        if task is None:
            raise NotFoundError(msg=f"任务 {task_id} 不存在")

        # 巡逻任务校验：执行机器人必须与任务在同一场景地图
        if task.task_type == "patrol":
            await RobotService.ensure_robots_match_map(
                db, list(robot_ids), task.map_id
            )

        # 尽力下发：仅向在线机器人发起 gRPC，离线机器人跳过（避免无谓的超时等待）
        online_robot_ids = await RobotService.get_online_robot_ids(
            db, list(robot_ids)
        )
        online_id_set = set(online_robot_ids)
        offline_robot_ids = [rid for rid in robot_ids if rid not in online_id_set]

        result = await TaskConfigClient.broadcast_task_changed(
            task_id=task_id,
            operation="run_now",
            robot_ids=online_robot_ids,
        )

        success_robot_ids: List[int] = list(result.get("success_robot_ids", []))
        # 失败 = gRPC 下发失败 + 离线未下发
        failed_robot_ids: List[int] = list(
            result.get("failed_robot_ids", [])
        ) + offline_robot_ids

        # 无一成功 → 提示任务执行失败
        if not success_robot_ids:
            if online_robot_ids:
                raise ConflictError(msg="任务执行失败：未能成功启动任何机器人")
            raise ConflictError(msg="任务执行失败：关联的机器人均不在线")

        return {
            "total": len(robot_ids),
            "success_count": len(success_robot_ids),
            "failed_count": len(failed_robot_ids),
            "success_robot_ids": success_robot_ids,
            "failed_robot_ids": failed_robot_ids,
        }

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
