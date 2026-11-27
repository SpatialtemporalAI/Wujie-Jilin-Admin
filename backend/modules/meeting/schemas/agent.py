#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
机器人 agent 上报协议 Schema
"""
from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic import Field, field_validator

from app.models.common.base import BaseEntity

LOCAL_TZ = ZoneInfo("Asia/Shanghai")


def _parse_datetime(value):
    """兼容 ISO8601 / 'YYYY-MM-DD HH:MM:SS'，无时区按 Asia/Shanghai 处理。"""
    if value is None or isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip()
        if not text:
            return None
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if isinstance(dt, datetime) and dt.tzinfo is None:
        dt = dt.replace(tzinfo=LOCAL_TZ)
    return dt


class AgentSpeakerPayload(BaseEntity):
    """agent 上报的发言人"""

    speaker_key: str = Field(..., description="agent 侧发言人标识，如 s1", max_length=40)
    name: str = Field(..., description="发言人姓名", max_length=50)
    role: str | None = Field(None, description="发言人角色，如 主任医师", max_length=50)
    color: str | None = Field(None, description="头像颜色标识：blue/purple/green/orange", max_length=20)
    match_score: int | None = Field(None, description="声纹匹配度 0-100")
    voiceprint_id: str | None = Field(None, description="关联声纹ID", max_length=64)
    sort: int = Field(0, description="展示排序")


class AgentSegmentPayload(BaseEntity):
    """agent 上报的逐字稿片段"""

    seq: int | None = Field(None, description="片段序号，缺省按数组顺序补齐")
    speaker_key: str | None = Field(None, description="发言人标识", max_length=40)
    timecode: str | None = Field(None, description="时间码，如 04:01", max_length=16)
    start_seconds: float | None = Field(None, description="片段起始秒数，用于音频跳转")
    text: str = Field(..., description="逐字稿文本")
    confidence: int | None = Field(None, description="声纹匹配置信度 0-100")
    need_confirm: bool = Field(False, description="是否为低置信待确认片段")
    audio_url: str | None = Field(None, description="片段音频地址", max_length=500)


class AgentMinuteReportPayload(BaseEntity):
    """agent 会后上报的会议纪要"""

    meeting_no: str | None = Field(None, description="会议编号，缺省由平台生成", max_length=40)
    title: str = Field(..., description="会议标题", max_length=200)
    robot_id: int = Field(..., description="录制机器人ID")
    started_at: datetime = Field(..., description="会议开始时间")
    duration_seconds: int = Field(0, description="会议时长（秒）")
    overview: str | None = Field(None, description="会议概览/机器人总结")
    conclusions: list | None = Field(None, description="关键结论列表")
    risks: list | None = Field(None, description="待确认提醒列表")
    summary_generated_at: datetime | None = Field(None, description="总结生成时间")
    audio_file_id: int | None = Field(None, description="整场录音文件ID（先调用文件上传接口获得）")
    audio_url: str | None = Field(None, description="整场录音地址", max_length=500)
    speakers: list[AgentSpeakerPayload] = Field(default_factory=list, description="发言人列表")
    segments: list[AgentSegmentPayload] = Field(default_factory=list, description="逐字稿片段列表")

    @field_validator("started_at", "summary_generated_at", mode="before")
    @classmethod
    def _normalize_datetime(cls, value):
        return _parse_datetime(value)


class AgentMinuteReportResponse(BaseEntity):
    """agent 上报结果"""

    id: int = Field(..., description="会议纪要ID")
    meeting_no: str = Field(..., description="会议编号")
    created: bool = Field(..., description="true-新建，false-覆盖更新")
    speaker_count: int = Field(0, description="发言人数")
    segment_count: int = Field(0, description="逐字稿段数")


class AgentFileUploadResponse(BaseEntity):
    """agent 音频上传结果"""

    file_id: int = Field(..., description="文件ID")
    url: str | None = Field(None, description="文件访问地址")
    original_name: str = Field(..., description="原始文件名")
    file_size: int = Field(..., description="文件大小（字节）")
    mime_type: str = Field(..., description="MIME 类型")
