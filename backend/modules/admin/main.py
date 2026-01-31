#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from .router import router
app = FastAPI(
    title=settings.SERVICE.NAME, version="1.0.0", docs_url="/docs", redoc_url="/redoc"
)
# 配置跨域（允许其他服务访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# 挂载认证路由
app.include_router(router)
@app.get("/health")
def health_check():
    """服务健康检查接口"""
    return {"status": "healthy", "service": "admin-service"}