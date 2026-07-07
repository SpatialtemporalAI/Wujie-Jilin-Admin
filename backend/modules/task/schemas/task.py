#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional, List, Annotated, ClassVar
from pydantic import Field, ConfigDict, BeforeValidator, field_validator, ValidationInfo
from datetime import datetime, date, time

from app.models.common.base import BaseEntity, BaseRespEntity, BaseReqEntity, BoolField, OptionalIntField


def _bool_to_enable_str(v):
    """将 bool 转换为 "1"/"2" 字符串"""
    if isinstance(v, bool):
        return "1" if v else "2"
    return v

EnableStatusField = Annotated[str, BeforeValidator(_bool_to_enable_str)]

VALID_REPEAT_CYCLES = {'none', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'}


def _validate_repeat_cycle(v: Optional[str]) -> Optional[str]:
    """校验逗号分隔的重复周期值"""
    if v is None or v == '':
        return None
    for part in v.split(','):
        part = part.strip()
        if part not in VALID_REPEAT_CYCLES:
            raise ValueError(f"无效的重复周期值: {part}")
    return v


# ==================== 点位 Schema ====================

class TaskActionItem(BaseReqEntity):
    """巡逻点位单个动作"""
    action: str = Field(..., description="运控动作: shake_hand/high_five/hug/high_wave/clap/face_wave/left_kiss/hands_up/x_ray/right_hand_up/reject/right_kiss/two_hand_kiss/no", max_length=20)
    voice_text: Optional[str] = Field(None, description="语音播报文本")


class TaskPointCreate(BaseReqEntity):
    """巡逻点位创建"""
    sort_order: int = Field(0, description="排序")
    point_name: Optional[str] = Field(None, description="点位名称", max_length=100)
    annotation_id: Optional[int] = Field(None, description="关联场景标注ID")
    actions: List[TaskActionItem] = Field(default_factory=list, description="动作列表（支持多个，可为空）")


class TaskPointResponse(BaseRespEntity):
    """巡逻点位响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="点位ID")
    task_id: int = Field(..., description="任务ID")
    sort_order: int = Field(..., description="排序")
    point_name: Optional[str] = Field(None, description="点位名称")
    annotation_id: Optional[int] = Field(None, description="关联场景标注ID")
    actions: List[TaskActionItem] = Field(default_factory=list, description="动作列表")


# ==================== 机器人简要 Schema ====================

class TaskRobotBrief(BaseRespEntity):
    """任务关联机器人简要信息"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="机器人ID")
    name: str = Field(..., description="机器人名称")
    status: Optional[str] = Field(None, description="机器人状态")
    map_id: Optional[int] = Field(None, description="绑定场景地图ID")
    map_name: Optional[str] = Field(None, description="绑定场景地图名称")


# ==================== 任务 CRUD Schema ====================

class TaskQueryParams(BaseReqEntity):
    """任务查询参数"""
    name: Optional[str] = Field(None, description="任务名称，支持模糊查询")
    task_type: Optional[str] = Field(None, description="任务类型: patrol/broadcast")
    enabled: BoolField = Field(None, description="启用状态")
    robot_id: OptionalIntField = Field(None, description="关联机器人ID")
    map_id: OptionalIntField = Field(None, description="关联场景地图ID")


class TaskCreate(BaseReqEntity):
    """创建任务"""
    name: str = Field(..., description="任务名称", min_length=2, max_length=20)
    map_id: Optional[int] = Field(None, description="关联场景地图ID")
    task_type: str = Field(..., description="任务类型: patrol/broadcast")
    points: Optional[List[TaskPointCreate]] = Field(None, description="巡逻点位列表")
    broadcast_text: Optional[str] = Field(None, description="播报文本")
    broadcast_count: Optional[str] = Field(None, description="播报次数: 1/2/3/5/loop")
    robot_ids: List[int] = Field(..., description="绑定的机器人ID列表（巡逻任务仅支持单选，播报任务支持多选）", min_length=1)
    schedule_enabled: bool = Field(False, description="是否启用定时调度")
    schedule_date: Optional[date] = Field(None, description="调度日期")
    schedule_start_time: Optional[time] = Field(None, description="调度开始时间")
    schedule_repeat_cycle: Optional[str] = Field(None, description="重复周期: 逗号分隔 mon,tue,wed,thu,fri,sat,sun")

    @field_validator('schedule_repeat_cycle')
    @classmethod
    def validate_repeat_cycle(cls, v):
        return _validate_repeat_cycle(v)

    @field_validator('robot_ids')
    @classmethod
    def validate_robot_ids(cls, v: List[int], info: ValidationInfo) -> List[int]:
        """巡逻任务仅支持绑定一台机器人，播报任务支持多选"""
        task_type = info.data.get('task_type')
        if task_type == 'patrol' and len(v) > 1:
            raise ValueError('巡逻任务仅支持绑定一台机器人')
        return v


class TaskUpdate(BaseReqEntity):
    """更新任务"""
    name: Optional[str] = Field(None, description="任务名称", min_length=2, max_length=20)
    map_id: Optional[int] = Field(None, description="关联场景地图ID")
    task_type: Optional[str] = Field(None, description="任务类型")
    points: Optional[List[TaskPointCreate]] = Field(None, description="巡逻点位列表")
    broadcast_text: Optional[str] = Field(None, description="播报文本")
    broadcast_count: Optional[str] = Field(None, description="播报次数")
    robot_ids: Optional[List[int]] = Field(None, description="绑定的机器人ID列表（巡逻任务仅支持单选，播报任务支持多选）")
    schedule_enabled: Optional[bool] = Field(None, description="是否启用定时调度")
    schedule_date: Optional[date] = Field(None, description="调度日期")
    schedule_start_time: Optional[time] = Field(None, description="调度开始时间")
    schedule_repeat_cycle: Optional[str] = Field(None, description="重复周期: 逗号分隔 mon,tue,wed,thu,fri,sat,sun")

    @field_validator('schedule_repeat_cycle')
    @classmethod
    def validate_repeat_cycle(cls, v):
        return _validate_repeat_cycle(v)

    @field_validator('robot_ids')
    @classmethod
    def validate_robot_ids(cls, v: Optional[List[int]], info: ValidationInfo) -> Optional[List[int]]:
        """巡逻任务仅支持绑定一台机器人，播报任务支持多选；task_type 缺省时不限制"""
        if v is None:
            return v
        task_type = info.data.get('task_type')
        if task_type == 'patrol' and len(v) > 1:
            raise ValueError('巡逻任务仅支持绑定一台机器人')
        return v


class TaskResponseData(BaseEntity):
    """任务响应"""
    # status 为执行状态字符串，不能走 BaseRespEntity 的 bool 序列化，故仅跳过非空校验
    _skip_required_check: ClassVar[bool] = True
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="任务ID")
    name: str = Field(..., description="任务名称")
    map_id: Optional[int] = Field(None, description="关联场景地图ID")
    map_name: Optional[str] = Field(None, description="关联场景地图名称")
    task_type: str = Field(..., description="任务类型")
    enabled: EnableStatusField = Field(..., description="启用状态: 1-启用, 2-禁用")
    status: str = Field(..., description="执行状态")
    broadcast_text: Optional[str] = Field(None, description="播报文本")
    broadcast_count: Optional[str] = Field(None, description="播报次数")
    schedule_enabled: bool = Field(..., description="是否启用定时调度")
    schedule_date: Optional[date] = Field(None, description="调度日期")
    schedule_start_time: Optional[time] = Field(None, description="调度开始时间")
    schedule_repeat_cycle: Optional[str] = Field(None, description="重复周期")
    point_count: int = Field(0, description="巡逻点位数量")
    active_execution_count: int = Field(0, description="活跃执行数（running/pending）")
    points: Optional[List[TaskPointResponse]] = Field(None, description="巡逻点位列表")
    robots: Optional[List[TaskRobotBrief]] = Field(None, description="关联机器人列表")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")


class TaskToggleEnabled(BaseReqEntity):
    """切换启用/禁用"""
    enabled: bool = Field(..., description="启用状态")
