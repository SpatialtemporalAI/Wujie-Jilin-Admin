#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
可逆加密工具（Fernet），用于商户 api_secret 的加密存储与验签解密。

与 core/security/password.py（bcrypt 单向哈希）不同：HMAC 签名验签需要服务端
持有 api_secret 明文来重新计算签名，因此 api_secret 必须可逆加密存储。

密钥由 settings.MERCHANT.ENCRYPT_KEY（passphrase）经 PBKDF2 派生，避免要求
调用方提供合法的 Fernet key 格式（urlsafe base64 32 字节）。更换 ENCRYPT_KEY
或 _SALT 会导致历史密文无法解密。
"""
import base64
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from core.config import settings

# 固定 salt（派生密钥用）；更换会使历史密文无法解密
_SALT = b"wujie-jilin-merchant-api-secret-salt"
_ITERATIONS = 480_000


@lru_cache(maxsize=1)
def _get_fernet() -> Fernet:
    """根据配置 passphrase 派生 Fernet 实例（进程级缓存）"""
    passphrase = settings.MERCHANT.ENCRYPT_KEY.encode("utf-8")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_SALT,
        iterations=_ITERATIONS,
    )
    key = base64.urlsafe_b64encode(kdf.derive(passphrase))
    return Fernet(key)


def encrypt(plaintext: str) -> str:
    """加密明文，返回 Fernet token 字符串"""
    return _get_fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt(token: str) -> str:
    """解密 Fernet token，返回明文；token 非法时抛 ValueError"""
    try:
        return _get_fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("api_secret 解密失败") from exc
