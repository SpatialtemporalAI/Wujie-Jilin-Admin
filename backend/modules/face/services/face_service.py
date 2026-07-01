#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
阿里云人脸库管理服务
- 密钥从 settings.FACE（.env）读取，懒加载 Client / FileUtils 并缓存
- facebody SDK 与 viapi FileUtils 均为同步阻塞，统一用 asyncio.to_thread 包装
- 失败抛 core.exception.errors 异常，由端点层统一成 ResponseModel
"""
from __future__ import annotations

import asyncio
import logging
import os
import re
import tempfile
from functools import lru_cache
from typing import List

from fastapi import UploadFile

from core.config import settings
from core.exception.errors import GatewayError, RequestError, ServerError
from alibabacloud_facebody20191230.client import Client
from alibabacloud_facebody20191230.models import (
    AddFaceEntityRequest,
    AddFaceRequest,
    CreateFaceDbRequest,
    DeleteFaceEntityRequest,
    DeleteFaceRequest,
    DetectFaceRequest,
    GetFaceEntityRequest,
    ListFaceDbsRequest,
    ListFaceEntitiesRequest,
    SearchFaceRequest,
)
from alibabacloud_tea_openapi.models import Config
from alibabacloud_tea_util.models import RuntimeOptions
from viapi.fileutils import FileUtils

logger = logging.getLogger(__name__)

_runtime_options = RuntimeOptions()

# 阿里云 facebody 常见错误码 → 中文友好提示（命中则用提示代替英文原始信息）
_FACE_ERROR_HINT = {
    "InvalidImage.NotFoundFace": "未在图片中检测到人脸，请使用清晰正面的真人照片",
    "InvalidImage.DownloadError": "图片下载失败，请重新上传后再试",
    "InvalidImage.DecodeError": "图片解析失败，请更换为清晰的 JPG/PNG 图片",
    "InvalidImage.Format": "图片格式不支持，请更换为 JPG/PNG 图片",
    "InvalidImage.URL": "图片地址无效，请重新上传图片",
    "EntityNotExist": "人脸实体不存在",
    "DataNotExist": "人脸实体或图片不存在",
    "DBNameNotExist": "人脸库不存在",
    "EntityIdAlreadyExist": "人脸实体已存在",
    "FaceCountExceed": "单个人脸图片数量已达上限",
    "FaceImageCountExceed": "单个人脸图片数量已达上限",
    "ExceedEntityLimit": "人脸实体数量已达上限",
    "InvalidParameterValue": "请求参数不合法",
}

# 抹掉阿里云 message 里 [pk=...,tag=viapi:default] 这类内部噪声前缀
_FACE_ERROR_NOISE_RE = re.compile(r"^\[[^\]]*\]\s*")


def _describe_aliyun_error(exc: Exception) -> str:
    """解析阿里云 facebody / viapi 异常，返回「中文提示（错误码：XXX）」形式。

    SDK 抛出的 TeaException 带有 code / message / statusCode 等属性；命中已知错误码时
    给出中文友好提示，其余情况回退到清洗后的 message 或 str(exc)，避免把整个
    Response 字典原样抛给前端。
    """
    code = getattr(exc, "code", None) or getattr(exc, "Code", None)
    message = getattr(exc, "message", None) or getattr(exc, "Message", None)
    if message and isinstance(message, str):
        message = _FACE_ERROR_NOISE_RE.sub("", message).strip()

    hint = _FACE_ERROR_HINT.get(code) if code else None

    if hint and code:
        return f"{hint}（错误码：{code}）"
    if message and code:
        return f"{message}（错误码：{code}）"
    if hint:
        return hint
    if message:
        return message
    return str(exc)


def _ensure_enabled() -> None:
    """校验人脸识别已启用且密钥完整"""
    if not settings.FACE.ENABLED:
        raise ServerError(msg="阿里云人脸识别未启用（FACE__ENABLED=false）")
    if not settings.FACE.ACCESS_KEY_ID or not settings.FACE.ACCESS_KEY_SECRET:
        raise ServerError(
            msg="阿里云人脸识别密钥未配置（FACE__ACCESS_KEY_ID / FACE__ACCESS_KEY_SECRET）"
        )


@lru_cache(maxsize=1)
def get_client() -> Client:
    """构造并缓存 facebody Client"""
    _ensure_enabled()
    config = Config(
        access_key_id=settings.FACE.ACCESS_KEY_ID,
        access_key_secret=settings.FACE.ACCESS_KEY_SECRET,
        endpoint=settings.FACE.ENDPOINT,
        region_id=settings.FACE.REGION_ID,
    )
    return Client(config)


@lru_cache(maxsize=1)
def get_file_utils() -> FileUtils:
    """构造并缓存 viapi FileUtils（本地文件上传 OSS）"""
    _ensure_enabled()
    return FileUtils(settings.FACE.ACCESS_KEY_ID, settings.FACE.ACCESS_KEY_SECRET)


class FaceService:
    """阿里云人脸库管理服务"""

    # ------------------------------ OSS 上传 ------------------------------
    @staticmethod
    async def _upload_bytes_to_oss(file_data: bytes, ext: str) -> str:
        """把图片字节写入临时文件，经 viapi FileUtils 上传到阿里云 OSS，返回可访问 URL"""
        _ensure_enabled()
        suffix = f".{ext.lstrip('.')}" if ext else ".jpg"
        tmp_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(file_data)
                tmp_path = tmp.name
            file_utils = get_file_utils()
            file_type = suffix.lstrip(".") or "jpg"
            oss_url = await asyncio.to_thread(
                file_utils.get_oss_url, tmp_path, file_type, True
            )
            if not oss_url:
                raise GatewayError(msg="上传文件到阿里云 OSS 失败")
            return oss_url
        except (ServerError, GatewayError, RequestError):
            raise
        except Exception as exc:
            logger.error(
                "上传文件到阿里云 OSS 失败: %s | 原始异常: %s",
                _describe_aliyun_error(exc),
                exc,
            )
            raise GatewayError(
                msg=f"上传文件到阿里云 OSS 失败：{_describe_aliyun_error(exc)}"
            ) from exc
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

    @staticmethod
    async def upload_to_oss(file: UploadFile) -> str:
        """把上传文件写入临时文件，经 viapi FileUtils 上传到阿里云 OSS，返回可访问 URL"""
        _ensure_enabled()
        try:
            data = await file.read()
        except Exception as exc:
            logger.error("读取上传文件失败: %s", exc)
            raise RequestError(msg="读取上传文件失败") from exc
        ext = os.path.splitext(file.filename or "")[1].lstrip(".") or "jpg"
        return await FaceService._upload_bytes_to_oss(data, ext)

    @staticmethod
    async def upload_bytes_to_oss(file_data: bytes, ext: str) -> str:
        """把图片字节（如本地存储读回的）上传到阿里云 OSS，返回可访问 URL（供其它模块复用）"""
        return await FaceService._upload_bytes_to_oss(file_data, ext)

    # ------------------------------ 人脸库 ------------------------------
    @staticmethod
    async def create_face_db(db_name: str) -> str:
        def _call() -> None:
            client = get_client()
            request = CreateFaceDbRequest(name=db_name)
            client.create_face_db_with_options(request, _runtime_options)

        try:
            await asyncio.to_thread(_call)
            return db_name
        except (ServerError, GatewayError):
            raise
        except Exception as exc:
            logger.error("创建人脸库失败: %s | 原始异常: %s", _describe_aliyun_error(exc), exc)
            raise GatewayError(msg=f"创建人脸库失败: {_describe_aliyun_error(exc)}") from exc

    @staticmethod
    async def list_face_dbs() -> List[str]:
        def _call() -> List[str]:
            client = get_client()
            request = ListFaceDbsRequest()
            response = client.list_face_dbs_with_options(request, _runtime_options)
            body_data = response.body.data if response.body else None
            if not body_data or not body_data.db_list:
                return []
            return [db.name for db in body_data.db_list]

        try:
            return await asyncio.to_thread(_call)
        except (ServerError, GatewayError):
            raise
        except Exception as exc:
            logger.error("查询人脸库列表失败: %s | 原始异常: %s", _describe_aliyun_error(exc), exc)
            raise GatewayError(msg=f"查询人脸库列表失败: {_describe_aliyun_error(exc)}") from exc

    # ------------------------------ 实体 ------------------------------
    @staticmethod
    async def add_face_entity(db_name: str, entity_id: str) -> str:
        def _call() -> str:
            client = get_client()
            request = AddFaceEntityRequest(db_name=db_name, entity_id=entity_id)
            client.add_face_entity_with_options(request, _runtime_options)
            return entity_id

        try:
            return await asyncio.to_thread(_call)
        except (ServerError, GatewayError):
            raise
        except Exception as exc:
            logger.error("新增人脸实体失败: %s | 原始异常: %s", _describe_aliyun_error(exc), exc)
            raise GatewayError(msg=f"新增人脸实体失败: {_describe_aliyun_error(exc)}") from exc

    @staticmethod
    async def delete_face_entity(db_name: str, entity_id: str) -> None:
        def _call() -> None:
            client = get_client()
            request = DeleteFaceEntityRequest(db_name=db_name, entity_id=entity_id)
            client.delete_face_entity_with_options(request, _runtime_options)

        try:
            await asyncio.to_thread(_call)
        except (ServerError, GatewayError):
            raise
        except Exception as exc:
            logger.error("删除人脸实体失败: %s | 原始异常: %s", _describe_aliyun_error(exc), exc)
            raise GatewayError(msg=f"删除人脸实体失败: {_describe_aliyun_error(exc)}") from exc

    @staticmethod
    async def list_face_entities(
        db_name: str, offset: int = 0, limit: int = 10
    ) -> dict:
        """分页查询人脸库下的实体，返回 {entities, total_count}"""

        def _call() -> dict:
            client = get_client()
            request = ListFaceEntitiesRequest(
                db_name=db_name, offset=offset, limit=limit
            )
            response = client.list_face_entities_with_options(
                request, _runtime_options
            )
            body_data = response.body.data if response.body else None
            entities: List[dict] = []
            if body_data and body_data.entities:
                for e in body_data.entities:
                    entities.append(
                        {
                            "entity_id": e.entity_id,
                            "db_name": e.db_name,
                            "face_count": e.face_count,
                            "labels": e.labels,
                            "created_at": e.created_at,
                            "updated_at": e.updated_at,
                        }
                    )
            total_count = getattr(body_data, "total_count", None) or 0
            return {"entities": entities, "total_count": total_count}

        try:
            return await asyncio.to_thread(_call)
        except (ServerError, GatewayError):
            raise
        except Exception as exc:
            logger.error("查询人脸实体列表失败: %s | 原始异常: %s", _describe_aliyun_error(exc), exc)
            raise GatewayError(msg=f"查询人脸实体列表失败: {_describe_aliyun_error(exc)}") from exc

    @staticmethod
    async def get_face_entity(db_name: str, entity_id: str) -> dict:
        """查询单个实体及其所有人脸图片 face_id"""

        def _call() -> dict:
            client = get_client()
            request = GetFaceEntityRequest(db_name=db_name, entity_id=entity_id)
            response = client.get_face_entity_with_options(
                request, _runtime_options
            )
            body_data = response.body.data if response.body else None
            faces: List[dict] = []
            if body_data and body_data.faces:
                faces = [{"face_id": f.face_id} for f in body_data.faces]
            return {
                "db_name": body_data.db_name if body_data else db_name,
                "entity_id": entity_id,
                "labels": body_data.labels if body_data else None,
                "faces": faces,
            }

        try:
            return await asyncio.to_thread(_call)
        except (ServerError, GatewayError):
            raise
        except Exception as exc:
            logger.error("查询人脸实体详情失败: %s | 原始异常: %s", _describe_aliyun_error(exc), exc)
            raise GatewayError(msg=f"查询人脸实体详情失败: {_describe_aliyun_error(exc)}") from exc

    # ------------------------------ 人脸图片 ------------------------------
    @staticmethod
    async def add_face_image(db_name: str, entity_id: str, oss_url: str) -> str:
        def _call() -> str:
            client = get_client()
            request = AddFaceRequest(
                db_name=db_name, entity_id=entity_id, image_url=oss_url
            )
            response = client.add_face_with_options(request, _runtime_options)
            body_data = response.body.data if response.body else None
            if body_data and body_data.face_id:
                return body_data.face_id
            raise GatewayError(msg="添加人脸图片未返回 face_id")

        try:
            return await asyncio.to_thread(_call)
        except (ServerError, GatewayError):
            raise
        except Exception as exc:
            logger.error("添加人脸图片失败: %s | 原始异常: %s", _describe_aliyun_error(exc), exc)
            raise GatewayError(msg=f"添加人脸图片失败: {_describe_aliyun_error(exc)}") from exc

    @staticmethod
    async def delete_face(db_name: str, face_id: str) -> None:
        def _call() -> None:
            client = get_client()
            request = DeleteFaceRequest(db_name=db_name, face_id=face_id)
            client.delete_face_with_options(request, _runtime_options)

        try:
            await asyncio.to_thread(_call)
        except (ServerError, GatewayError):
            raise
        except Exception as exc:
            logger.error("删除人脸图片失败: %s | 原始异常: %s", _describe_aliyun_error(exc), exc)
            raise GatewayError(msg=f"删除人脸图片失败: {_describe_aliyun_error(exc)}") from exc

    # ------------------------------ 搜索 / 检测 ------------------------------
    @staticmethod
    async def search_face(db_name: str, oss_url: str, limit: int = 3) -> List[dict]:
        def _call() -> List[dict]:
            client = get_client()
            request = SearchFaceRequest(
                db_name=db_name, image_url=oss_url, limit=limit
            )
            response = client.search_face_with_options(request, _runtime_options)
            results: List[dict] = []
            body_data = response.body.data if response.body else None
            if body_data and body_data.match_list:
                for face_item in body_data.match_list[0].face_items[:limit]:
                    results.append(
                        {
                            "entity_id": face_item.entity_id,
                            "confidence": face_item.confidence,
                        }
                    )
            return results

        try:
            return await asyncio.to_thread(_call)
        except (ServerError, GatewayError):
            raise
        except Exception as exc:
            logger.error("人脸搜索失败: %s | 原始异常: %s", _describe_aliyun_error(exc), exc)
            raise GatewayError(msg=f"人脸搜索失败: {_describe_aliyun_error(exc)}") from exc

    @staticmethod
    async def detect_face(oss_url: str, max_face_num: int = 10) -> List[dict]:
        def _call() -> List[dict]:
            client = get_client()
            request = DetectFaceRequest(
                image_url=oss_url,
                landmark=False,
                quality=False,
                pose=False,
                max_face_number=max_face_num,
            )
            response = client.detect_face_with_options(request, _runtime_options)
            results: List[dict] = []
            body_data = response.body.data if response.body else None
            if body_data:
                for i in range(body_data.face_count):
                    results.append(
                        {
                            "face_rect": body_data.face_rectangles[i],
                            "face_probability": body_data.face_probability_list[i],
                        }
                    )
            return results

        try:
            return await asyncio.to_thread(_call)
        except (ServerError, GatewayError):
            raise
        except Exception as exc:
            logger.error("人脸检测失败: %s | 原始异常: %s", _describe_aliyun_error(exc), exc)
            raise GatewayError(msg=f"人脸检测失败: {_describe_aliyun_error(exc)}") from exc
