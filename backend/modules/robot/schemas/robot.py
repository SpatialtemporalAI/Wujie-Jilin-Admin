#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional
from pydantic import Field, ConfigDict
from datetime import datetime

from pydantic import BaseModel

from app.models.common.base import BaseRespEntity, BaseReqEntity


class RobotQueryParams(BaseModel):
    """
    机器人查询参数模型
    用于机器人列表分页查询时的筛选条件
    """

    name: Optional[str] = Field(None, description="机器人名称，支持模糊查询")
    serial_number: Optional[str] = Field(None, description="序列号，支持模糊查询")
    status: Optional[str] = Field(None, description="状态：online/offline/inactive")
    model_id: Optional[int] = Field(None, description="型号ID")


class RobotCreate(BaseReqEntity):
    """
    机器人创建请求模型
    用于创建新机器人时的请求数据
    """

    name: str = Field(..., description="机器人名称", max_length=100)
    model_id: int = Field(..., description="型号ID")
    serial_number: str = Field(..., description="序列号", max_length=100)
    status: str = Field("inactive", description="状态：online/offline/inactive")


class RobotUpdate(BaseReqEntity):
    """
    机器人更新请求模型
    用于更新机器人信息时的请求数据
    """

    name: Optional[str] = Field(None, description="机器人名称", max_length=100)
    model_id: Optional[int] = Field(None, description="型号ID")
    serial_number: Optional[str] = Field(None, description="序列号", max_length=100)
    status: Optional[str] = Field(None, description="状态：online/offline/inactive")


class RobotResponseData(BaseRespEntity):
    """
    机器人响应模型
    用于展示机器人完整信息
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="机器人ID")
    name: str = Field(..., description="机器人名称")
    model_id: int = Field(..., description="型号ID")
    serial_number: str = Field(..., description="序列号")
    status: str = Field(..., description="状态")
    model_name: Optional[str] = Field(None, description="型号名称（关联查询）")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
