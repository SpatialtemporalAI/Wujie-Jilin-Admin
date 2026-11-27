#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime

from pydantic import Field

from app.models.common.base import BaseEntity, BaseRespEntity


class MinuteQueryParams(BaseEntity):
    """会议纪要列表查询参数"""

    keyword: str | None = Field(None, description="搜索会议标题/总结/发言人")
    robot_id: str | None = Field(None, description="机器人ID")
    time_range: str | None = Field(None, description="时间范围：all/today/7/30")
    sort: str | None = Field(None, description="排序：desc-由近到远，asc-由远到近")


class MinuteSpeakerResponse(BaseRespEntity):
    """会议发言人"""

    id: int
    speaker_key: str
    name: str
    role: str | None = None
    color: str | None = None
    match_score: int | None = None
    voiceprint_id: str | None = None
    sort: int = 0


class MinuteSegmentResponse(BaseRespEntity):
    """逐字稿片段"""

    id: int
    seq: int
    speaker_id: int | None = None
    speaker_key: str | None = None
    timecode: str | None = None
    start_seconds: float | None = None
    text: str
    confidence: int | None = None
    need_confirm: bool = False
    audio_url: str | None = None


class MinuteListItem(BaseRespEntity):
    """会议纪要列表项"""

    id: int
    meeting_no: str
    title: str
    robot_id: int
    robot_name: str | None = None
    robot_model_name: str | None = None
    started_at: datetime
    duration_seconds: int = 0
    speaker_count: int = 0
    segment_count: int = 0
    overview: str | None = None
    conclusions: list | None = None
    risks: list | None = None
    summary_generated_at: datetime | None = None
    audio_url: str | None = None
    deleted_at: datetime | None = None
    created_at: datetime | None = None
    speakers: list[MinuteSpeakerResponse] = Field(default_factory=list)


class MinuteDetailResponse(MinuteListItem):
    """会议纪要详情"""

    segments: list[MinuteSegmentResponse] = Field(default_factory=list)


class SegmentSpeakerUpdate(BaseEntity):
    """人工改派发言人请求"""

    speaker_id: int = Field(..., description="目标发言人ID（必须属于同一会议）")


class MinuteExportQuery(BaseEntity):
    """纪要导出参数"""

    format: str | None = Field("md", description="导出格式：md/txt，默认 md")


class MinuteTrashClearResponse(BaseEntity):
    """清空回收站结果"""

    purged_count: int = Field(0, description="彻底删除的会议数量")


class MinuteExportData(BaseEntity):
    """纪要导出内容"""

    filename: str = Field(..., description="建议文件名")
    content: str = Field(..., description="文件内容")
    mime_type: str = Field(..., description="MIME类型")
