#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""临时脚本：列出最近创建的用户和角色，用于确认待清理的测试数据"""
import asyncio
import sys

sys.path.insert(0, ".")

from sqlalchemy import select
from database.db_manager import init_pool, close_pool, get_session
from database.models.sys.user import SysUser
from database.models.sys.role import SysRole


async def main():
    await init_pool()
    try:
        async for db in get_session():
            roles = (
                await db.execute(select(SysRole).order_by(SysRole.created_at.desc()).limit(10))
            ).scalars().all()
            print("=== 最近创建的角色 ===")
            for r in roles:
                print(f"id={r.id} name={r.name!r} status={r.status} is_system={r.is_system} created_at={r.created_at}")

            users = (
                await db.execute(select(SysUser).order_by(SysUser.created_at.desc()).limit(10))
            ).scalars().all()
            print("=== 最近创建的用户 ===")
            for u in users:
                print(f"id={u.id} username={u.username!r} nickname={u.nickname!r} status={u.status} created_at={u.created_at}")
            break
    finally:
        await close_pool()


asyncio.run(main())
