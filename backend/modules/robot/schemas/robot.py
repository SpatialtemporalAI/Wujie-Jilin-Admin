#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Any, Optional, Annotated
from pydantic import Field, ConfigDict, field_serializer, field_validator, BeforeValidator
from datetime import datetime

from pydantic import BaseModel

from app.models.common.base import BaseRespEntity, BaseReqEntity, OptionalIntField, parse_optional_enum

RobotStatusField = Annotated[
    Optional[str], BeforeValidator(parse_optional_enum({"online", "offline", "inactive"}))
]
SpeedLevelField = Annotated[
    Optional[str], BeforeValidator(parse_optional_enum({"normal", "slow", "low"}))
]


class RobotQueryParams(BaseModel):
    """
    机器人查询参数模型
    用于机器人列表分页查询时的筛选条件
    """

    name: Optional[str] = Field(None, description="机器人名称，支持模糊查询")
    serial_number: Optional[str] = Field(None, description="序列号，支持模糊查询")
    status: RobotStatusField = Field(None, description="状态：online/offline/inactive")
    model_id: OptionalIntField = Field(None, description="型号ID")
    map_id: OptionalIntField = Field(None, description="绑定场景地图ID")


class GrpcServiceConfig(BaseModel):
    """单套 gRPC 服务配置（agent / middleware 各一份）"""

    host: str = Field(..., description="gRPC 服务地址", max_length=128)
    port: int = Field(..., description="gRPC 服务端口", ge=1, le=65535)
    enabled: bool = Field(True, description="是否启用")


class RobotGrpcConfigPayload(BaseModel):
    """机器人 gRPC 配置载体：agent / middleware / ros 三套"""

    agent: Optional[GrpcServiceConfig] = Field(None, description="agent 端 gRPC 配置")
    middleware: Optional[GrpcServiceConfig] = Field(None, description="middleware 端 gRPC 配置")
    ros: Optional[GrpcServiceConfig] = Field(None, description="ros 端 gRPC 配置")


class RobotGrpcConfigUpdate(BaseReqEntity):
    """更新机器人 gRPC 配置请求"""

    grpc_config: RobotGrpcConfigPayload = Field(..., description="gRPC 配置")


class RobotMapBindingUpdate(BaseReqEntity):
    """更新机器人绑定场景请求（地图编辑器专用，与主表单 edit 解耦）"""

    map_id: Optional[int] = Field(
        None, description="绑定场景地图ID，传 null 表示解绑"
    )


class RobotCreate(BaseReqEntity):
    """
    机器人创建请求模型
    用于创建新机器人时的请求数据
    """

    name: str = Field(..., description="机器人名称", max_length=100)
    model_id: int = Field(..., description="型号ID")
    serial_number: str = Field(..., description="序列号", max_length=100)
    map_id: Optional[int] = Field(None, description="绑定场景地图ID")
    status: RobotStatusField = Field("inactive", description="状态：online/offline/inactive")
    speed_level: SpeedLevelField = Field(None, description="速度等级：normal/slow/low")
    battery_threshold: Optional[int] = Field(None, description="电量报警阈值(%)")


class RobotUpdate(BaseReqEntity):
    """
    机器人更新请求模型
    用于更新机器人信息时的请求数据
    """

    name: Optional[str] = Field(None, description="机器人名称", max_length=100)
    model_id: Optional[int] = Field(None, description="型号ID")
    serial_number: Optional[str] = Field(None, description="序列号", max_length=100)
    map_id: Optional[int] = Field(None, description="绑定场景地图ID")
    status: RobotStatusField = Field(None, description="状态：online/offline/inactive")
    speed_level: SpeedLevelField = Field(None, description="速度等级：normal/slow/low")
    battery_threshold: Optional[int] = Field(None, description="电量报警阈值(%)")


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
    map_id: Optional[int] = Field(None, description="绑定场景地图ID")
    map_name: Optional[str] = Field(None, description="绑定场景地图名称")
    status: str = Field(..., description="状态")
    speed_level: Optional[str] = Field(None, description="速度等级")
    battery_threshold: Optional[int] = Field(None, description="电量报警阈值(%)")
    grpc_config: Optional[RobotGrpcConfigPayload] = Field(
        None, description="gRPC 配置: { agent, middleware, ros }"
    )
    model_name: Optional[str] = Field(None, description="型号名称（关联查询）")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    # 兜底历史脏数据：grpc_config 中 agent / middleware / ros 子对象可能缺 host / port，
    # 写入侧 (update_grpc_config) 已严格校验，但库里若有旧的部分结构会让整页 list
    # 在响应序列化时 422。这里把不完整的子对象降级为 None，保住列表可用性。
    @field_validator("grpc_config", mode="before")
    @classmethod
    def _sanitize_grpc_config(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        for key in ("agent", "middleware", "ros"):
            sub = value.get(key)
            if isinstance(sub, dict) and (
                not sub.get("host") or sub.get("port") is None
            ):
                value[key] = None
        return value

    # 覆盖 BaseRespEntity 的 status 序列化器（后者将 status 当作布尔值转 "1"/"2"），
    # 机器人状态是 online/offline/inactive 字符串枚举，需保持原值。
    @field_serializer("status")
    def serialize_status_output(self, value):
        return value.value if hasattr(value, "value") else value


class SlotStatusData(BaseModel):
    """
    服务器自启动状态响应
    注意不能用 BaseRespEntity：其 status 序列化器会把 truthy 值转成 "1"，
    本接口 status 是中文字符串（已启动/启动中/启动失败/未配置/未知），需保持原值。
    """

    status: str = Field(
        ..., description="服务器自启动状态：已启动/启动中/启动失败/未配置/未知"
    )


class RobotSimpleResponse(BaseRespEntity):
    """
    机器人简化响应模型
    用于下拉选择等轻量场景，仅暴露必要字段（不含 grpc_config、battery_threshold 等敏感/无关字段）
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="机器人ID")
    name: str = Field(..., description="机器人名称")
    serial_number: str = Field(..., description="序列号")
    map_id: Optional[int] = Field(None, description="绑定场景地图ID")
    status: str = Field(..., description="状态：online/offline/inactive")

    # 与 RobotResponseData 保持一致的枚举序列化
    @field_serializer("status")
    def serialize_status_output(self, value):
        return value.value if hasattr(value, "value") else value
