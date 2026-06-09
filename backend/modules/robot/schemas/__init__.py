#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .robot_model import (
    RobotModelQueryParams,
    RobotModelCreate,
    RobotModelUpdate,
    RobotModelResponseData,
)
from .robot import (
    RobotQueryParams,
    RobotCreate,
    RobotUpdate,
    RobotResponseData,
)
from .robot_status_record import (
    RobotStatusRecordQueryParams,
    RobotStatusRecordResponseData,
)

__all__ = [
    # 机器人型号相关
    "RobotModelQueryParams",
    "RobotModelCreate",
    "RobotModelUpdate",
    "RobotModelResponseData",
    # 机器人相关
    "RobotQueryParams",
    "RobotCreate",
    "RobotUpdate",
    "RobotResponseData",
    # 机器人状态记录相关
    "RobotStatusRecordQueryParams",
    "RobotStatusRecordResponseData",
]
