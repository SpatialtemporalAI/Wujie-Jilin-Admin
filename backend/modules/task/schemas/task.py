#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional, List, Annotated, ClassVar
from pydantic import Field, ConfigDict, BeforeValidator, field_validator, model_validator, ValidationInfo
from datetime import datetime, date, time

from app.models.common.base import BaseEntity, BaseRespEntity, BaseReqEntity


def _bool_to_enable_str(v):
    """将 bool 转换为 "1"/"2" 字符串"""
    if isinstance(v, bool):
        return "1" if v else "2"
    return v

EnableStatusField = Annotated[str, BeforeValidator(_bool_to_enable_str)]

VALID_REPEAT_CYCLES = {'none', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'}

# 表演任务（八段锦）约束：动作与音乐均为后端预置，本期不支持用户上传音频
VALID_PERFORMANCE_ACTIONS = {'baduanjin_1', 'baduanjin_2', 'baduanjin_3'}
VALID_PERFORMANCE_MUSIC = {'bdj_1', 'bdj_2', 'bdj_3', 'bdj_full_12min'}
PERFORMANCE_MAX_STEPS = 3
PERFORMANCE_MAX_INTERVAL = 300


def _validate_repeat_cycle(v: Optional[str]) -> Optional[str]:
    """校验逗号分隔的重复周期值"""
    if v is None or v == '':
        return None
    for part in v.split(','):
        part = part.strip()
        if part not in VALID_REPEAT_CYCLES:
            raise ValueError(f"无效的重复周期值: {part}")
    return v


# ==================== 播报步骤 Schema ====================

class BroadcastStepSchema(BaseReqEntity):
    """播报任务单个步骤：content 与 actions 均非必填，但二者至少有其一；
    interval 仅非最后一步需要（最后一步无后续间隔），允许为空"""

    content: Optional[str] = Field(None, description="播报内容", max_length=1000)
    interval: Optional[int] = Field(None, description="播报间隔（秒），最后一步可为空", ge=0)
    actions: List[str] = Field(default_factory=list, description="动作列表（同一动作可重复出现）")

    @model_validator(mode='after')
    def validate_at_least_one(self):
        has_content = bool(self.content and self.content.strip())
        has_actions = bool(self.actions)
        if not has_content and not has_actions:
            raise ValueError('播报内容与动作至少填写一项')
        return self


# ==================== 表演步骤 Schema ====================

class PerformanceStepSchema(BaseReqEntity):
    """表演任务单套动作（八段锦）：动作与音乐均为后端预置标识；
    play_count 播放次数最低 1，interval 套间间隔 0-300 秒（最后一套可为空）"""

    action: str = Field(..., description="表演动作: baduanjin_1/baduanjin_2/baduanjin_3", max_length=30)
    music: str = Field(..., description="背景音乐（预设标识）: bdj_1/bdj_2/bdj_3/bdj_full_12min", max_length=30)
    play_count: int = Field(1, description="播放次数（循环动作+音乐）", ge=1)
    interval: Optional[int] = Field(None, description="套间间隔（秒），最后一套可为空", ge=0, le=PERFORMANCE_MAX_INTERVAL)

    @field_validator('action')
    @classmethod
    def validate_action(cls, v: str) -> str:
        if v not in VALID_PERFORMANCE_ACTIONS:
            raise ValueError(f"无效的表演动作: {v}")
        return v

    @field_validator('music')
    @classmethod
    def validate_music(cls, v: str) -> str:
        if v not in VALID_PERFORMANCE_MUSIC:
            raise ValueError(f"无效的背景音乐: {v}")
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
    """任务查询参数

    注意：查询参数统一使用基础 Optional[str] 而非 Annotated[Optional[int/bool], BeforeValidator]，
    FastAPI 对 Depends() query 模型中的 Annotated 字段在部分版本存在兼容性问题（可能漏收集
    请求参数导致模型构造缺键报 missing）；空值/脏值收敛由 service 层完成。
    """

    name: Optional[str] = Field(None, description="任务名称，支持模糊查询")
    task_type: Optional[str] = Field(None, description="任务类型: patrol/broadcast/performance")
    enabled: Optional[str] = Field(None, description="启用状态")
    robot_id: Optional[str] = Field(None, description="关联机器人ID")
    map_id: Optional[str] = Field(None, description="关联场景地图ID")


class TaskCreate(BaseReqEntity):
    """创建任务"""
    name: str = Field(..., description="任务名称", min_length=2, max_length=20)
    map_id: Optional[int] = Field(None, description="关联场景地图ID")
    task_type: str = Field(..., description="任务类型: patrol/broadcast/performance")
    points: Optional[List[TaskPointCreate]] = Field(None, description="巡逻点位列表")
    broadcast_text: Optional[str] = Field(None, description="播报文本（兼容旧数据）")
    broadcast_count: Optional[str] = Field(None, description="播报次数: 1/2/3/5/loop")
    broadcast_steps: Optional[List[BroadcastStepSchema]] = Field(None, description="播报步骤列表")
    performance_steps: Optional[List[PerformanceStepSchema]] = Field(None, description="表演步骤列表（最多3套）")
    robot_ids: List[int] = Field(..., description="绑定的机器人ID列表（巡逻任务仅支持单选，播报/表演任务支持多选）", min_length=1)
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

    @model_validator(mode='after')
    def validate_broadcast_steps(self):
        """播报任务必须包含至少一个步骤（每个步骤的内容/动作校验由 BroadcastStepSchema 负责）；
        除最后一步外，其余步骤必须填写播报间隔"""
        if self.task_type != 'broadcast':
            return self
        steps = self.broadcast_steps
        if not steps or len(steps) == 0:
            raise ValueError('播报任务至少包含一个播报步骤')
        for idx, step in enumerate(steps[:-1]):
            if step.interval is None:
                raise ValueError(f'步骤 {idx + 1} 的播报间隔不能为空')
        return self

    @model_validator(mode='after')
    def validate_performance_steps(self):
        """表演任务必须包含 1-3 套动作（每个步骤的动作/音乐校验由 PerformanceStepSchema 负责）；
        除最后一套外，其余套必须填写套间间隔"""
        if self.task_type != 'performance':
            return self
        steps = self.performance_steps
        if not steps or len(steps) == 0:
            raise ValueError('表演任务至少包含一套表演动作')
        if len(steps) > PERFORMANCE_MAX_STEPS:
            raise ValueError(f'表演任务最多包含 {PERFORMANCE_MAX_STEPS} 套动作')
        for idx, step in enumerate(steps[:-1]):
            if step.interval is None:
                raise ValueError(f'第 {idx + 1} 套动作的套间间隔不能为空')
        return self


class TaskUpdate(BaseReqEntity):
    """更新任务"""
    name: Optional[str] = Field(None, description="任务名称", min_length=2, max_length=20)
    map_id: Optional[int] = Field(None, description="关联场景地图ID")
    task_type: Optional[str] = Field(None, description="任务类型")
    points: Optional[List[TaskPointCreate]] = Field(None, description="巡逻点位列表")
    broadcast_text: Optional[str] = Field(None, description="播报文本（兼容旧数据）")
    broadcast_count: Optional[str] = Field(None, description="播报次数")
    broadcast_steps: Optional[List[BroadcastStepSchema]] = Field(None, description="播报步骤列表")
    performance_steps: Optional[List[PerformanceStepSchema]] = Field(None, description="表演步骤列表（最多3套）")
    robot_ids: Optional[List[int]] = Field(None, description="绑定的机器人ID列表（巡逻任务仅支持单选，播报/表演任务支持多选）")
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

    @model_validator(mode='after')
    def validate_broadcast_steps(self):
        """播报任务必须包含至少一个步骤（每个步骤的内容/动作校验由 BroadcastStepSchema 负责）；
        除最后一步外，其余步骤必须填写播报间隔"""
        if self.task_type != 'broadcast':
            return self
        steps = self.broadcast_steps
        if steps is None:
            return self
        if len(steps) == 0:
            raise ValueError('播报任务至少包含一个播报步骤')
        for idx, step in enumerate(steps[:-1]):
            if step.interval is None:
                raise ValueError(f'步骤 {idx + 1} 的播报间隔不能为空')
        return self

    @model_validator(mode='after')
    def validate_performance_steps(self):
        """表演任务必须包含 1-3 套动作；task_type 缺省或 performance_steps 为 None 时跳过"""
        if self.task_type != 'performance':
            return self
        steps = self.performance_steps
        if steps is None:
            return self
        if len(steps) == 0:
            raise ValueError('表演任务至少包含一套表演动作')
        if len(steps) > PERFORMANCE_MAX_STEPS:
            raise ValueError(f'表演任务最多包含 {PERFORMANCE_MAX_STEPS} 套动作')
        for idx, step in enumerate(steps[:-1]):
            if step.interval is None:
                raise ValueError(f'第 {idx + 1} 套动作的套间间隔不能为空')
        return self


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
    broadcast_text: Optional[str] = Field(None, description="播报文本（兼容旧数据）")
    broadcast_count: Optional[str] = Field(None, description="播报次数")
    broadcast_steps: Optional[List[BroadcastStepSchema]] = Field(None, description="播报步骤列表")
    performance_steps: Optional[List[PerformanceStepSchema]] = Field(None, description="表演步骤列表")
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


# ==================== 预设表演资源 Schema ====================

class PerformanceActionOption(BaseRespEntity):
    """表演动作下拉选项（预训练八段锦）"""
    value: str = Field(..., description="动作标识")
    label: str = Field(..., description="展示名称")
    duration_seconds: int = Field(..., description="单套动作时长（秒）")


class PerformanceMusicOption(BaseRespEntity):
    """背景音乐下拉选项（预设，本期不支持上传）"""
    value: str = Field(..., description="音乐标识")
    label: str = Field(..., description="展示名称")
    duration_seconds: int = Field(..., description="音频时长（秒，≤240）")
    file_url: Optional[str] = Field(None, description="试听文件地址（预留）")
