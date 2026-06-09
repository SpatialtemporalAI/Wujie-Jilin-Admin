#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional
from pydantic import Field, ConfigDict
from datetime import datetime

from pydantic import BaseModel

from app.models.common.base import BaseRespEntity


class RobotStatusRecordQueryParams(BaseModel):
    """
    机器人状态记录查询参数模型
    用于状态记录列表分页查询时的筛选条件
    """

    robot_id: int = Field(..., description="机器人ID（必填）")


class RobotStatusRecordResponseData(BaseRespEntity):
    """
    机器人状态记录响应模型
    用于展示状态记录完整信息
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="记录ID")
    robot_id: int = Field(..., description="机器人ID")
    battery: float = Field(..., description="电量百分比")
    signal: int = Field(..., description="信号强度")
    speed: float = Field(..., description="速度(m/s)")
    location: Optional[str] = Field(None, description="位置信息(JSON)")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
