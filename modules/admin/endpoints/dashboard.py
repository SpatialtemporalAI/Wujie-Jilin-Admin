#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
后台仪表盘接口
提供系统概览信息
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from core.models.user import User
from core.models.device import Device
# 创建仪表盘路由器
dashboard_router = APIRouter()
@dashboard_router.get("/")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """获取仪表盘统计数据"""
    # 查询用户总数
    total_users = db.query(User).count()
    # 查询设备总数
    total_devices = db.query(Device).count()
    # 查询活跃设备数
    active_devices = db.query(Device).filter(Device.status == True).count()
    return {
        "total_users": total_users,
        "total_devices": total_devices,
        "active_devices": active_devices,
        "summary": "系统运行正常"
    }