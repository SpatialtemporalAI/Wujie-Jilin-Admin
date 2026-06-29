#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
商户开放 API 鉴权依赖（HMAC 签名）

校验流程：
1. 解析请求头 X-Api-Key / X-Timestamp / X-Nonce / X-Signature
2. 校验时间戳新鲜度（± SIGN_TTL_SECONDS）
3. 查询商户并校验启用状态，解密 api_secret
4. 读取请求体并验签（HMAC-SHA256）
5. nonce 防重放（Redis SET NX EX，验签通过后写入）
"""
import logging
import time

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from database.db_manager import get_session
from database.models.business.merchant import Merchant
from core.config import settings
from core.exception.errors import TokenError, ForbiddenError
from core.redis import get_redis_util
from modules.merchant.services.merchant_service import MerchantService
from modules.merchant.services.api_key_service import ApiKeyService

logger = logging.getLogger(__name__)


async def get_current_merchant(
    request: Request,
    db: AsyncSession = Depends(get_session),
) -> Merchant:
    """解析并校验商户 HMAC 签名，返回商户对象"""
    api_key = request.headers.get("X-Api-Key", "")
    timestamp = request.headers.get("X-Timestamp", "")
    nonce = request.headers.get("X-Nonce", "")
    signature = request.headers.get("X-Signature", "")

    if not all([api_key, timestamp, nonce, signature]):
        raise TokenError(msg="缺少鉴权请求头（X-Api-Key/X-Timestamp/X-Nonce/X-Signature）")

    # 时间戳新鲜度
    try:
        ts = int(timestamp)
    except (TypeError, ValueError):
        raise TokenError(msg="时间戳格式非法")
    skew = abs(int(time.time()) - ts)
    if skew > settings.MERCHANT.SIGN_TTL_SECONDS:
        raise TokenError(msg="请求时间戳已过期")

    # 查询商户
    merchant = await MerchantService.get_by_api_key(db, api_key)
    if not merchant:
        raise TokenError(msg="无效的 API Key")
    if not merchant.status:
        raise ForbiddenError(msg="商户已被禁用")

    # 解密 api_secret
    try:
        api_secret = ApiKeyService.decrypt_secret(merchant.api_secret_encrypted)
    except ValueError:
        raise TokenError(msg="凭证解析失败")

    # 读取请求体（Starlette 会缓存，不影响后续 endpoint 解析 body）
    body = await request.body()

    # 验签
    if not ApiKeyService.verify_signature(
        api_secret=api_secret,
        method=request.method,
        path=request.url.path,
        timestamp=timestamp,
        nonce=nonce,
        body=body,
        provided_signature=signature,
    ):
        logger.warning("商户开放 API 验签失败 api_key=%s path=%s", api_key, request.url.path)
        raise TokenError(msg="签名校验失败")

    # nonce 防重放（验签通过后写入，TTL 与时间窗口一致）
    redis_util = get_redis_util()
    nonce_key = f"merchant:nonce:{api_key}:{nonce}"
    ok = await redis_util.set_nx_ex(
        nonce_key, "1", settings.MERCHANT.NONCE_TTL_SECONDS
    )
    if not ok:
        raise TokenError(msg="重复的请求（nonce 已使用）")

    return merchant
