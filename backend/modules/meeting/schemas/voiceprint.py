#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime

from pydantic import Field, field_serializer

from app.models.common.base import BaseEntity, BaseRespEntity

ROLE_TYPES = {"主持人", "发言人", "记录员", "旁听"}
VOICEPRINT_METHODS = {"record", "stream"}
VOICEPRINT_STATUSES = {"processing", "success", "failed"}


class VoiceprintQueryParams(BaseEntity):
    """声纹列表查询参数（统一用 Optional[str]，空值收敛在 service 层）"""

    robot_id: str | None = Field(None, description="机器人ID")
    keyword: str | None = Field(None, description="角色名称关键词")
    status: str | None = Field(None, description="注册状态：processing/success/failed")


class VoiceprintRobotItem(BaseRespEntity):
    """声纹页可选机器人"""

    id: int
    name: str
    serial_number: str
    model_name: str | None = Field(None, description="机器人型号名称")
    robot_status: str = Field(..., description="机器人状态：online/offline/inactive")
    meeting_mode: bool = Field(..., description="会议模式是否开启")
    registered_count: int = Field(0, description="已注册声纹数量")


class VoiceprintResponse(BaseRespEntity):
    """声纹记录响应"""

    id: int
    robot_id: int
    robot_name: str | None = None
    role_name: str
    role_type: str
    method: str
    status: str
    voiceprint_id: str | None = None
    transcript: str | None = None
    score: int | None = None
    clarity: int | None = None
    match_score: int | None = None
    noise_level: str | None = None
    sample_url: str | None = None
    error_msg: str | None = None
    created_at: datetime | None = None

    @field_serializer("status")
    def serialize_status_output(self, value):
        """注册状态是字符串枚举，覆盖 BaseRespEntity 的 bool -> 1/2 序列化"""
        return value.value if hasattr(value, "value") else value


class VoiceprintRegisterResponse(VoiceprintResponse):
    """声纹注册结果"""


class MeetingModeUpdate(BaseEntity):
    """切换会议模式请求"""

    robot_id: int = Field(..., description="目标机器人ID")
    enabled: bool = Field(..., description="true-开启会议模式，false-关闭")


class MeetingModeStatusData(BaseEntity):
    """会议模式状态"""

    meeting_mode: bool = Field(..., description="true-监听中，false-未开启")
    registered_count: int = Field(0, description="已注册声纹数量")


class VoiceprintOverviewData(BaseEntity):
    """声纹页概览"""

    meeting_mode: bool = Field(..., description="会议模式是否开启")
    registered_count: int = Field(0, description="已注册声纹数量")
