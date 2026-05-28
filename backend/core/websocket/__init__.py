#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WebSocket 通信层模块
提供可插拔的实时通信连接管理抽象
"""

from .manager import ConnectionManager
from .connection import FastAPIConnectionManager

__all__ = ["ConnectionManager", "FastAPIConnectionManager"]
