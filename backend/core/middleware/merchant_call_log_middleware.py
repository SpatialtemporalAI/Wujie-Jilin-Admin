#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
商户开放 API 调用日志中间件
自动捕获所有 /openapi/v1/* 的调用并落库（含鉴权失败），全程脱敏。

脱敏策略：
- api_key 经 mask_api_key 掩码后存储；X-Signature / X-Timestamp / X-Nonce 绝不入库
- 请求体、响应体经 mask_secret_fields 清洗凭证字段后再存储
- 响应体超长截断
"""
import json
import logging
import time
from typing import Callable

from starlette.background import BackgroundTask
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from core.security.mask import mask_api_key, mask_secret_fields
from core.utils.ip_utils import get_real_client_ip

logger = logging.getLogger(__name__)

MAX_RESULT_LENGTH = 2000
OPENAPI_PREFIX = "/openapi/v1/"


async def _capture_body(request: Request) -> str | None:
    """异步读取并脱敏请求体。

    Starlette 首次读取 body 后会缓存，不影响后续 endpoint / 鉴权依赖再次读取。
    """
    try:
        body_bytes = await request.body()
    except Exception:
        return None
    return _serialize_body(request, body_bytes)


def _serialize_body(request: Request, body_bytes: bytes | None) -> str | None:
    try:
        params: dict = {}
        if request.query_params:
            params["query"] = dict(request.query_params)
        if body_bytes:
            try:
                parsed = json.loads(body_bytes)
                params["body"] = mask_secret_fields(parsed)
            except (json.JSONDecodeError, UnicodeDecodeError):
                text = body_bytes.decode("utf-8", errors="replace")
                params["body"] = text[:MAX_RESULT_LENGTH]
        if not params:
            return None
        return json.dumps(params, ensure_ascii=False)
    except Exception:
        return None


def _read_response_body_fast(response: Response) -> tuple[str | None, bool, str | None]:
    """读取响应体，返回 (脱敏后文本, success, error_msg)"""
    try:
        body = getattr(response, "body", None)
        if not body:
            return None, False, None
        text = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else str(body)
        if len(text) > MAX_RESULT_LENGTH:
            text = text[:MAX_RESULT_LENGTH] + "...(truncated)"

        success = False
        error_msg: str | None = None
        try:
            parsed = json.loads(text)
            masked = mask_secret_fields(parsed)
            text = json.dumps(masked, ensure_ascii=False)
            if isinstance(parsed, dict):
                # 统一响应结构 { code, msg, data }
                code = parsed.get("code")
                success = code == 200
                if not success and parsed.get("msg"):
                    error_msg = str(parsed.get("msg"))[:500]
        except (json.JSONDecodeError, ValueError):
            pass
        return text, success, error_msg
    except Exception:
        return None, False, None


def _derive_action(path: str) -> str:
    """从 /openapi/v1/<action> 提取动作名"""
    try:
        return path.rstrip("/").split("/")[-1]
    except Exception:
        return ""


async def _write_call_log(
    api_key_masked: str,
    raw_api_key: str,
    method: str,
    path: str,
    action: str,
    ip: str | None,
    request_params: str | None,
    response_code: int | None,
    response_result: str | None,
    success: bool,
    elapsed_ms: float | None,
    error_msg: str | None,
):
    """异步写入调用日志到数据库，在响应发送后由 BackgroundTask 触发"""
    try:
        from database import get_session
        from database.models.business.merchant_call_log import MerchantCallLog
        from modules.merchant.services.merchant_service import MerchantService

        merchant_id = None
        merchant_name = None
        merchant_code = None
        if raw_api_key:
            async for db in get_session():
                merchant = await MerchantService.get_by_api_key(db, raw_api_key)
                if merchant:
                    merchant_id = merchant.id
                    merchant_name = merchant.name
                    merchant_code = merchant.code
                break

        async for db in get_session():
            log_entry = MerchantCallLog(
                merchant_id=merchant_id,
                merchant_name=merchant_name,
                merchant_code=merchant_code,
                api_key_masked=api_key_masked,
                method=method,
                path=path,
                action=action,
                ip=ip,
                request_params=request_params,
                response_code=response_code,
                response_result=response_result,
                success=success,
                elapsed_ms=elapsed_ms,
                error_msg=error_msg,
            )
            db.add(log_entry)
            await db.commit()
    except Exception as e:
        logger.error("写入商户调用日志失败: %s", e)


class MerchantCallLogMiddleware(BaseHTTPMiddleware):
    """自动记录所有商户开放 API（/openapi/v1/*）的调用日志"""

    async def dispatch(self, request: Request, call_next: Callable):
        path = request.url.path

        if not path.startswith(OPENAPI_PREFIX):
            return await call_next(request)

        start = time.monotonic()

        raw_api_key = request.headers.get("X-Api-Key", "") or ""
        api_key_masked = mask_api_key(raw_api_key)
        ip = get_real_client_ip(request)
        request_params = await _capture_body(request)

        response = await call_next(request)

        elapsed_ms = (time.monotonic() - start) * 1000
        response_result, body_success, body_error = _read_response_body_fast(response)

        # success：HTTP 2xx 且响应体业务码 == 200（无响应体时以 HTTP 状态为准）
        http_ok = 200 <= (response.status_code or 0) < 400
        if response_result:
            success = body_success
        else:
            success = http_ok
        error_msg = body_error if not success else None

        response.background = BackgroundTask(
            _write_call_log,
            api_key_masked=api_key_masked,
            raw_api_key=raw_api_key,
            method=request.method,
            path=path,
            action=_derive_action(path),
            ip=ip,
            request_params=request_params,
            response_code=response.status_code,
            response_result=response_result,
            success=success,
            elapsed_ms=elapsed_ms,
            error_msg=error_msg,
        )

        return response
