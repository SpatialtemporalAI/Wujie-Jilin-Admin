#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
阿里云人脸库管理接口（后台，JWT 鉴权 + 权限校验）
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile

from core.config import settings
from core.response.response_schema import ResponseModel
from modules.admin.deps.auth.user_manager import current_user
from modules.admin.deps.auth.permission import require_permission

from modules.face.services.face_service import FaceService
from modules.face.schemas.face import (
    FaceDbCreate,
    FaceDbListResponse,
    FaceEntityCreate,
    FaceImageAddResponse,
    FaceSearchResponse,
    FaceDetectResponse,
)

logger = logging.getLogger(__name__)

face_router = APIRouter(
    prefix="/face",
    tags=["人脸库管理"],
    dependencies=[Depends(current_user)],
)


# ------------------------------ 人脸库 ------------------------------
@face_router.post(
    "/db",
    response_model=ResponseModel[FaceDbCreate],
    dependencies=[Depends(require_permission("face:db:create"))],
)
async def create_face_db(body: FaceDbCreate):
    """创建人脸库"""
    await FaceService.create_face_db(body.db_name)
    return ResponseModel(data=body, msg="创建成功")


@face_router.get(
    "/db/list",
    response_model=ResponseModel[FaceDbListResponse],
    dependencies=[Depends(require_permission("face:db:list"))],
)
async def list_face_dbs():
    """列出所有人脸库"""
    db_list = await FaceService.list_face_dbs()
    return ResponseModel(data=FaceDbListResponse(db_list=db_list))


# ------------------------------ 实体 ------------------------------
@face_router.post(
    "/entity",
    response_model=ResponseModel,
    dependencies=[Depends(require_permission("face:entity:add"))],
)
async def add_face_entity(body: FaceEntityCreate):
    """新增人脸实体"""
    db_name = body.db_name or settings.FACE.DEFAULT_DB_NAME
    entity_id = await FaceService.add_face_entity(db_name, body.entity_id)
    return ResponseModel(
        data={"db_name": db_name, "entity_id": entity_id}, msg="新增成功"
    )


@face_router.delete(
    "/entity",
    response_model=ResponseModel,
    dependencies=[Depends(require_permission("face:entity:delete"))],
)
async def delete_face_entity(
    entity_id: str = Query(..., description="实体标识"),
    db_name: Optional[str] = Query(None, description="人脸库名称，为空使用默认"),
):
    """删除人脸实体及其所有人脸图片"""
    db_name = db_name or settings.FACE.DEFAULT_DB_NAME
    await FaceService.delete_face_entity(db_name, entity_id)
    return ResponseModel(msg="删除成功")


# ------------------------------ 人脸图片 ------------------------------
@face_router.post(
    "/image",
    response_model=ResponseModel[FaceImageAddResponse],
    dependencies=[Depends(require_permission("face:image:add"))],
)
async def add_face_image(
    entity_id: str = Form(..., description="实体标识"),
    db_name: Optional[str] = Form(None, description="人脸库名称，为空使用默认"),
    file: UploadFile = File(..., description="人脸图片文件"),
):
    """上传人脸图片并入库，返回 face_id"""
    db_name = db_name or settings.FACE.DEFAULT_DB_NAME
    oss_url = await FaceService.upload_to_oss(file)
    face_id = await FaceService.add_face_image(db_name, entity_id, oss_url)
    return ResponseModel(
        data=FaceImageAddResponse(
            db_name=db_name, entity_id=entity_id, face_id=face_id
        ),
        msg="添加成功",
    )


@face_router.delete(
    "/image",
    response_model=ResponseModel,
    dependencies=[Depends(require_permission("face:image:delete"))],
)
async def delete_face(
    face_id: str = Query(..., description="阿里云人脸图片 ID"),
    db_name: Optional[str] = Query(None, description="人脸库名称，为空使用默认"),
):
    """删除单张人脸图片"""
    db_name = db_name or settings.FACE.DEFAULT_DB_NAME
    await FaceService.delete_face(db_name, face_id)
    return ResponseModel(msg="删除成功")


# ------------------------------ 搜索 / 检测 ------------------------------
@face_router.post(
    "/search",
    response_model=ResponseModel[FaceSearchResponse],
    dependencies=[Depends(require_permission("face:search"))],
)
async def search_face(
    file: UploadFile = File(..., description="待搜索的人脸图片"),
    db_name: Optional[str] = Form(None, description="人脸库名称，为空使用默认"),
    limit: int = Form(3, ge=1, le=10, description="返回的匹配数量上限"),
):
    """在指定人脸库中搜索匹配的人脸"""
    db_name = db_name or settings.FACE.DEFAULT_DB_NAME
    oss_url = await FaceService.upload_to_oss(file)
    results = await FaceService.search_face(db_name, oss_url, limit=limit)
    return ResponseModel(data=FaceSearchResponse(results=results))


@face_router.post(
    "/detect",
    response_model=ResponseModel[FaceDetectResponse],
    dependencies=[Depends(require_permission("face:detect"))],
)
async def detect_face(
    file: UploadFile = File(..., description="待检测的图片"),
    max_face_num: int = Form(10, ge=1, le=100, description="最大检测人脸数"),
):
    """检测图片中的人脸并返回人脸框"""
    oss_url = await FaceService.upload_to_oss(file)
    results = await FaceService.detect_face(oss_url, max_face_num=max_face_num)
    return ResponseModel(data=FaceDetectResponse(results=results))
