#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database.db_manager import get_session
from core.response import ResponseModel, response_base
from modules.admin.deps.auth.user_manager import current_user
from modules.admin.deps.auth.permission import require_any_permission
from modules.admin.services.sys.file_service import FileService
from modules.admin.schemas.sys.file import SysFileUploadResponse
from database.models.sys.user import SysUser
from modules.scene.services.scene_map_editor_service import SceneMapEditorService
from modules.scene.services.scene_map_nav_image_service import SceneMapNavImageService
from modules.scene.schemas.scene_map_editor import (
    EditorSaveRequest,
    EditorSaveResponse,
    EditorMapDataResponse,
    EditorMapAnnotationResponse,
    EditorMapPathResponse,
    EditorMapObjectResponse,
    SceneMapConfigParseResponse,
)
from modules.scene.schemas.scene_map import SceneMapResponseData

scene_map_editor_router = APIRouter(
    prefix="/map/{map_id}/editor",
    tags=["场景管理/地图编辑器"],
    dependencies=[Depends(current_user)],
)

# 地图编辑器菜单下"不依赖 map_id"的接口（如新增场景时的图片上传）
# 与 scene_map_router 的 /upload-image 严格分离，使用 scene:map-editor:* 权限
scene_map_editor_public_router = APIRouter(
    prefix="/map-editor",
    tags=["场景管理/地图编辑器"],
    dependencies=[Depends(current_user)],
)


@scene_map_editor_router.get(
    "/data",
    response_model=ResponseModel[EditorMapDataResponse],
    summary="获取编辑器完整数据",
    dependencies=[Depends(require_any_permission("scene:map-editor:list", "scene:map:list"))],
)
async def get_editor_data(
    map_id: int,
    user: SysUser = Depends(current_user),
    db: AsyncSession = Depends(get_session),
):
    """获取地图编辑器所需的完整数据（地图元数据 + 标注 + 路径 + 物体）"""
    map_obj = await SceneMapEditorService.get_editor_data(db, map_id)

    data = EditorMapDataResponse(
        map=SceneMapResponseData.model_validate(map_obj).model_dump(),
        annotations=[
            EditorMapAnnotationResponse.model_validate(a)
            for a in map_obj.annotations
        ],
        paths=[
            EditorMapPathResponse.model_validate(p)
            for p in map_obj.paths
        ],
        objects=[
            EditorMapObjectResponse.model_validate(o)
            for o in map_obj.objects
        ],
    )
    return response_base.success(data=data)


@scene_map_editor_router.post(
    "/save",
    response_model=ResponseModel[EditorSaveResponse],
    summary="批量保存编辑器数据",
    dependencies=[Depends(require_any_permission("scene:map-editor:edit", "scene:map:edit"))],
)
async def save_editor_data(
    map_id: int,
    save_request: EditorSaveRequest,
    user: SysUser = Depends(current_user),
    db: AsyncSession = Depends(get_session),
):
    """批量保存编辑器数据（标注、路径、物体的增删改），返回新建元素的id映射"""
    result = await SceneMapEditorService.save_editor_data(db, map_id, save_request)
    await db.commit()
    SceneMapNavImageService.schedule_regenerate(map_id, user.id)
    return response_base.success(data=result, msg="保存成功")


@scene_map_editor_public_router.post(
    "/upload-image",
    response_model=ResponseModel[SysFileUploadResponse],
    summary="上传场景地图主图（地图编辑器入口）",
    dependencies=[Depends(require_any_permission("scene:map-editor:add", "scene:map-editor:edit"))],
)
async def upload_scene_map_editor_image(
    file: UploadFile = File(..., description="图片文件"),
    include_image_info: bool = Query(False, description="是否返回图片宽高"),
    db: AsyncSession = Depends(get_session),
    user: SysUser = Depends(current_user),
):
    """地图编辑器新增/编辑场景时上传主图。

    权限要求 scene:map-editor:add 或 scene:map-editor:edit，与地图编辑器菜单一致，
    与场景地图菜单的 /scene/map/upload-image 严格分离。
    底层调用 FileService.upload_file，不依赖 sys:file:upload。
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


@scene_map_editor_public_router.post(
    "/parse-map-config",
    response_model=ResponseModel[SceneMapConfigParseResponse],
    summary="解析 ROS 地图配置文件(yaml)",
    dependencies=[Depends(require_any_permission("scene:map-editor:add", "scene:map-editor:edit"))],
)
async def parse_scene_map_config(
    file: UploadFile = File(..., description="ROS 地图配置文件(yaml)"),
    user: SysUser = Depends(current_user),
):
    """解析 ROS 地图配置文件(yaml)，回显分辨率与扫图起始点。

    仅做读取解析，不落库、不依赖任何数据库会话：
    - ``resolution`` 取自 yaml 中的 resolution 字段（必须存在）
    - ``start_point_x`` / ``start_point_y`` 取自 origin 数组前两项（必须存在）

    权限要求 scene:map-editor:add 或 scene:map-editor:edit，与地图编辑器新增/编辑场景一致。
    """
    file_data = await file.read()
    data = await SceneMapEditorService.parse_map_config(file_data)
    return response_base.success(data=data, msg="解析成功")
