#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import List, Optional

from pydantic import Field, ConfigDict, BaseModel

from app.models.common.base import BaseReqEntity, BaseRespEntity


class EditorAnnotationItem(BaseReqEntity):
    """编辑器标注项（支持新建和更新）"""

    id: int | None = Field(None, description="标注ID，为空时新建")
    client_temp_id: int | None = Field(None, description="前端临时id（负数），仅新建项需要，用于回填真实id")
    x: float = Field(..., description="X坐标")
    y: float = Field(..., description="Y坐标")
    name: str = Field(..., description="标注名称")
    angle: float = Field(0, description="角度(弧度)")
    type: str = Field(..., description="标注类型(字典值)")


class EditorPathItem(BaseReqEntity):
    """编辑器路径项（支持新建和更新）"""

    id: int | None = Field(None, description="路径ID，为空时新建")
    client_temp_id: int | None = Field(None, description="前端临时id（负数），仅新建项需要，用于回填真实id")
    start_annotation_id: int = Field(..., description="起始标注ID")
    end_annotation_id: int = Field(..., description="结束标注ID")
    name: str | None = Field(None, description="路径名称")
    points: str | None = Field(None, description="中间路径点(JSON数组)")


class EditorObjectItem(BaseReqEntity):
    """编辑器物体项（支持新建和更新）"""

    id: int | None = Field(None, description="物体ID，为空时新建")
    client_temp_id: int | None = Field(None, description="前端临时id（负数），仅新建项需要，用于回填真实id")
    type: str = Field(..., description="物体类型(字典值)")
    name: str | None = Field(None, description="物体名称")
    x: float = Field(..., description="X坐标")
    y: float = Field(..., description="Y坐标")
    width: float = Field(0, description="宽度")
    height: float = Field(0, description="高度")
    points: str | None = Field(None, description="多边形顶点(JSON数组)")
    angle: float = Field(0, description="旋转角度(度)")


class EditorSaveRequest(BaseReqEntity):
    """编辑器批量保存请求"""

    annotations: List[EditorAnnotationItem] = Field(default_factory=list, description="标注列表")
    paths: List[EditorPathItem] = Field(default_factory=list, description="路径列表")
    objects: List[EditorObjectItem] = Field(default_factory=list, description="物体列表")
    deleted_annotation_ids: List[int] = Field(default_factory=list, description="已删除的标注ID")
    deleted_path_ids: List[int] = Field(default_factory=list, description="已删除的路径ID")
    deleted_object_ids: List[int] = Field(default_factory=list, description="已删除的物体ID")


class CreatedIdMapping(BaseModel):
    """新建元素的临时id与真实id映射"""

    temp_id: int = Field(..., description="前端临时id")
    id: int = Field(..., description="后端真实id")


class EditorSaveResponse(BaseModel):
    """编辑器保存响应：返回本次新建元素的真实id，供前端回填"""

    created_annotations: List[CreatedIdMapping] = Field(default_factory=list, description="新建标注的id映射")
    created_objects: List[CreatedIdMapping] = Field(default_factory=list, description="新建物体的id映射")
    created_paths: List[CreatedIdMapping] = Field(default_factory=list, description="新建路径的id映射")


class EditorMapAnnotationResponse(BaseRespEntity):
    """编辑器标注响应"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    map_id: int
    x: float
    y: float
    name: str
    angle: float
    type: str
    task_count: int = Field(0, description="关联该点位的有效任务数（用于删除前提示）")


class EditorMapPathResponse(BaseRespEntity):
    """编辑器路径响应"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    map_id: int
    start_annotation_id: int
    end_annotation_id: int
    name: str | None
    points: str | None


class EditorMapObjectResponse(BaseRespEntity):
    """编辑器物体响应"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    map_id: int
    type: str
    name: str | None
    x: float
    y: float
    width: float
    height: float
    points: str | None
    angle: float


class EditorMapDataResponse(BaseModel):
    """编辑器完整数据响应"""

    map: dict = Field(..., description="地图元数据")
    annotations: List[EditorMapAnnotationResponse] = Field(default_factory=list)
    paths: List[EditorMapPathResponse] = Field(default_factory=list)
    objects: List[EditorMapObjectResponse] = Field(default_factory=list)


class SceneMapConfigParseResponse(BaseModel):
    """ROS 地图配置文件(yaml)解析响应

    resolution 取自 yaml 中的 resolution 字段；
    start_point_x / start_point_y 取自 origin 数组的前两项。
    """

    resolution: float = Field(..., description="分辨率(m/px)")
    start_point_x: float = Field(..., description="扫图起始点X坐标(origin[0])")
    start_point_y: float = Field(..., description="扫图起始点Y坐标(origin[1])")
