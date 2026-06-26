#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database.db_manager import get_session
from core.response import ResponseModel, ResponsePageModel, response_base, ResponsePageDataModel
from app.models.common.page import PageRequest, get_page_params, get_paginated_results
from modules.admin.deps.auth.user_manager import current_user
from modules.admin.deps.auth.permission import require_any_permission
from modules.admin.services.sys.file_service import FileService
from modules.admin.schemas.sys.file import SysFileUploadResponse
from database.models.sys.user import SysUser
from modules.scene.services.scene_map_service import SceneMapService
from modules.scene.services.scene_map_nav_image_service import SceneMapNavImageService
from modules.scene.schemas.scene_map import (
    SceneMapCreate,
    SceneMapUpdate,
    SceneMapQueryParams,
    SceneMapResponseData,
)

scene_map_router = APIRouter(
    prefix="/map",
    tags=["场景管理/场景地图"],
    dependencies=[Depends(current_user)],
)


@scene_map_router.get(
    "/list",
    response_model=ResponsePageModel[SceneMapResponseData],
    summary="获取场景地图列表",
    dependencies=[
        Depends(
            require_any_permission(
                "scene:map:list",
                "scene:map-editor:list",
                "task:list",
            )
        )
    ],
)
async def get_map_list(
    query_params: SceneMapQueryParams = Depends(),
    page_params: PageRequest = Depends(get_page_params),
    user: SysUser = Depends(current_user),
    db: AsyncSession = Depends(get_session),
):
    """分页查询场景地图列表（含分组名称）"""
    items, total = await SceneMapService.get_list_with_group_name(db, query_params)

    pages = (total + page_params.page_size - 1) // page_params.page_size
    page_data = ResponsePageDataModel(
        records=items,
        page=page_params.page,
        page_size=page_params.page_size,
        total=total,
        total_pages=pages,
    )
    return response_base.page(data=page_data)


@scene_map_router.get(
    "/{map_id}",
    response_model=ResponseModel[SceneMapResponseData],
    summary="获取场景地图详情",
    dependencies=[Depends(require_any_permission("scene:map:detail", "scene:map-editor:list"))],
)
async def get_map(
    map_id: int,
    user: SysUser = Depends(current_user),
    db: AsyncSession = Depends(get_session),
):
    """获取场景地图详情"""
    map_obj = await SceneMapService.get(db, map_id)
    return response_base.success(data=SceneMapResponseData.model_validate(map_obj))


@scene_map_router.post(
    "/upload-image",
    response_model=ResponseModel[SysFileUploadResponse],
    summary="上传场景地图主图",
    dependencies=[Depends(require_any_permission("scene:map:add", "scene:map:edit"))],
)
async def upload_scene_map_image(
    file: UploadFile = File(..., description="图片文件"),
    include_image_info: bool = Query(False, description="是否返回图片宽高"),
    db: AsyncSession = Depends(get_session),
    user: SysUser = Depends(current_user),
):
    """上传场景地图主图（用于 image_id 字段）。

    权限要求 scene:map:add 或 scene:map:edit，与新增/编辑场景地图保持一致，
    避免依赖 sys:file:upload。底层调用 FileService.upload_file。
    """
    file_data = await file.read()
    sys_file = await FileService.upload_file(
        db=db,
        file_data=file_data,
        original_name=file.filename or "unknown",
        mime_type=file.content_type or "application/octet-stream",
        created_by=user.id,
    )
    await db.commit()

    response = SysFileUploadResponse.model_validate(sys_file)
    if include_image_info:
        width, height = FileService.get_image_dimensions(
            file_data, file.content_type or "application/octet-stream"
        )
        response.image_width = width
        response.image_height = height
    return response_base.success(data=response, msg="上传成功")


@scene_map_router.post(
    "/add",
    response_model=ResponseModel[SceneMapResponseData],
    summary="创建场景地图",
    dependencies=[Depends(require_any_permission("scene:map:add", "scene:map-editor:add"))],
)
async def create_map(
    map_create: SceneMapCreate,
    user: SysUser = Depends(current_user),
    db: AsyncSession = Depends(get_session),
):
    """创建场景地图"""
    map_obj = await SceneMapService.create(db, map_create)
    await db.commit()
    await db.refresh(map_obj)
    return response_base.success(data=SceneMapResponseData.model_validate(map_obj), msg="创建成功")


@scene_map_router.put(
    "/{map_id}",
    response_model=ResponseModel[SceneMapResponseData],
    summary="更新场景地图",
    dependencies=[Depends(require_any_permission("scene:map:edit", "scene:map-editor:edit"))],
)
async def update_map(
    map_id: int,
    map_update: SceneMapUpdate,
    user: SysUser = Depends(current_user),
    db: AsyncSession = Depends(get_session),
):
    """更新场景地图"""
    map_obj, image_id_changed = await SceneMapService.update(db, map_id, map_update)
    await db.commit()
    await db.refresh(map_obj)
    if image_id_changed:
        SceneMapNavImageService.schedule_regenerate(map_id, user.id)
    return response_base.success(data=SceneMapResponseData.model_validate(map_obj), msg="更新成功")


@scene_map_router.delete(
    "/{map_id}",
    response_model=ResponseModel,
    summary="删除场景地图",
    dependencies=[Depends(require_any_permission("scene:map:delete", "scene:map-editor:delete"))],
)
async def delete_map(
    map_id: int,
    user: SysUser = Depends(current_user),
    db: AsyncSession = Depends(get_session),
):
    """删除场景地图"""
    await SceneMapService.delete(db, map_id)
    await db.commit()
    return response_base.success(msg="删除成功")
