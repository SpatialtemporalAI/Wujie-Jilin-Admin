#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
任务管理服务
"""
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, Select, func
from sqlalchemy.orm import noload, selectinload
from typing import List

from database.models.business.task import Task, task_robot_association
from database.models.business.task_point import TaskPoint
from database.models.business.robot import Robot
from core.exception.errors import NotFoundError
from modules.grpc.task_client import TaskConfigClient
from modules.task.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskQueryParams,
)

logger = logging.getLogger(__name__)


class TaskService:
    """任务管理服务类"""

    @staticmethod
    def build_query(query_params: TaskQueryParams) -> Select:
        """构建任务查询"""
        base_query = select(Task).options(
            noload(Task.points),
            noload(Task.robots),
        )

        conditions = [Task.deleted_at.is_(None)]
        if query_params.name:
            conditions.append(Task.name.contains(query_params.name))
        if query_params.task_type:
            conditions.append(Task.task_type == query_params.task_type)
        if query_params.enabled is not None:
            conditions.append(Task.enabled == query_params.enabled)
        if query_params.map_id is not None:
            conditions.append(Task.map_id == query_params.map_id)
        if query_params.robot_id is not None:
            base_query = base_query.join(
                task_robot_association,
                Task.id == task_robot_association.c.task_id,
            ).join(Robot, Robot.id == task_robot_association.c.robot_id)
            conditions.append(Robot.id == query_params.robot_id)
            conditions.append(Robot.deleted_at.is_(None))
            base_query = base_query.distinct()

        if conditions:
            base_query = base_query.where(and_(*conditions))

        base_query = base_query.order_by(Task.id.desc())
        return base_query

    @staticmethod
    async def get(db: AsyncSession, task_id: int) -> Task:
        """获取单个任务"""
        result = await db.execute(
            select(Task)
            .where(Task.id == task_id)
            .where(Task.deleted_at.is_(None))
        )
        task_obj = result.scalar_one_or_none()
        if not task_obj:
            raise NotFoundError(msg=f"任务 {task_id} 不存在")
        return task_obj

    @staticmethod
    async def get_with_relations(db: AsyncSession, task_id: int) -> Task:
        """获取任务（含点位和机器人）"""
        result = await db.execute(
            select(Task)
            .options(
                selectinload(Task.points),
                selectinload(Task.robots),
            )
            .where(Task.id == task_id)
            .where(Task.deleted_at.is_(None))
        )
        task_obj = result.unique().scalar_one_or_none()
        if not task_obj:
            raise NotFoundError(msg=f"任务 {task_id} 不存在")
        return task_obj

    @staticmethod
    async def create(db: AsyncSession, task_in: TaskCreate) -> Task:
        """创建任务"""
        try:
            # 验证机器人存在
            robot_result = await db.execute(
                select(Robot).where(
                    Robot.id.in_(task_in.robot_ids),
                    Robot.deleted_at.is_(None),
                )
            )
            robots = robot_result.scalars().all()
            if len(robots) != len(task_in.robot_ids):
                raise NotFoundError(msg="部分机器人不存在")

            # 创建任务主记录
            task_obj = Task(
                name=task_in.name,
                map_id=task_in.map_id,
                task_type=task_in.task_type,
                broadcast_text=task_in.broadcast_text,
                broadcast_count=task_in.broadcast_count,
                schedule_enabled=task_in.schedule_enabled,
                schedule_date=task_in.schedule_date,
                schedule_start_time=task_in.schedule_start_time,
                schedule_repeat_cycle=task_in.schedule_repeat_cycle,
            )
            db.add(task_obj)
            await db.flush()

            # 创建巡逻点位
            if task_in.points:
                for pt in task_in.points:
                    point_obj = TaskPoint(
                        task_id=task_obj.id,
                        sort_order=pt.sort_order,
                        point_name=pt.point_name,
                        annotation_id=pt.annotation_id,
                        actions=[a.model_dump() for a in pt.actions],
                    )
                    db.add(point_obj)

            # 创建机器人关联
            for robot_id in task_in.robot_ids:
                await db.execute(
                    task_robot_association.insert().values(
                        task_id=task_obj.id, robot_id=robot_id
                    )
                )

            await db.commit()
            await db.refresh(task_obj)

            # DB 落库后下发 gRPC 通知到机器人 agent；失败仅日志，不阻塞业务
            try:
                await TaskConfigClient.broadcast_task_changed(
                    task_id=task_obj.id,
                    operation="create",
                    robot_ids=list(task_in.robot_ids),
                )
            except Exception as exc:  # noqa: BLE001 - 推送容错
                logger.warning(
                    "grpc task broadcast create failed task_id=%s err=%s",
                    task_obj.id,
                    exc,
                )

            return task_obj

        except NotFoundError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error("创建任务失败: %s", str(e), exc_info=True)
            raise

    @staticmethod
    async def update(db: AsyncSession, task_id: int, task_in: TaskUpdate) -> Task:
        """更新任务"""
        try:
            task_obj = await TaskService.get(db, task_id)

            # 更新基础字段
            update_data = task_in.model_dump(exclude_unset=True, exclude={"points", "robot_ids"})
            for field, value in update_data.items():
                setattr(task_obj, field, value)

            # 更新巡逻点位（全量替换）
            if task_in.points is not None:
                await db.execute(
                    TaskPoint.__table__.delete().where(TaskPoint.task_id == task_id)
                )
                for pt in task_in.points:
                    point_obj = TaskPoint(
                        task_id=task_id,
                        sort_order=pt.sort_order,
                        point_name=pt.point_name,
                        annotation_id=pt.annotation_id,
                        actions=[a.model_dump() for a in pt.actions],
                    )
                    db.add(point_obj)

            # 更新机器人关联（全量替换）
            if task_in.robot_ids is not None:
                # 验证机器人存在
                robot_result = await db.execute(
                    select(Robot).where(
                        Robot.id.in_(task_in.robot_ids),
                        Robot.deleted_at.is_(None),
                    )
                )
                robots = robot_result.scalars().all()
                if len(robots) != len(task_in.robot_ids):
                    raise NotFoundError(msg="部分机器人不存在")

                await db.execute(
                    task_robot_association.delete().where(
                        task_robot_association.c.task_id == task_id
                    )
                )
                for robot_id in task_in.robot_ids:
                    await db.execute(
                        task_robot_association.insert().values(
                            task_id=task_id, robot_id=robot_id
                        )
                    )

            await db.commit()
            await db.refresh(task_obj)

            # DB 落库后下发 gRPC 通知到机器人 agent；失败仅日志，不阻塞业务
            # robot_ids 可能未在更新请求中提供，需读取 DB 当前关联值
            if task_in.robot_ids is not None:
                final_robot_ids = list(task_in.robot_ids)
            else:
                assoc_result = await db.execute(
                    select(task_robot_association.c.robot_id).where(
                        task_robot_association.c.task_id == task_id
                    )
                )
                final_robot_ids = [row[0] for row in assoc_result.all()]

            try:
                await TaskConfigClient.broadcast_task_changed(
                    task_id=task_id,
                    operation="edit",
                    robot_ids=final_robot_ids,
                )
            except Exception as exc:  # noqa: BLE001 - 推送容错
                logger.warning(
                    "grpc task broadcast edit failed task_id=%s err=%s",
                    task_id,
                    exc,
                )

            return task_obj

        except NotFoundError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error("更新任务失败: %s", str(e), exc_info=True)
            raise

    @staticmethod
    async def delete_points_by_annotation_ids(db: AsyncSession, annotation_ids: list[int]) -> None:
        if not annotation_ids:
            return

        result = await db.execute(
            select(TaskPoint).where(
                TaskPoint.annotation_id.in_(annotation_ids),
                TaskPoint.deleted_at.is_(None),
            )
        )
        points = result.scalars().all()
        if not points:
            return

        task_ids = {point.task_id for point in points}
        deleting_point_ids = {point.id for point in points}
        for task_id in task_ids:
            task_points_result = await db.execute(
                select(TaskPoint)
                .where(TaskPoint.task_id == task_id, TaskPoint.deleted_at.is_(None))
                .order_by(TaskPoint.sort_order.asc(), TaskPoint.id.asc())
            )
            task_points = task_points_result.scalars().all()
            if all(point.id in deleting_point_ids for point in task_points):
                task_obj = await db.get(Task, task_id)
                if task_obj is not None and task_obj.deleted_at is None:
                    task_obj.soft_delete()
                for point in task_points:
                    await db.delete(point)
                continue

            sort_order = 0
            for point in task_points:
                if point.id in deleting_point_ids:
                    await db.delete(point)
                else:
                    point.sort_order = sort_order
                    sort_order += 1

        await db.flush()

    @staticmethod
    async def count_tasks_by_annotation_ids(
        db: AsyncSession, annotation_ids: list[int]
    ) -> dict[int, int]:
        """统计每个标注关联的有效任务数（按 task_id 去重）。

        仅统计未删除的任务及其未删除的任务点位，用于地图编辑器判断
        删除点位时是否需要弹出"已关联任务"的二次确认。
        返回 {annotation_id: task_count}，未关联任务的标注不在结果中。
        """
        if not annotation_ids:
            return {}

        result = await db.execute(
            select(
                TaskPoint.annotation_id,
                func.count(func.distinct(TaskPoint.task_id)),
            )
            .join(Task, TaskPoint.task_id == Task.id)
            .where(
                TaskPoint.annotation_id.in_(annotation_ids),
                TaskPoint.deleted_at.is_(None),
                Task.deleted_at.is_(None),
            )
            .group_by(TaskPoint.annotation_id)
        )
        return {annotation_id: count for annotation_id, count in result.all()}

    @staticmethod
    async def delete(db: AsyncSession, task_id: int) -> bool:
        """删除任务（软删除）"""
        try:
            task_obj = await TaskService.get(db, task_id)

            # 软删除前先取出当前关联 robot_ids，删除后用于 gRPC 通知
            assoc_result = await db.execute(
                select(task_robot_association.c.robot_id).where(
                    task_robot_association.c.task_id == task_id
                )
            )
            robot_ids = [row[0] for row in assoc_result.all()]

            task_obj.soft_delete()
            await db.commit()

            # DB 落库后下发 gRPC 通知到机器人 agent；失败仅日志，不阻塞业务
            try:
                await TaskConfigClient.broadcast_task_changed(
                    task_id=task_id,
                    operation="delete",
                    robot_ids=robot_ids,
                )
            except Exception as exc:  # noqa: BLE001 - 推送容错
                logger.warning(
                    "grpc task broadcast delete failed task_id=%s err=%s",
                    task_id,
                    exc,
                )

            return True
        except NotFoundError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error("删除任务失败: %s", str(e), exc_info=True)
            raise

    @staticmethod
    async def soft_delete_by_map_id(db: AsyncSession, map_id: int) -> int:
        """软删除某场景地图下的所有任务（不 commit，由调用方控制事务）。
        返回软删除的记录数。"""
        result = await db.execute(
            select(Task).where(
                Task.map_id == map_id,
                Task.deleted_at.is_(None),
            )
        )
        tasks = result.scalars().all()
        for task_obj in tasks:
            task_obj.soft_delete()
        await db.flush()
        return len(tasks)

    @staticmethod
    async def toggle_enabled(db: AsyncSession, task_id: int, enabled: bool) -> Task:
        """切换启用/禁用"""
        try:
            task_obj = await TaskService.get(db, task_id)
            task_obj.enabled = enabled
            await db.commit()
            await db.refresh(task_obj)

            # DB 落库后下发 gRPC 通知到机器人 agent；失败仅日志，不阻塞业务
            assoc_result = await db.execute(
                select(task_robot_association.c.robot_id).where(
                    task_robot_association.c.task_id == task_id
                )
            )
            robot_ids = [row[0] for row in assoc_result.all()]
            operation = "enable" if enabled else "disable"
            try:
                await TaskConfigClient.broadcast_task_changed(
                    task_id=task_id,
                    operation=operation,
                    robot_ids=robot_ids,
                )
            except Exception as exc:  # noqa: BLE001 - 推送容错
                logger.warning(
                    "grpc task broadcast %s failed task_id=%s err=%s",
                    operation,
                    task_id,
                    exc,
                )

            return task_obj
        except NotFoundError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error("切换任务启用状态失败: %s", str(e), exc_info=True)
            raise
