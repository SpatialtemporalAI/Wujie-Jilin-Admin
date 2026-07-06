#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
机器人参数配置相关接口
"""
import logging
from fastapi import APIRouter, Depends, Path, Request, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from database.db_manager import get_session
from core.response.response_schema import (
    ResponseModel,
    ResponsePageModel,
    response_base,
)
from app.models.common.page import PageRequest, get_page_params, get_paginated_results
from core.decorators.operation_log import log_operation
from modules.admin.deps.auth.user_manager import current_user
from modules.admin.deps.auth.permission import require_permission
from database.models.sys.user import SysUser
from modules.admin.services.sys.file_service import FileService
from modules.admin.schemas.sys.file import SysFileUploadResponse

from modules.robot.services.robot_config_service import RobotConfigService
from modules.robot.schemas.robot_config import (
    RobotVoiceConfigSchema,
    RobotVoiceConfigResponse,
    RobotFaceRecognitionCreate,
    RobotFaceRecognitionUpdate,
    RobotFaceRecognitionResponse,
    TestWakeWordRequest,
    TestTTSRequest,
    RobotSpeedLevelUpdate,
    RobotBatteryThresholdUpdate,
    RobotVideoMonitoringControl,
    ConfigUpdateResponse,
)
from modules.grpc.config_client import VoiceConfigClient, VideoMonitoringClient
from core.storage import validate_file_size, validate_file_extension
from core.exception.errors import RequestError

# 人像上传限制（对齐阿里云 facebody 要求；人脸占比 64×64 由 facebody 校验）
ALLOWED_FACE_PHOTO_EXTS = ("jpg", "jpeg", "png")
MAX_FACE_PHOTO_SIZE = 5 * 1024 * 1024  # 5MB
MIN_FACE_PHOTO_DIM = 32  # 分辨率下限（>32）
MAX_FACE_PHOTO_DIM = 4096  # 分辨率上限（<4096）

# grpc_status → 前端展示文案（绿色 success）
_GRPC_MSG_MAP = {
    "synced": "保存成功",
    "pending_retry": "保存成功（设备同步待重试）",
    "disabled": "保存成功",
}

logger = logging.getLogger(__name__)

robot_config_router = APIRouter(
    prefix="/config", tags=["机器人参数配置"], dependencies=[Depends(current_user)]
)


# ==================== 语音合成配置 ====================


@robot_config_router.get(
    "/voice",
    response_model=ResponseModel[RobotVoiceConfigResponse],
)
async def get_voice_config(
    robot_id: int,
    db: AsyncSession = Depends(get_session),
):
    """
    获取语音合成配置
    """
    try:
        logger.info("获取语音合成配置接口被调用，robot_id: %d", robot_id)
        config = await RobotConfigService.get_voice_config(db, robot_id)
        response_data = RobotVoiceConfigResponse.model_validate(config)
        logger.info("获取语音合成配置接口成功")
        return response_base.success(data=response_data)
    except Exception as e:
        logger.error("获取语音合成配置接口失败: %s", str(e), exc_info=True)
        raise


@robot_config_router.post(
    "/voice",
    response_model=ResponseModel[RobotVoiceConfigResponse],
    dependencies=[Depends(require_permission("robot:config:edit"))],
)
@log_operation(module="robot", action="update", description="保存语音合成配置")
async def save_voice_config(
    request: Request,
    config_in: RobotVoiceConfigSchema,
    db: AsyncSession = Depends(get_session),
    user: SysUser = Depends(current_user),
):
    """
    保存语音合成配置
    """
    try:
        logger.info("保存语音合成配置接口被调用")
        config, grpc_status = await RobotConfigService.save_voice_config(db, config_in)
        response_data = RobotVoiceConfigResponse.model_validate(config)
        response_data.grpc_status = grpc_status
        logger.info("保存语音合成配置接口成功 grpc_status=%s", grpc_status)
        return response_base.success(
            data=response_data, msg=_GRPC_MSG_MAP.get(grpc_status, "保存成功")
        )
    except Exception as e:
        logger.error("保存语音合成配置接口失败: %s", str(e), exc_info=True)
        raise


@robot_config_router.post(
    "/voice/test-wake-word",
    response_model=ResponseModel,
    dependencies=[Depends(require_permission("robot:config:edit"))],
)
async def test_wake_word(
    body: TestWakeWordRequest,
    db: AsyncSession = Depends(get_session),
):
    """测试唤醒词（调用 gRPC TestWakeWord，让机器人按当前唤醒词模拟一次响应）

    测试按钮失败时直接返回 fail，不入重试队列（实时语义，用户等响应）。
    """
    logger.info(
        "测试唤醒词接口被调用，robot_id: %d, 文本: %s", body.robot_id, body.text
    )
    resp = await VoiceConfigClient.test_wake_word(
        robot_id=body.robot_id, wake_word=body.text
    )
    if resp.success:
        return response_base.success(msg=resp.message or "测试指令已下发")
    logger.warning(
        "测试唤醒词失败 robot_id=%s code_msg=%s", body.robot_id, resp.message
    )
    return response_base.fail(msg="测试失败，请确保机器人在线")


@robot_config_router.post(
    "/voice/test-tts",
    response_model=ResponseModel,
    dependencies=[Depends(require_permission("robot:config:edit"))],
)
async def test_tts(
    body: TestTTSRequest,
    db: AsyncSession = Depends(get_session),
):
    """测试TTS语音合成（调用 gRPC TestTTSConfig，按指定参数播报测试文本）

    测试按钮失败时直接返回 fail，不入重试队列（实时语义，用户等响应）。
    """
    logger.info(
        "测试TTS接口被调用，robot_id: %d, 音色: %s", body.robot_id, body.voice
    )
    resp = await VoiceConfigClient.test_tts(
        robot_id=body.robot_id,
        tts_voice=body.voice,
        tts_speed=body.speed,
        tts_volume=body.volume,
        text=body.text,
    )
    if resp.success:
        return response_base.success(msg=resp.message or "测试指令已下发")
    logger.warning(
        "测试TTS失败 robot_id=%s code_msg=%s", body.robot_id, resp.message
    )
    return response_base.fail(msg="测试失败，请确保机器人在线")


# ==================== 人脸识别TTS配置 ====================


@robot_config_router.post(
    "/face/upload",
    response_model=ResponseModel[SysFileUploadResponse],
    dependencies=[Depends(require_permission("robot:config:edit"))],
)
async def upload_face_photo(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_session),
    user: SysUser = Depends(current_user),
):
    """
    上传人脸识别人像
    """
    file_data = await file.read()
    validate_file_size(len(file_data), MAX_FACE_PHOTO_SIZE)
    validate_file_extension(file.filename or "unknown", ALLOWED_FACE_PHOTO_EXTS)
    width, height = FileService.get_image_dimensions(
        file_data, file.content_type or "application/octet-stream"
    )
    if width and height:
        if width <= MIN_FACE_PHOTO_DIM or height <= MIN_FACE_PHOTO_DIM:
            raise RequestError(
                msg=f"图像分辨率需大于 32×32 像素，当前 {width}×{height}"
            )
        if width >= MAX_FACE_PHOTO_DIM or height >= MAX_FACE_PHOTO_DIM:
            raise RequestError(
                msg=f"图像分辨率需小于 4096×4096 像素，当前 {width}×{height}"
            )
    sys_file = await FileService.upload_file(
        db=db,
        file_data=file_data,
        original_name=file.filename or "unknown",
        mime_type=file.content_type or "application/octet-stream",
        created_by=user.id,
    )
    await db.commit()
    return response_base.success(
        data=SysFileUploadResponse.model_validate(sys_file),
        msg="上传成功",
    )


@robot_config_router.get(
    "/face",
    response_model=ResponsePageModel[RobotFaceRecognitionResponse],
    dependencies=[Depends(require_permission("robot:config:list"))],
)
async def get_face_list(
    page_params: PageRequest = Depends(get_page_params),
    db: AsyncSession = Depends(get_session),
):
    """
    获取人脸识别TTS配置列表
    """
    try:
        logger.info("获取人脸识别TTS列表接口被调用")
        query = RobotConfigService.build_face_query()
        page_data = await get_paginated_results(
            db=db,
            page_params=page_params,
            query=query,
            schema=RobotFaceRecognitionResponse,
        )
        logger.info("获取人脸识别TTS列表接口成功，共 %d 条记录", page_data.total)
        return response_base.page(data=page_data)
    except Exception as e:
        logger.error("获取人脸识别TTS列表接口失败: %s", str(e), exc_info=True)
        raise


@robot_config_router.post(
    "/face",
    response_model=ResponseModel[RobotFaceRecognitionResponse],
    dependencies=[Depends(require_permission("robot:config:edit"))],
)
@log_operation(module="robot", action="create", description="创建人脸识别TTS配置")
async def create_face(
    request: Request,
    face_in: RobotFaceRecognitionCreate,
    db: AsyncSession = Depends(get_session),
    user: SysUser = Depends(current_user),
):
    """创建人脸识别TTS配置"""
    try:
        logger.info("创建人脸识别TTS配置接口被调用")
        face, grpc_status = await RobotConfigService.create_face(db, face_in)
        response_data = RobotFaceRecognitionResponse.model_validate(face)
        response_data.grpc_status = grpc_status
        logger.info("创建人脸识别TTS配置接口成功，ID: %d, grpc_status=%s", face.id, grpc_status)
        return response_base.success(
            data=response_data, msg=_GRPC_MSG_MAP.get(grpc_status, "创建成功")
        )
    except Exception as e:
        logger.error("创建人脸识别TTS配置接口失败: %s", str(e), exc_info=True)
        raise


@robot_config_router.put(
    "/face/{face_id}",
    response_model=ResponseModel[RobotFaceRecognitionResponse],
    dependencies=[Depends(require_permission("robot:config:edit"))],
)
@log_operation(module="robot", action="update", description="更新人脸识别TTS配置")
async def update_face(
    request: Request,
    face_in: RobotFaceRecognitionUpdate,
    face_id: int = Path(..., description="人脸识别配置ID"),
    db: AsyncSession = Depends(get_session),
    user: SysUser = Depends(current_user),
):
    """更新人脸识别TTS配置"""
    try:
        logger.info("更新人脸识别TTS配置接口被调用，ID: %d", face_id)
        face, grpc_status = await RobotConfigService.update_face(db, face_id, face_in)
        response_data = RobotFaceRecognitionResponse.model_validate(face)
        response_data.grpc_status = grpc_status
        logger.info("更新人脸识别TTS配置接口成功，ID: %d, grpc_status=%s", face_id, grpc_status)
        return response_base.success(
            data=response_data, msg=_GRPC_MSG_MAP.get(grpc_status, "更新成功")
        )
    except Exception as e:
        logger.error("更新人脸识别TTS配置接口失败: %s", str(e), exc_info=True)
        raise


@robot_config_router.delete(
    "/face/{face_id}",
    response_model=ResponseModel[ConfigUpdateResponse],
    dependencies=[Depends(require_permission("robot:config:edit"))],
)
@log_operation(module="robot", action="delete", description="删除人脸识别TTS配置")
async def delete_face(
    request: Request,
    face_id: int = Path(..., description="人脸识别配置ID"),
    db: AsyncSession = Depends(get_session),
    user: SysUser = Depends(current_user),
):
    """删除人脸识别TTS配置"""
    try:
        logger.info("删除人脸识别TTS配置接口被调用，ID: %d", face_id)
        grpc_status = await RobotConfigService.delete_face(db, face_id)
        logger.info("删除人脸识别TTS配置接口成功，ID: %d, grpc_status=%s", face_id, grpc_status)
        return response_base.success(
            data=ConfigUpdateResponse(grpc_status=grpc_status),
            msg=_GRPC_MSG_MAP.get(grpc_status, "删除成功"),
        )
    except Exception as e:
        logger.error("删除人脸识别TTS配置接口失败: %s", str(e), exc_info=True)
        raise


# ==================== 行走速度 / 电量阈值配置 ====================


@robot_config_router.put(
    "/speed-level/{robot_id}",
    response_model=ResponseModel[ConfigUpdateResponse],
    dependencies=[Depends(require_permission("robot:config:edit"))],
)
@log_operation(module="robot", action="update", description="更新机器人行走速度")
async def update_speed_level(
    request: Request,
    payload: RobotSpeedLevelUpdate,
    robot_id: int = Path(..., description="机器人ID"),
    db: AsyncSession = Depends(get_session),
    user: SysUser = Depends(current_user),
):
    """更新机器人行走速度等级（参数配置专用，权限 robot:config:edit）"""
    try:
        logger.info(
            "更新机器人行走速度接口被调用，robot_id: %d, speed_level: %s",
            robot_id,
            payload.speed_level,
        )
        _, grpc_status = await RobotConfigService.update_speed_level(
            db, robot_id, payload.speed_level
        )
        logger.info(
            "更新机器人行走速度接口成功，robot_id: %d, grpc_status=%s",
            robot_id,
            grpc_status,
        )
        return response_base.success(
            data=ConfigUpdateResponse(grpc_status=grpc_status),
            msg=_GRPC_MSG_MAP.get(grpc_status, "保存成功"),
        )
    except Exception as e:
        logger.error("更新机器人行走速度接口失败: %s", str(e), exc_info=True)
        raise


@robot_config_router.put(
    "/battery-threshold/{robot_id}",
    response_model=ResponseModel[ConfigUpdateResponse],
    dependencies=[Depends(require_permission("robot:config:edit"))],
)
@log_operation(module="robot", action="update", description="更新机器人电量报警阈值")
async def update_battery_threshold(
    request: Request,
    payload: RobotBatteryThresholdUpdate,
    robot_id: int = Path(..., description="机器人ID"),
    db: AsyncSession = Depends(get_session),
    user: SysUser = Depends(current_user),
):
    """更新机器人电量报警阈值（参数配置专用，权限 robot:config:edit）"""
    try:
        logger.info(
            "更新机器人电量阈值接口被调用，robot_id: %d, battery_threshold: %d",
            robot_id,
            payload.battery_threshold,
        )
        _, grpc_status = await RobotConfigService.update_battery_threshold(
            db, robot_id, payload.battery_threshold
        )
        logger.info(
            "更新机器人电量阈值接口成功，robot_id: %d, grpc_status=%s",
            robot_id,
            grpc_status,
        )
        return response_base.success(
            data=ConfigUpdateResponse(grpc_status=grpc_status),
            msg=_GRPC_MSG_MAP.get(grpc_status, "保存成功"),
        )
    except Exception as e:
        logger.error("更新机器人电量阈值接口失败: %s", str(e), exc_info=True)
        raise


# ==================== 视频监控启停 ====================


@robot_config_router.post(
    "/video-monitoring/{robot_id}",
    response_model=ResponseModel,
    dependencies=[Depends(require_permission("robot:config:edit"))],
)
@log_operation(module="robot", action="update", description="视频监控启停")
async def control_video_monitoring(
    request: Request,
    payload: RobotVideoMonitoringControl,
    robot_id: int = Path(..., description="机器人ID"),
    db: AsyncSession = Depends(get_session),
    user: SysUser = Depends(current_user),
):
    """启动/停止视频监控（gRPC NotifyVideoMonitoringChanged → 机器人 middleware）

    实时控制：失败直接返回 fail，不入重试队列（用户等待即时响应）。
    """
    action = "启动" if payload.enabled else "停止"
    logger.info(
        "视频监控%s接口被调用 robot_id=%d", action, robot_id
    )
    resp = await VideoMonitoringClient.notify_video_monitoring_changed(
        robot_id=robot_id, enabled=payload.enabled
    )
    if resp.success:
        return response_base.success(msg=resp.message or f"{action}指令已下发")
    logger.warning(
        "视频监控%s失败 robot_id=%s msg=%s", action, robot_id, resp.message
    )
    return response_base.fail(msg=f"{action}失败，请确保机器人在线")
