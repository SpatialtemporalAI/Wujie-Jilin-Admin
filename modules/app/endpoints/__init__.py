#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .auth import router as auth_router
from .chat import router as chat_router
from .robot import router as robot_router
from .iot import router as iot_router
from .emergency_contact import router as emergency_contact_router
from .alarm import router as alarm_router
from .robot_scan import router as robot_scan_router
__all__ = [
    "auth_router",
    "chat_router",
    "robot_router",
    "iot_router",
    "emergency_contact_router",
    "alarm_router",
    "robot_scan_router",
]