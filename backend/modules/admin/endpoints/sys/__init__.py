#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
系统管理模块路由聚合
"""
from fastapi import APIRouter
from .config import config_router
from .dict import dict_router
from .menu import menu_router
from .permission import permission_router
from .role import role_router
from .user import user_router

# 创建系统管理主路由器
sys_router = APIRouter(
    prefix="/sys",
    tags=["系统管理"]
)

# 包含各个子模块路由
sys_router.include_router(config_router)
sys_router.include_router(dict_router)
sys_router.include_router(menu_router)
sys_router.include_router(permission_router)
sys_router.include_router(role_router)
sys_router.include_router(user_router)

__all__ = ["sys_router"]

