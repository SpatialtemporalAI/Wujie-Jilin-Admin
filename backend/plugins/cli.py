#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
插件管理 CLI

用法:
    cd backend
    python -m plugins install <plugin_name>    # 安装插件（自动生成+执行迁移+种子数据）
    python -m plugins uninstall <plugin_name>  # 卸载插件（清理数据+自动生成删除迁移）
    python -m plugins list                     # 查看所有插件状态
"""

import asyncio
import sys
import os

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def _run_install(plugin_name: str):
    from database.db_manager import init_pool, close_pool
    from plugins import install_plugin

    try:
        await install_plugin(plugin_name)
    finally:
        await close_pool()


async def _run_uninstall(plugin_name: str):
    from database.db_manager import init_pool, close_pool
    from plugins import uninstall_plugin

    print(f"\n警告: 卸载插件 '{plugin_name}' 将:")
    print("  1. 清理种子数据（菜单、默认租户等）")
    print("  2. 自动生成删除迁移（DROP TABLE / DROP COLUMN）")
    print("  3. 执行迁移")
    answer = input("\n确认卸载? (y/N): ")
    if answer.lower() != "y":
        print("卸载已取消")
        return

    try:
        await uninstall_plugin(plugin_name)
    finally:
        await close_pool()


async def _run_list():
    from database.db_manager import init_pool, close_pool
    from plugins import list_plugins

    try:
        await init_pool()
        plugins = await list_plugins()
    finally:
        await close_pool()

    print(f"\n{'名称':<20} {'版本':<10} {'已安装':<8} {'已激活':<8} {'说明'}")
    print("-" * 80)
    for p in plugins:
        installed = "是" if p["installed"] else "否"
        active = "是" if p["active"] else "否"
        print(
            f"{p['name']:<20} {p['version']:<10} {installed:<8} {active:<8} {p['description']}"
        )
    print()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == "install":
        if len(sys.argv) < 3:
            print("用法: python -m plugins install <plugin_name>")
            sys.exit(1)
        asyncio.run(_run_install(sys.argv[2]))

    elif command == "uninstall":
        if len(sys.argv) < 3:
            print("用法: python -m plugins uninstall <plugin_name>")
            sys.exit(1)
        asyncio.run(_run_uninstall(sys.argv[2]))

    elif command == "list":
        asyncio.run(_run_list())

    else:
        print(f"未知命令: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
