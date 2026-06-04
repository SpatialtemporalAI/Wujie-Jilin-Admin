#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def seed_scheduler_menus(db: AsyncSession) -> None:
    """插入定时任务管理菜单（幂等）"""
    from database.models.sys.menu import SysMenu, MenuType

    result = await db.execute(
        select(SysMenu.id).where(SysMenu.name == "scheduler").limit(1)
    )
    if result.scalar_one_or_none():
        return

    catalog = SysMenu(
        parent_id=None,
        name="scheduler",
        path="/manage/scheduler",
        component="layout.base",
        redirect="/manage/scheduler/list",
        permission=None,
        meta_icon="material-symbols:schedule-outline",
        type=MenuType.CATALOG,
        sort=95,
    )
    db.add(catalog)
    await db.flush()

    task_menu = SysMenu(
        parent_id=catalog.id,
        name="manage_scheduler",
        path="/manage/scheduler/list",
        component="view.manage_scheduler",
        redirect=None,
        permission="sys:scheduler:list",
        meta_icon="material-symbols:task-alt-outline",
        type=MenuType.MENU,
        sort=1,
    )
    db.add(task_menu)
    await db.flush()

    buttons = [
        ("sys:scheduler:add", "新增任务"),
        ("sys:scheduler:edit", "编辑任务"),
        ("sys:scheduler:delete", "删除任务"),
        ("sys:scheduler:detail", "任务详情"),
        ("sys:scheduler:status", "启停任务"),
        ("sys:scheduler:trigger", "手动执行"),
    ]
    for perm, label in buttons:
        db.add(SysMenu(
            parent_id=task_menu.id,
            name=label,
            path="",
            component=None,
            redirect=None,
            permission=perm,
            meta_icon=None,
            type=MenuType.BUTTON,
            sort=0,
        ))

    log_menu = SysMenu(
        parent_id=catalog.id,
        name="manage_scheduler-log",
        path="/manage/scheduler-log",
        component="view.manage_scheduler-log",
        redirect=None,
        permission="sys:scheduler:log:list",
        meta_icon="material-symbols:history",
        type=MenuType.MENU,
        sort=2,
    )
    db.add(log_menu)
    await db.flush()

    log_buttons = [
        ("sys:scheduler:log:detail", "日志详情"),
        ("sys:scheduler:log:delete", "删除日志"),
    ]
    for perm, label in log_buttons:
        db.add(SysMenu(
            parent_id=log_menu.id,
            name=label,
            path="",
            component=None,
            redirect=None,
            permission=perm,
            meta_icon=None,
            type=MenuType.BUTTON,
            sort=0,
        ))

    logger.info("定时任务管理菜单已创建")


async def seed_scheduler(db: AsyncSession) -> None:
    """种子数据：菜单 + 同步装饰器注册的任务"""
    from modules.scheduler.services.scheduler_service import SchedulerService

    await seed_scheduler_menus(db)
    await SchedulerService.sync_registry_to_db(db)
    await db.commit()
