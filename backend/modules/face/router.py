#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
人脸库管理模块路由聚合
"""
from fastapi import APIRouter

from .endpoints import face_router

router = APIRouter()
router.include_router(face_router)
