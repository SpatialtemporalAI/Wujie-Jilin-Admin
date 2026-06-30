#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from typing import Optional, Any
from pydantic import Field, ConfigDict, field_validator
from datetime import datetime, timezone

from pydantic import BaseModel

from app.models.common.base import BaseRespEntity


class RobotStatusRecordQueryParams(BaseModel):
    """
    机器人状态记录查询参数模型
    用于状态记录列表分页查询时的筛选条件
    """

    robot_id: int = Field(..., description="机器人ID（必填）")


class LocationInfoData(BaseModel):
    """
    位置信息结构
    与前端 Api.Robot.LocationInfo 契约保持一致
    """

    x: Optional[float] = Field(None, description="x 坐标")
    y: Optional[float] = Field(None, description="y 坐标")
    angle: Optional[float] = Field(None, description="角度")
    update_at: Optional[str] = Field(None, description="更新时间")

    @field_validator("update_at", mode="before")
    @classmethod
    def _coerce_update_at(cls, v: Any) -> Any:
        # 兼容上报/历史脏数据：update_at 可能是 datetime、数字时间戳(秒/毫秒)等非字符串，
        # 而 schema 声明为 str，未规范化会导致响应序列化 422。统一转成字符串，无法解析置 None。
        if v is None or isinstance(v, str):
            return v
        if isinstance(v, datetime):
            return v.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(v, (int, float)):
            try:
                ts = float(v)
                if ts > 1e12:  # 毫秒级时间戳
                    ts /= 1000
                return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            except (OverflowError, OSError, ValueError):
                return None
        return None


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
    location_info: Optional[LocationInfoData] = Field(
        None, description="位置信息：{x, y, angle, update_at}"
    )
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    @field_validator("location_info", mode="before")
    @classmethod
    def _normalize_location_info(cls, v: Any) -> Any:
        # 兼容历史脏数据：location_info 被错误写入为 JSON 字符串标量（如 '"{}"'）
        # asyncpg 经 json.loads 解析后得到 Python str，这里再尝试解析为 dict
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
            except (ValueError, TypeError):
                return None
            return parsed if isinstance(parsed, dict) else None
        return v


class RobotLocationItem(BaseModel):
    """机器人位置项（地图编辑器按地图查询机器人实时位置用）

    位置数据由外部写入 DB，平台只读。同时透传 location_info(JSON) 与
    location(Text 历史字段)，由前端按优先级解析（见前端 extractRobotPoint）。
    """

    id: int = Field(..., description="机器人ID")
    name: str = Field(..., description="机器人名称")
    status: Optional[str] = Field(None, description="机器人状态：online/offline/inactive")
    map_id: Optional[int] = Field(None, description="绑定场景地图ID")
    location_info: Optional[LocationInfoData] = Field(
        None, description="位置信息：{x, y, angle, update_at}"
    )
    location: Optional[str] = Field(None, description="位置信息(JSON 字符串，历史字段)")

    @field_validator("location_info", mode="before")
    @classmethod
    def _normalize_location_info(cls, v: Any) -> Any:
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
            except (ValueError, TypeError):
                return None
            return parsed if isinstance(parsed, dict) else None
        return v

