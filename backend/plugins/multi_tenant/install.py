#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
多租户插件安装（兼容入口）

推荐使用统一 CLI:
    python -m plugins install multi_tenant
    python -m plugins uninstall multi_tenant
    python -m plugins list
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def main():
    print("提示: 推荐使用 python -m plugins install multi_tenant\n")
    from plugins.cli import _run_install
    asyncio.run(_run_install("multi_tenant"))


if __name__ == "__main__":
    main()
