#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
商户模块路由聚合
- merchant_router: 后台管理（/merchant，JWT 鉴权）
- openapi_router : 商户开放 API（/openapi/v1，HMAC 签名鉴权）
"""
from fastapi import APIRouter

from .endpoints import merchant_router, openapi_router

router = APIRouter()
router.include_router(merchant_router)
router.include_router(openapi_router)
