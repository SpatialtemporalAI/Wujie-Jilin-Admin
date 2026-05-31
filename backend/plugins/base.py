#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from fastapi import FastAPI


class PluginBase(ABC):
    """插件基类，所有插件必须继承此类"""

    name: str = ""
    version: str = "1.0.0"
    description: str = ""

    # ---- Alembic 模型注册 ----

    def register_alembic_models(self) -> None:
        """
        在 alembic autogenerate 前调用。
        将插件的新模型注册到 Base.metadata，并修改已有模型的 schema（如加列）。
        不需要 import 基础模型——env.py 已导入。
        """
        pass

    # ---- 生命周期：安装 / 卸载 ----

    async def on_install(self) -> None:
        """
        插件安装时调用（仅执行一次）。
        在 alembic 迁移完成后执行，用于种子数据写入、菜单初始化等。
        """
        pass

    async def on_uninstall(self) -> None:
        """
        插件卸载时调用（仅执行一次）。
        在 alembic 生成删除迁移前执行，用于清理种子数据。
        """
        pass

    # ---- 生命周期：激活 / 停用 ----

    @abstractmethod
    def on_activate(self, app: FastAPI) -> None:
        """每次应用启动且插件已安装时调用，用于初始化运行时状态"""
        pass

    # ---- 注册钩子 ----

    @abstractmethod
    def register_routes(self, app: FastAPI) -> None:
        """注册插件路由"""
        pass

    @abstractmethod
    def register_middleware(self, app: FastAPI) -> None:
        """注册插件中间件"""
        pass

    @abstractmethod
    def register_database_plugins(self) -> None:
        """注册数据库事件监听（如租户过滤）"""
        pass
