#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
认证模块初始化文件
导出认证相关的路由和依赖项
"""
from .user_manager import (
    UserManager,
    current_user,
    get_user_manager,
)
__all__ = [
    "router",
    "current_user",
    "get_user_manager",
]