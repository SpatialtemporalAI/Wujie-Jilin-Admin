#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import importlib
import json
import logging
import os
import re
from typing import Dict, List, Optional

from fastapi import FastAPI
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from .base import PluginBase

logger = logging.getLogger(__name__)

_plugin_registry: Dict[str, PluginBase] = {}

PLUGIN_MODULES = {
    "multi_tenant": "plugins.multi_tenant.plugin:MultiTenantPlugin",
    "scheduler": "plugins.scheduler.plugin:SchedulerPlugin",
}


def _load_plugin_class(plugin_name: str) -> PluginBase:
    """根据名称实例化插件类"""
    if plugin_name not in PLUGIN_MODULES:
        raise ValueError(f"Unknown plugin: {plugin_name}")
    module_path, class_name = PLUGIN_MODULES[plugin_name].rsplit(":", 1)
    module = importlib.import_module(module_path)
    plugin_cls = getattr(module, class_name)
    return plugin_cls()


def load_plugins(app: FastAPI, enabled_plugins: list[str]) -> None:
    """同步加载并激活插件"""
    for plugin_name in enabled_plugins:
        plugin_name = plugin_name.strip()
        try:
            plugin = _load_plugin_class(plugin_name)
            plugin.register_database_plugins()
            plugin.register_middleware(app)
            plugin.register_routes(app)
            plugin.on_activate(app)
            _plugin_registry[plugin_name] = plugin
            logger.info("Plugin loaded: %s v%s", plugin.name, plugin.version)
        except Exception as e:
            logger.error("Failed to load plugin %s: %s", plugin_name, e)
            raise


def get_plugin(name: str) -> Optional[PluginBase]:
    return _plugin_registry.get(name)


def is_plugin_active(name: str) -> bool:
    return name in _plugin_registry


# ---------------------------------------------------------------------------
# 安装 / 卸载 / 状态查询
# ---------------------------------------------------------------------------


def _get_env_files() -> List[str]:
    """返回需要更新 PLUGINS__ENABLED 的 .env 文件绝对路径列表"""
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_dir = os.path.dirname(backend_dir)
    candidates = [
        os.path.join(backend_dir, ".env"),
        os.path.join(backend_dir, ".env.dev"),
        os.path.join(project_dir, "frontend", ".env"),
    ]
    return [f for f in candidates if os.path.isfile(f)]


def _update_plugins_env(plugin_name: str, add: bool = True) -> None:
    """
    在所有 .env 文件中更新 PLUGINS__ENABLED 列表。

    add=True  → 添加 plugin_name（若不存在）
    add=False → 移除 plugin_name（若存在）
    """
    pattern = re.compile(r"^(PLUGINS__ENABLED\s*=\s*)(.*)$", re.MULTILINE)

    for env_file in _get_env_files():
        with open(env_file, "r", encoding="utf-8") as f:
            content = f.read()

        match = pattern.search(content)
        if not match:
            continue

        raw_value = match.group(2).strip()
        try:
            plugins = json.loads(raw_value)
        except (json.JSONDecodeError, TypeError):
            plugins = []

        if not isinstance(plugins, list):
            plugins = []

        changed = False
        if add and plugin_name not in plugins:
            plugins.append(plugin_name)
            changed = True
        elif not add and plugin_name in plugins:
            plugins.remove(plugin_name)
            changed = True

        if changed:
            new_value = json.dumps(plugins, ensure_ascii=False)
            new_line = f"PLUGINS__ENABLED={new_value}"
            content = content[: match.start()] + new_line + content[match.end() :]
            with open(env_file, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info("Updated PLUGINS__ENABLED in %s: %s", env_file, new_value)


async def _ensure_registry_exists(db: AsyncSession) -> None:
    """确保 plugin_registry 表存在（幂等）"""
    await db.execute(text("""
        CREATE TABLE IF NOT EXISTS plugin_registry (
            id BIGINT PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            version VARCHAR(50) NOT NULL,
            is_installed BOOLEAN DEFAULT TRUE,
            installed_at TIMESTAMP WITH TIME ZONE,
            deleted_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE,
            updated_at TIMESTAMP WITH TIME ZONE
        )
    """))
    await db.commit()


async def install_plugin(plugin_name: str) -> None:
    """
    安装插件（全自动）：
    1. register_alembic_models() — 注册插件模型到 Base.metadata
    2. alembic autogenerate + upgrade — 建表、加列
    3. 写 plugin_registry 记录
    4. on_install() — 种子数据
    """
    if plugin_name not in PLUGIN_MODULES:
        raise ValueError(f"Unknown plugin: {plugin_name}")

    from plugins.alembic_utils import get_current_head, autogenerate_and_upgrade
    from database.db_manager import init_pool, get_session

    print(f"\n正在安装插件 '{plugin_name}'...")

    plugin = _load_plugin_class(plugin_name)

    # 1. 注册模型（在 alembic 之前，让 Base.metadata 包含插件模型）
    print("  注册插件模型到 Base.metadata...")
    plugin.register_alembic_models()

    # 2. 自动生成迁移 + 执行
    pre_revision = get_current_head()
    print(f"  当前 alembic head: {pre_revision}")
    print("  生成并执行 alembic 迁移...")
    new_head = autogenerate_and_upgrade(f"install {plugin_name} plugin")
    print(f"  迁移完成: {pre_revision} -> {new_head}")

    # 3. 写 registry 记录（表已存在）
    await init_pool()
    async for db in get_session():
        await _ensure_registry_exists(db)

        from plugins.models import PluginRegistry

        result = await db.execute(
            select(PluginRegistry).where(PluginRegistry.name == plugin_name)
        )
        record = result.scalar_one_or_none()
        if record and record.is_installed:
            print(f"  插件 '{plugin_name}' 已安装，跳过 registry 写入")
        else:
            if record:
                record.is_installed = True
                record.version = plugin.version
            else:
                db.add(
                    PluginRegistry(
                        name=plugin_name,
                        version=plugin.version,
                        is_installed=True,
                    )
                )
            await db.commit()
            print(f"  registry 记录已写入")

        # 4. 种子数据
        print("  写入种子数据...")
        await plugin.on_install()
        await db.commit()

    # 5. 自动更新 .env 中的 PLUGINS__ENABLED
    _update_plugins_env(plugin_name, add=True)

    print(f"\n插件 '{plugin_name}' v{plugin.version} 安装完成\n")


async def uninstall_plugin(plugin_name: str) -> None:
    """
    卸载插件（全自动）：
    1. on_uninstall() — 清理种子数据
    2. 标记 plugin_registry 为未安装
    3. alembic autogenerate（不注册模型 → 检测多余表/列）+ upgrade
    """
    if plugin_name not in PLUGIN_MODULES:
        raise ValueError(f"Unknown plugin: {plugin_name}")

    from plugins.alembic_utils import generate_removal_and_upgrade
    from database.db_manager import init_pool, get_session

    print(f"\n正在卸载插件 '{plugin_name}'...")

    plugin = _load_plugin_class(plugin_name)

    await init_pool()
    async for db in get_session():
        await _ensure_registry_exists(db)

        from plugins.models import PluginRegistry

        result = await db.execute(
            select(PluginRegistry).where(
                PluginRegistry.name == plugin_name,
                PluginRegistry.is_installed == True,
            )
        )
        record = result.scalar_one_or_none()
        if not record:
            print(f"  插件 '{plugin_name}' 未安装，无需卸载")
            return

        # 1. 清理种子数据
        print("  清理种子数据...")
        await plugin.on_uninstall()

        # 2. 标记为未安装
        record.is_installed = False
        await db.commit()
        print("  registry 已标记为未安装")

    # 3. 生成删除迁移（不注册插件模型，autogenerate 自动检测多余表/列）
    print("  生成并执行删除迁移...")
    generate_removal_and_upgrade(plugin_name)

    print(f"\n插件 '{plugin_name}' 已卸载\n")

    # 4. 从 .env 的 PLUGINS__ENABLED 中移除
    _update_plugins_env(plugin_name, add=False)


async def list_plugins() -> List[dict]:
    """列出所有已知插件的安装状态"""
    from database.db_manager import init_pool, get_session

    result_list = []
    await init_pool()
    async for db in get_session():
        await _ensure_registry_exists(db)

        from plugins.models import PluginRegistry

        for plugin_name in PLUGIN_MODULES:
            plugin = _load_plugin_class(plugin_name)

            result = await db.execute(
                select(PluginRegistry).where(PluginRegistry.name == plugin_name)
            )
            record = result.scalar_one_or_none()

            result_list.append(
                {
                    "name": plugin_name,
                    "version": plugin.version,
                    "description": plugin.description,
                    "installed": record.is_installed if record else False,
                    "active": is_plugin_active(plugin_name),
                    "installed_at": str(record.installed_at) if record else None,
                }
            )
    return result_list
