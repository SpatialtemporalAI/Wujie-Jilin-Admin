#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
app路由初始化
"""
from fastapi import APIRouter
from .endpoints import auth_router
# 创建管理路由器
router = APIRouter(
    prefix="/app",
)
# 注册各个管理路由
router.include_router(auth_router)