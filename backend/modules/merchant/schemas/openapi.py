#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""商户开放 API 请求/响应 Schema"""

from typing import Any, Dict, List, Optional

from pydantic import Field

from app.models.common.base import BaseEntity, BaseRespEntity


class GotoPointRequest(BaseEntity):
    """单点导航"""

    robot_sn: str = Field(..., description="目标机器人序列号（必须已绑定到当前商户）")
    point_id: int = Field(..., description="目标点位ID（scene_map_annotation.id）")


class NavigateRouteRequest(BaseEntity):
    """多点导航（按顺序途经）"""

    robot_sn: str = Field(..., description="目标机器人序列号")
    point_ids: List[int] = Field(..., description="途经点位ID列表（按顺序）")


class ExecuteTaskRequest(BaseEntity):
    """执行任务"""

    robot_sn: str = Field(..., description="目标机器人序列号")
    task_id: int = Field(..., description="任务ID")


class RobotSnRequest(BaseEntity):
    """任务控制（暂停/恢复/停止）：作用于该机器人当前活跃的执行记录"""

    robot_sn: str = Field(..., description="目标机器人序列号")


class TtsParams(BaseEntity):
    """语音播报参数"""

    voice: Optional[str] = Field(None, description="音色，如 male/female")
    speed: Optional[float] = Field(None, description="语速 0.5-2.0")
    volume: Optional[int] = Field(None, description="音量 0-100")


class SpeakRequest(BaseEntity):
    """语音播报"""

    robot_sn: str = Field(..., description="目标机器人序列号")
    text: str = Field(..., description="播报文本")
    tts_params: Optional[TtsParams] = Field(None, description="TTS 参数")


class ScenesRequest(BaseEntity):
    """获取场景列表"""

    robot_sn: Optional[str] = Field(None, description="可选：仅返回该机器人绑定的场景")


class PointsRequest(BaseEntity):
    """获取点位列表"""

    map_id: int = Field(..., description="场景地图ID（须属于当前商户可访问的场景）")


class TasksRequest(BaseEntity):
    """获取任务列表"""

    robot_sn: Optional[str] = Field(None, description="可选：仅返回关联该机器人的任务")
    map_id: Optional[int] = Field(None, description="可选：按场景地图过滤")
    task_type: Optional[str] = Field(None, description="可选：任务类型 patrol/broadcast")
    status: Optional[str] = Field(None, description="可选：执行状态 idle/running/paused")


class OpenApiResult(BaseRespEntity):
    """开放 API 通用结果"""

    success: bool = Field(..., description="是否成功")
    message: Optional[str] = Field(None, description="附加信息")
    data: Optional[Dict[str, Any]] = Field(None, description="附加数据")
