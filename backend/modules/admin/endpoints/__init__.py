#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .auth import router as auth_router
from .sys import sys_router

__all__ = ["auth_router", "sys_router"]
