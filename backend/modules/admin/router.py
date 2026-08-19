#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
app路由初始化
"""
from fastapi import APIRouter
from .endpoints import auth_router, sys_router
from .endpoints.ws import ws_router

from modules.robot.router import router as robot_router
from modules.scene.router import router as scene_router
from modules.task.router import router as task_router
from modules.merchant.router import router as merchant_router
from modules.face.router import router as face_router
from modules.voice_consultation.router import router as voice_consultation_router

# 创建管理路由器
router = APIRouter(
    prefix="/admin",
)
router.include_router(auth_router)
router.include_router(sys_router)
router.include_router(ws_router)
router.include_router(robot_router)
router.include_router(scene_router)
router.include_router(task_router)
router.include_router(merchant_router)
router.include_router(face_router)
router.include_router(voice_consultation_router)
