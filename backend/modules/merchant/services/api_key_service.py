#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
商户 api_key / api_secret 生成与 HMAC 签名验签服务。

签名规则（商户开放 API）：
    string_to_sign = "{method}\n{path}\n{timestamp}\n{nonce}\n{body_sha256_hex}"
    signature      = HMAC-SHA256(api_secret, string_to_sign) 的十六进制摘要

其中：
- method/timestamp/nonce 由请求头 X-Method / X-Timestamp / X-Nonce 提供
  （method 也可取自 request.method，但统一从头取避免大小写歧义）
- path 为请求路径（不含 query string）
- body_sha256_hex 为请求体原始字节的 SHA-256 十六进制摘要（GET/无 body 时为空串的摘要）

请求头约定：
- X-Api-Key:    商户 api_key
- X-Timestamp:  秒级 Unix 时间戳
- X-Nonce:      随机串（单次唯一）
- X-Signature:  计算出的签名
"""
import hashlib
import hmac
import secrets

from core.config import settings
from core.security import crypto


class ApiKeyService:
    """api_key / api_secret 生成与 HMAC 验签"""

    @staticmethod
    def generate_api_key() -> str:
        """生成 api_key：前缀 + 32 位 hex"""
        prefix = settings.MERCHANT.API_KEY_PREFIX
        return f"{prefix}{secrets.token_hex(16)}"

    @staticmethod
    def generate_api_secret() -> str:
        """生成 api_secret 明文：前缀 + urlsafe 随机串（仅创建/重置时返回一次）"""
        prefix = settings.MERCHANT.API_SECRET_PREFIX
        return f"{prefix}{secrets.token_urlsafe(32)}"

    @staticmethod
    def encrypt_secret(plaintext: str) -> str:
        """加密 api_secret 明文，得到入库密文"""
        return crypto.encrypt(plaintext)

    @staticmethod
    def decrypt_secret(ciphertext: str) -> str:
        """解密 api_secret 密文，得到明文（用于验签重算）"""
        return crypto.decrypt(ciphertext)

    @staticmethod
    def build_string_to_sign(
        method: str, path: str, timestamp: str, nonce: str, body: bytes
    ) -> str:
        """构造待签名串"""
        body_hash = hashlib.sha256(body or b"").hexdigest()
        return f"{method.upper()}\n{path}\n{timestamp}\n{nonce}\n{body_hash}"

    @staticmethod
    def sign(api_secret: str, string_to_sign: str) -> str:
        """用 api_secret 对待签名串计算 HMAC-SHA256 十六进制签名"""
        return hmac.new(
            api_secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    @staticmethod
    def verify_signature(
        api_secret: str,
        method: str,
        path: str,
        timestamp: str,
        nonce: str,
        body: bytes,
        provided_signature: str,
    ) -> bool:
        """验签：常量时间比较，避免计时攻击"""
        expected = ApiKeyService.sign(
            api_secret,
            ApiKeyService.build_string_to_sign(method, path, timestamp, nonce, body),
        )
        if not provided_signature:
            return False
        return hmac.compare_digest(expected, provided_signature)
