#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
权限校验依赖
用于在API端点上检查当前用户是否具有指定的权限标识
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from database.db_manager import get_session
from app.models.sys.user import SysUser
from app.models.sys.role import SysRole
from app.models.sys.menu import SysMenu, MenuType
from core.exception.errors import ForbiddenError
from modules.admin.deps.auth.user_manager import current_user


def require_permission(permission_code: str):
    """
    创建一个权限校验依赖项

    Args:
        permission_code: 权限标识码，如 "sys:menu:add"

    Returns:
        FastAPI依赖项函数，校验当前用户是否具有指定权限
    """
    async def _check_permission(
        user: SysUser = Depends(current_user),
        db: AsyncSession = Depends(get_session),
    ) -> SysUser:
        # 超级用户跳过权限检查
        if user.is_superuser:
            return user

        # 查询用户角色关联的按钮权限中是否包含指定权限码
        stmt = (
            select(SysMenu.permission)
            .join(SysMenu.roles)
            .join(SysRole.users)
            .where(
                SysUser.id == user.id,
                SysMenu.type == MenuType.BUTTON,
                SysMenu.status == True,
                SysRole.status == True,
                SysMenu.permission == permission_code,
            )
            .limit(1)
        )
        result = await db.execute(stmt)
        if result.scalar_one_or_none() is None:
            raise ForbiddenError(msg=f"没有操作权限: {permission_code}")

        return user

    return _check_permission
