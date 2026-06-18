#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文件 preview 端点的 HMAC 签名 URL 工具

用途：让后端把"自带时效的图片 URL"推给外部服务（如导览服务/机器人），
无需对方额外携带鉴权信息，且密钥本身不暴露在 URL 中。

URL 形态：
    {BASE_URL}/admin/sys/file/{file_id}/preview?expires={unix_ts}&sig={hex}

签名规则：
    sig = HMAC-SHA256(secret, f"{file_id}:{expires}")

依赖 settings.SERVICE.INTERNAL_TOKEN 作为 HMAC 密钥；该字段为空时回退到非签名模式。
"""
from __future__ import annotations

import hashlib
import hmac
import time
from urllib.parse import quote

from core.config import settings


def _secret() -> str:
    return settings.SERVICE.INTERNAL_TOKEN or ""


def is_enabled() -> bool:
    """是否启用签名模式（INTERNAL_TOKEN 非空即启用）"""
    return bool(_secret())


def compute_sig(file_id: int, expires: int) -> str:
    """对 (file_id, expires) 计算 HMAC-SHA256 hex"""
    msg = f"{file_id}:{expires}".encode()
    return hmac.new(_secret().encode(), msg, hashlib.sha256).hexdigest()


def verify(file_id: int, expires: int, sig: str) -> bool:
    """校验签名 + 过期时间；任一字段缺失/超时/不匹配返回 False"""
    if not sig or not expires:
        return False
    if int(time.time()) > expires:
        return False
    expected = compute_sig(file_id, expires)
    return hmac.compare_digest(expected, sig)


def build_signed_url(file_id: int, ttl_seconds: int | None = None) -> str:
    """构造签名后的完整 preview URL

    ttl_seconds 未传时使用 settings.SERVICE.FILE_PREVIEW_TTL_SECONDS，再退回 600。
    """
    base_url = (settings.SERVICE.BASE_URL or "").rstrip("/")
    ttl = (
        ttl_seconds
        if ttl_seconds is not None
        else getattr(settings.SERVICE, "FILE_PREVIEW_TTL_SECONDS", 600)
    )
    expires = int(time.time()) + int(ttl)
    sig = compute_sig(file_id, expires)
    return (
        f"{base_url}/admin/sys/file/{file_id}/preview"
        f"?expires={expires}&sig={sig}"
    )
