#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .robot_model import robot_model_router
from .robot import robot_router
from .robot_status_record import robot_status_record_router

__all__ = ["robot_model_router", "robot_router", "robot_status_record_router"]
