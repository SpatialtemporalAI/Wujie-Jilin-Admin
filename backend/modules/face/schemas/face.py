#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
阿里云人脸库管理 - 数据契约
无本地数据表，纯传输模型，直接使用阿里云 entity_id 作为实体标识
"""
from typing import List, Optional

from pydantic import BaseModel, Field


class FaceDbCreate(BaseModel):
    """创建人脸库请求"""

    db_name: str = Field(..., description="人脸库名称", max_length=128)


class FaceDbListResponse(BaseModel):
    """人脸库列表响应"""

    db_list: List[str] = Field(..., description="人脸库名称列表")


class FaceEntityCreate(BaseModel):
    """新增人脸实体请求"""

    db_name: Optional[str] = Field(
        None, description="人脸库名称，为空时使用默认人脸库"
    )
    entity_id: str = Field(..., description="实体标识（人物唯一 ID/名称）", max_length=128)


class FaceImageAddResponse(BaseModel):
    """人脸图片入库响应"""

    db_name: str = Field(..., description="所属人脸库名称")
    entity_id: str = Field(..., description="所属实体标识")
    face_id: str = Field(..., description="阿里云返回的人脸图片 ID")


class FaceSearchItem(BaseModel):
    """人脸搜索单项匹配结果"""

    entity_id: str = Field(..., description="匹配到的实体标识")
    confidence: float = Field(..., description="匹配置信度")


class FaceSearchResponse(BaseModel):
    """人脸搜索响应"""

    results: List[FaceSearchItem] = Field([], description="匹配结果列表（按置信度降序）")


class FaceDetectItem(BaseModel):
    """人脸检测单项结果"""

    face_rect: List[int] = Field(
        ..., description="人脸框 [x, y, width, height]"
    )
    face_probability: float = Field(..., description="人脸概率")


class FaceDetectResponse(BaseModel):
    """人脸检测响应"""

    results: List[FaceDetectItem] = Field([], description="检测到的人脸列表")
