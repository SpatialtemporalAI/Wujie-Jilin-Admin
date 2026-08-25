#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Literal, Optional
from pydantic import Field, ConfigDict, field_validator, model_validator
from datetime import datetime
from urllib.parse import urlsplit

from pydantic import BaseModel

from app.models.common.base import BaseEntity, BaseRespEntity, BaseReqEntity


def normalize_file_preview_path(value: str | None) -> str | None:
    if not value:
        return value
    parsed = urlsplit(value)
    return parsed.path if parsed.path.endswith("/preview") else value


class RobotVoiceConfigSchema(BaseReqEntity):
    """
    机器人语音合成配置请求模型
    """

    robot_id: int = Field(..., description="机器人ID")
    wake_word_enabled: bool = Field(default=False, description="是否启用唤醒词")
    wake_word: Optional[str] = Field(default=None, description="唤醒词", max_length=20)
    tts_voice: str = Field(..., description="音色", max_length=50)
    tts_speed: float = Field(..., description="语速（0.5-2.0，步长 0.1）", ge=0.5, le=2.0)
    tts_volume: int = Field(..., description="音量")

    @model_validator(mode="after")
    def validate_wake_word(self):
        """开关启用时唤醒词必填且 4-6 字；关闭时可空"""
        if self.wake_word_enabled:
            if not self.wake_word or not self.wake_word.strip():
                raise ValueError("唤醒词开关启用时，唤醒词不能为空")
            stripped = self.wake_word.strip()
            if len(stripped) < 4 or len(stripped) > 6:
                raise ValueError("唤醒词必须为 4-6 个字")
            self.wake_word = stripped
        else:
            if self.wake_word is not None:
                self.wake_word = self.wake_word.strip() or None
        return self


class RobotVoiceConfigResponse(BaseRespEntity):
    """
    机器人语音合成配置响应模型
    """

    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = Field(None, description="配置ID")
    robot_id: Optional[int] = Field(None, description="机器人ID")
    wake_word_enabled: Optional[bool] = Field(None, description="是否启用唤醒词")
    wake_word: Optional[str] = Field(None, description="唤醒词")
    tts_voice: Optional[str] = Field(None, description="音色")
    tts_speed: Optional[float] = Field(None, description="语速（0.5-2.0）")
    tts_volume: Optional[int] = Field(None, description="音量")
    greeting_mode: Optional[str] = Field(
        None, description="打招呼模式：wave-招手模式，no_wave-无招手模式"
    )
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    grpc_status: Optional[str] = Field(
        None, description="gRPC 推送状态：synced(已同步)/pending_retry(待重试)/disabled(未启用)"
    )


class RobotFaceRecognitionCreate(BaseReqEntity):
    """
    人脸识别TTS配置创建请求模型
    """

    person_name: str = Field(..., description="人员名称", max_length=100)
    photo_url: str = Field(..., description="人像图片URL", max_length=255)
    broadcast_text: str = Field(..., description="语音播报内容")

    @field_validator("photo_url", mode="before")
    @classmethod
    def normalize_photo_url(cls, value: str | None) -> str | None:
        return normalize_file_preview_path(value)


class RobotFaceRecognitionUpdate(BaseReqEntity):
    """
    人脸识别TTS配置更新请求模型
    """

    person_name: Optional[str] = Field(None, description="人员名称", max_length=100)
    photo_url: Optional[str] = Field(None, description="人像图片URL", max_length=255)
    broadcast_text: Optional[str] = Field(None, description="语音播报内容")

    @field_validator("photo_url", mode="before")
    @classmethod
    def normalize_photo_url(cls, value: str | None) -> str | None:
        return normalize_file_preview_path(value)


class RobotFaceRecognitionResponse(BaseRespEntity):
    """
    人脸识别TTS配置响应模型
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="配置ID")
    person_name: str = Field(..., description="人员名称")
    photo_url: str = Field(..., description="人像图片URL")
    broadcast_text: str = Field(..., description="语音播报内容")
    entity_id: Optional[str] = Field(None, description="阿里云人脸库实体ID")
    face_id: Optional[str] = Field(None, description="阿里云人脸图片ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    grpc_status: Optional[str] = Field(
        None, description="gRPC 推送状态：synced/pending_retry/disabled"
    )


class TestWakeWordRequest(BaseReqEntity):
    """
    测试唤醒词请求模型
    """

    robot_id: int = Field(..., description="机器人ID")
    text: str = Field(..., description="要测试的唤醒词文本")


class TestTTSRequest(BaseReqEntity):
    """
    测试TTS请求模型
    """

    robot_id: int = Field(..., description="机器人ID")
    voice: str = Field(..., description="音色")
    speed: float = Field(..., description="语速（0.5-2.0）", ge=0.5, le=2.0)
    volume: int = Field(..., description="音量")
    text: str = Field(..., description="要播报的文本")


class RobotSpeedLevelUpdate(BaseReqEntity):
    """机器人行走速度配置更新"""

    speed_level: Optional[str] = Field(
        None, description="速度等级: normal/slow/low", max_length=20
    )


class RobotBatteryThresholdUpdate(BaseReqEntity):
    """机器人电量报警阈值更新"""

    battery_threshold: int = Field(
        ..., description="电量报警阈值(5-50)", ge=5, le=50
    )


class RobotGreetingModeUpdate(BaseReqEntity):
    """机器人打招呼模式更新"""

    greeting_mode: Literal["wave", "no_wave"] = Field(
        ..., description="打招呼模式：wave-招手模式，no_wave-无招手模式"
    )


class RobotVideoMonitoringControl(BaseReqEntity):
    """视频监控启停请求（robot_id 走 path）"""

    enabled: bool = Field(..., description="true=启动视频监控 / false=停止")
    viewer_id: Optional[str] = Field(
        default=None, description="观众会话 ID，停止/心跳时必填"
    )


class RobotVideoMonitoringTicket(BaseEntity):
    """视频监控打开成功后返回的 LiveKit 连接票据"""

    room: str = Field(..., description="LiveKit 房间名，等于机器人 serial_number")
    token: str = Field(..., description="LiveKit 观众 Token")
    server_url: str = Field(..., description="LiveKit WebSocket 连接地址")
    viewer_id: str = Field(..., description="观众会话 ID，关闭/心跳时回传")
    robot_serial_number: str = Field(..., description="机器人序列号")


class RobotVideoMonitoringHeartbeat(BaseReqEntity):
    """视频监控观众心跳请求"""

    viewer_id: str = Field(..., description="观众会话 ID")


class ConfigUpdateResponse(BaseRespEntity):
    """参数配置保存响应（speed/battery 等不返回完整 ORM 的场景，仅携带 grpc_status）"""

    grpc_status: Optional[str] = Field(
        None, description="gRPC 推送状态：synced/pending_retry/disabled"
    )
