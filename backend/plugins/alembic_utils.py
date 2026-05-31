#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Alembic 自动化工具

在插件 install/uninstall 时自动生成并执行迁移，无需手动编辑 env.py。

原理：
  1. 在内存中注册插件模型到 Base.metadata
  2. 调用 alembic.command API 生成迁移（autogenerate）
  3. env.py 运行时复用同一 Base.metadata 单例，自动包含插件模型
  4. 执行 upgrade head
"""

import logging
import os

from alembic.config import Config
from alembic.script import ScriptDirectory

logger = logging.getLogger(__name__)


def _get_alembic_config() -> Config:
    """获取 alembic 配置，自动定位 alembic.ini"""
    cfg_path = os.path.join(os.getcwd(), "alembic.ini")
    if not os.path.exists(cfg_path):
        # 尝试 backend/ 子目录
        cfg_path = os.path.join(os.getcwd(), "backend", "alembic.ini")
    if not os.path.exists(cfg_path):
        raise FileNotFoundError("找不到 alembic.ini，请在 backend/ 目录下运行")
    return Config(cfg_path)


def get_current_head() -> str:
    """获取当前 alembic head revision"""
    cfg = _get_alembic_config()
    script = ScriptDirectory.from_config(cfg)
    return script.get_current_head()


def autogenerate_and_upgrade(message: str) -> str:
    """
    自动生成迁移文件并执行 upgrade head。

    调用前必须确保 Base.metadata 已包含插件模型
    （通过 import 模型文件 + 调用 register_alembic_models 实现）。

    Returns:
        新的 revision ID
    """
    from alembic import command

    cfg = _get_alembic_config()

    # 生成迁移
    logger.info("生成 alembic 迁移: %s", message)
    command.revision(cfg, message=message, autogenerate=True)

    # 获取新 head
    script = ScriptDirectory.from_config(cfg)
    new_head = script.get_current_head()

    # 执行升级
    logger.info("执行 alembic upgrade head -> %s", new_head)
    command.upgrade(cfg, "head")

    return new_head


def generate_removal_and_upgrade(plugin_name: str) -> str:
    """
    卸载插件时生成"删除"迁移并执行。

    前提：不导入插件模型，使 Base.metadata 中没有插件表/列，
    autogenerate 会检测到数据库中多出的表和列，自动生成 DROP 语句。

    Returns:
        新的 revision ID
    """
    return autogenerate_and_upgrade(f"remove {plugin_name} plugin")
