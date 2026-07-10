#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
商户模块路由聚合
- merchant_router : 后台商户管理（/merchant，JWT 鉴权）
- call_log_router : 开放 API 调用日志管理（/merchant/call-log，JWT 鉴权）

注：商户开放 API（/openapi/v1，HMAC 签名鉴权）由主应用在 main.py 中直接挂载，
    不经过 /admin 前缀，以保持与第三方接入方的常见约定一致。
"""
from fastapi import APIRouter

from .endpoints import merchant_router, call_log_router

router = APIRouter()
router.include_router(merchant_router)
router.include_router(call_log_router)
