#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

from fastapi import FastAPI
from sqlalchemy import text

from plugins.base import PluginBase
from plugins.scheduler.services.scheduler_service import SchedulerService

logger = logging.getLogger(__name__)


class SchedulerPlugin(PluginBase):
    """定时任务调度插件"""

    name = "scheduler"
    version = "1.0.0"
    description = "定时任务调度插件，支持 Cron 配置、装饰器注册、执行日志记录"

    # ---- Alembic 模型注册 ----

    def register_alembic_models(self) -> None:
        from plugins.scheduler.models.scheduled_task import SysScheduledTask
        from plugins.scheduler.models.task_log import SysScheduledTaskLog

    # ---- 安装 / 卸载 ----

    async def on_install(self) -> None:
        """种子菜单 + 同步装饰器任务"""
        from database.db_manager import get_session

        async for db in get_session():
            await self._seed_menus(db)
            await SchedulerService.sync_registry_to_db(db)
            await db.commit()

    async def on_uninstall(self) -> None:
        """清理种子菜单"""
        from database.db_manager import get_session

        async for db in get_session():
            await db.execute(
                text("DELETE FROM sys_menu WHERE permission LIKE 'sys:scheduler:%'")
            )
            await db.execute(
                text(
                    "DELETE FROM sys_menu WHERE path = '/manage/scheduler' "
                    "OR name = 'manage_scheduler' OR name = 'scheduler'"
                )
            )
            await db.commit()

    # ---- 激活 ----

    def on_activate(self, app: FastAPI) -> None:
        from plugins.scheduler.core.scheduler import SchedulerManager

        # 导入内置任务，触发装饰器注册
        import plugins.scheduler.tasks.builtin  # noqa: F401

        manager = SchedulerManager.get_instance()
        manager.start()
        app.state.scheduler_manager = manager

        logger.info("定时任务调度插件已激活")

    # ---- 注册 ----

    def register_routes(self, app: FastAPI) -> None:
        from plugins.scheduler.router import router

        app.include_router(router)

    def register_middleware(self, app: FastAPI) -> None:
        pass

    def register_database_plugins(self) -> None:
        pass

    # ---- 种子数据 ----

    async def _seed_menus(self, db) -> None:
        """插入定时任务管理菜单"""
        from database.models.sys.menu import SysMenu, MenuType
        from sqlalchemy import select

        # 检查是否已存在
        result = await db.execute(
            select(SysMenu.id).where(SysMenu.name == "scheduler").limit(1)
        )
        if result.scalar_one_or_none():
            return

        # 目录：定时任务
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

        # 菜单：任务列表
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

        # 按钮权限
        buttons = [
            ("sys:scheduler:add", "新增任务"),
            ("sys:scheduler:edit", "编辑任务"),
            ("sys:scheduler:delete", "删除任务"),
            ("sys:scheduler:detail", "任务详情"),
            ("sys:scheduler:status", "启停任务"),
            ("sys:scheduler:trigger", "手动执行"),
        ]
        for perm, label in buttons:
            btn = SysMenu(
                parent_id=task_menu.id,
                name=label,
                path="",
                component=None,
                redirect=None,
                permission=perm,
                meta_icon=None,
                type=MenuType.BUTTON,
                sort=0,
            )
            db.add(btn)

        # 菜单：执行日志
        log_menu = SysMenu(
            parent_id=catalog.id,
            name="scheduler_log",
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
            btn = SysMenu(
                parent_id=log_menu.id,
                name=label,
                path="",
                component=None,
                redirect=None,
                permission=perm,
                meta_icon=None,
                type=MenuType.BUTTON,
                sort=0,
            )
            db.add(btn)
