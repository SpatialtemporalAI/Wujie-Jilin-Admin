#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from core.exception.errors import NotFoundError, ConflictError
from database.models.sys.scheduled_task import SysScheduledTask
from modules.scheduler.schemas.scheduled_task import (
    ScheduledTaskCreate,
    ScheduledTaskUpdate,
    ScheduledTaskQueryParams,
)
from modules.scheduler.core.registry import get_registered_tasks
from modules.scheduler.core.scheduler import SchedulerManager


class SchedulerService:
    """定时任务管理服务"""

    @staticmethod
    def build_task_query(query_params: ScheduledTaskQueryParams):
        """构建定时任务查询"""
        conditions = []
        if query_params.name:
            conditions.append(SysScheduledTask.name.like(f"%{query_params.name}%"))
        if query_params.task_key:
            conditions.append(
                SysScheduledTask.task_key.like(f"%{query_params.task_key}%")
            )
        if query_params.status is not None:
            conditions.append(SysScheduledTask.status == query_params.status)
        if query_params.trigger_type:
            conditions.append(
                SysScheduledTask.trigger_type == query_params.trigger_type
            )

        stmt = select(SysScheduledTask).where(SysScheduledTask.deleted_at.is_(None))
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(SysScheduledTask.created_at.desc())
        return stmt

    @staticmethod
    async def get_task(db: AsyncSession, task_id: int) -> SysScheduledTask:
        """获取单个任务"""
        stmt = select(SysScheduledTask).where(
            SysScheduledTask.id == task_id,
            SysScheduledTask.deleted_at.is_(None),
        )
        result = await db.execute(stmt)
        task = result.scalar_one_or_none()
        if not task:
            raise NotFoundError(msg=f"定时任务 {task_id} 不存在")
        return task

    @staticmethod
    async def get_task_by_key(
        db: AsyncSession, task_key: str
    ) -> SysScheduledTask | None:
        """按 task_key 获取任务"""
        stmt = select(SysScheduledTask).where(
            SysScheduledTask.task_key == task_key,
            SysScheduledTask.deleted_at.is_(None),
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_task(
        db: AsyncSession, task_create: ScheduledTaskCreate
    ) -> SysScheduledTask:
        """创建定时任务"""
        existing = await SchedulerService.get_task_by_key(db, task_create.task_key)
        if existing:
            raise ConflictError(msg=f"任务标识 '{task_create.task_key}' 已存在")

        task = SysScheduledTask(
            name=task_create.name,
            task_key=task_create.task_key,
            description=task_create.description,
            cron_expression=task_create.cron_expression,
            trigger_type=task_create.trigger_type,
            trigger_params=task_create.trigger_params,
            status=True,
            timeout=task_create.timeout,
            max_retries=task_create.max_retries,
            concurrent_policy=task_create.concurrent_policy,
        )
        db.add(task)
        await db.flush()

        await SchedulerService._sync_job(task, db)
        return task

    @staticmethod
    async def update_task(
        db: AsyncSession, task_id: int, task_update: ScheduledTaskUpdate
    ) -> SysScheduledTask:
        """更新定时任务"""
        task = await SchedulerService.get_task(db, task_id)

        update_data = task_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)

        await db.flush()
        await SchedulerService._sync_job(task, db)
        return task

    @staticmethod
    async def delete_task(db: AsyncSession, task_id: int) -> None:
        """删除定时任务"""
        task = await SchedulerService.get_task(db, task_id)
        if task.is_system:
            raise ConflictError(msg="系统任务不可删除")

        from database.utils.timezone import timezone

        task.deleted_at = timezone.now()
        await db.flush()

        manager = SchedulerManager.get_instance()
        manager.remove_task_job(task_id)

    @staticmethod
    async def toggle_status(
        db: AsyncSession, task_id: int, status: bool
    ) -> SysScheduledTask:
        """启用/禁用任务"""
        task = await SchedulerService.get_task(db, task_id)
        task.status = status
        await db.flush()

        await SchedulerService._sync_job(task, db)
        return task

    @staticmethod
    async def manual_trigger(db: AsyncSession, task_id: int):
        """手动触发任务"""
        task = await SchedulerService.get_task(db, task_id)
        manager = SchedulerManager.get_instance()
        await manager.run_task_now(task, db, triggered_by="manual")
        return task

    @staticmethod
    def preview_cron(cron_expression: str, count: int = 5) -> list[str]:
        """预览 cron 表达式"""
        return SchedulerManager.preview_cron(cron_expression, count)

    @staticmethod
    async def sync_registry_to_db(db: AsyncSession) -> list[str]:
        """将装饰器注册的任务同步到数据库"""
        registry = get_registered_tasks()
        synced = []

        for task_key, definition in registry.items():
            existing = await SchedulerService.get_task_by_key(db, task_key)
            if existing:
                existing.name = definition.name
                existing.description = definition.description
                existing.cron_expression = definition.cron_expression
                existing.trigger_type = definition.trigger_type
                existing.module = definition.module
                existing.function_path = definition.function_path
                existing.timeout = definition.timeout
                existing.max_retries = definition.max_retries
                existing.concurrent_policy = definition.concurrent_policy
                existing.is_system = definition.is_system
                if definition.trigger_params:
                    import json

                    existing.trigger_params = json.dumps(definition.trigger_params)
                synced.append(task_key)
            else:
                import json

                task = SysScheduledTask(
                    name=definition.name,
                    task_key=definition.task_key,
                    description=definition.description,
                    cron_expression=definition.cron_expression,
                    trigger_type=definition.trigger_type,
                    trigger_params=(
                        json.dumps(definition.trigger_params)
                        if definition.trigger_params
                        else None
                    ),
                    status=True,
                    module=definition.module,
                    function_path=definition.function_path,
                    is_system=definition.is_system,
                    timeout=definition.timeout,
                    max_retries=definition.max_retries,
                    concurrent_policy=definition.concurrent_policy,
                )
                db.add(task)
                synced.append(task_key)

        await db.flush()
        return synced

    @staticmethod
    async def _sync_job(task: SysScheduledTask, db: AsyncSession):
        """同步单个任务到调度器"""
        manager = SchedulerManager.get_instance()
        if manager.running:
            await manager.add_task_job(task)
            await db.flush()
        else:
            # 调度器未运行时，用 trigger 计算下次执行时间
            if not task.status:
                task.next_run_at = None
            elif task.trigger_type == "cron" and task.cron_expression:
                next_str = manager.preview_cron(task.cron_expression, count=1)
                if next_str:
                    from datetime import datetime

                    task.next_run_at = datetime.fromisoformat(next_str[0])
                else:
                    task.next_run_at = None
            else:
                task.next_run_at = None
            await db.flush()
