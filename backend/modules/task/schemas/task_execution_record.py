#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
任务执行记录 Schema（独立版本）
"""
from typing import Optional, List, Dict, Any
from pydantic import Field, ConfigDict
from datetime import datetime

from app.models.common.base import (
    BaseEntity,
    BaseReqEntity,
    BaseRespEntity,
    OptionalIntField,
)


# ==================== 任务定义快照 Schema ====================

class TaskActionSnapshot(BaseReqEntity):
    """动作快照"""
    action: str = Field(..., description="运控动作")
    voice_text: Optional[str] = Field(None, description="语音播报文本")


class TaskPointSnapshot(BaseReqEntity):
    """点位快照"""
    sort_order: int = Field(0, description="排序")
    point_name: Optional[str] = Field(None, description="点位名称")
    annotation_id: Optional[int] = Field(None, description="关联场景标注ID")
    actions: List[TaskActionSnapshot] = Field(default_factory=list, description="动作列表")


class TaskDefinitionSnapshot(BaseReqEntity):
    """任务定义快照"""
    task_type: str = Field(..., description="任务类型: patrol/broadcast")
    task_name: Optional[str] = Field(None, description="任务名称")
    points: List[TaskPointSnapshot] = Field(default_factory=list, description="巡逻点位列表")
    broadcast_text: Optional[str] = Field(None, description="播报文本")


# ==================== 进度 Schema ====================

class PointProgressStatus(BaseReqEntity):
    """单点位进度状态"""
    index: int = Field(..., description="点位序号")
    status: str = Field("pending", description="点位状态: pending/running/completed/failed")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    finished_at: Optional[datetime] = Field(None, description="完成时间")


class ProgressDetail(BaseReqEntity):
    """详细进度"""
    total_points: int = Field(0, description="总点位数")
    completed_points: int = Field(0, description="已完成点位数")
    current_point_index: int = Field(0, description="当前执行点位序号")
    points_status: List[PointProgressStatus] = Field(
        default_factory=list, description="每个点位的状态"
    )


# ==================== 查询参数 Schema ====================

class TaskExecutionRecordQueryParams(BaseReqEntity):
    """任务执行记录查询参数"""
    status: Optional[str] = Field(None, description="执行状态")
    robot_id: OptionalIntField = Field(None, description="机器人ID")
    scene_id: OptionalIntField = Field(None, description="场景地图ID")
    user_id: OptionalIntField = Field(None, description="触发用户ID")
    source: Optional[str] = Field(None, description="触发源")
    start_time: Optional[str] = Field(None, description="开始时间(起)")
    end_time: Optional[str] = Field(None, description="结束时间(止)")


class TaskExecutionRecordStartIn(BaseReqEntity):
    """启动执行参数"""
    robot_ids: List[int] = Field(..., description="机器人ID列表", min_length=1)
    source: str = Field("manual", description="触发源: platform_schedule/voice_trigger/manual")


# ==================== 响应 Schema ====================

class TaskExecutionRecordResponseData(BaseRespEntity):
    """执行记录响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="执行记录ID")
    robot_id: Optional[int] = Field(None, description="机器人ID")
    robot_name: Optional[str] = Field(None, description="机器人名称")
    scene_id: Optional[int] = Field(None, description="场景地图ID")
    scene_name: Optional[str] = Field(None, description="场景地图名称")
    user_id: Optional[int] = Field(None, description="触发用户ID")
    user_name: Optional[str] = Field(None, description="触发用户名")
    task_definition: Optional[TaskDefinitionSnapshot] = Field(
        None, description="任务定义快照"
    )
    progress: Optional[ProgressDetail] = Field(None, description="详细进度")
    progress_per: int = Field(0, description="执行百分比 0-100")
    status: str = Field(..., description="执行状态")
    source: str = Field("manual", description="触发源")
    error_msg: Optional[str] = Field(None, description="错误信息")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    finish_time: Optional[datetime] = Field(None, description="结束时间")
    created_at: datetime = Field(..., description="创建时间")


class TaskExecutionRecordDetailResponseData(TaskExecutionRecordResponseData):
    """执行记录详情响应（task_definition 完整展开）"""
    pass
