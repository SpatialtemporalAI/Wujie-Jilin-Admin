#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hashlib
import time
import random
import string
from datetime import datetime
from core.config import settings
def generate_session_id(
    user_id: str or int, secret_salt: str = settings.JWT.SECRET_SALT
) -> str:
    """
    基于用户ID和当前时间生成会话ID
    参数:
        user_id: 用户唯一标识
        secret_salt: 用于增强安全性的盐值（生产环境中应保密）
    返回:
        生成的会话ID字符串
    """
    # 1. 获取当前时间戳（精确到毫秒）
    timestamp = str(int(time.time() * 1000))
    # 2. 生成随机字符串（增加唯一性）
    random_str = "".join(random.choices(string.ascii_letters + string.digits, k=8))
    # 3. 组合用户ID、时间戳、随机字符串和盐值
    raw_data = f"{user_id}-{timestamp}-{random_str}-{secret_salt}"
    # 4. 使用SHA-256哈希算法生成固定长度的会话ID
    session_id = hashlib.sha256(raw_data.encode("utf-8")).hexdigest()
    # 5. 可以添加前缀便于识别（可选）
    # session_id = f"sess_{session_id}"
    return session_id
def parse_session_info(
    session_id: str, user_id: str or int, secret_salt: str = "your-secret-salt"
) -> dict or None:
    """
    验证会话ID并解析其中的时间信息（仅用于演示，实际中哈希值无法反向解析）
    注意：哈希是单向的，此函数仅用于说明生成逻辑，实际中无法从session_id还原信息
    """
    # 实际应用中，这里应该是从数据库或缓存中查询会话信息
    # 本函数仅作为生成逻辑的反向演示
    return {
        "user_id": user_id,
        "generated_time": (
            datetime.fromtimestamp(int(session_id[:13]) / 1000)
            if len(session_id) >= 13
            else None
        ),
        "is_valid": True,  # 实际中应根据存储的会话信息验证
    }
# 示例使用
if __name__ == "__main__":
    user_id = "123456"  # 用户ID
    session_id = generate_session_id(user_id)
    print(f"生成的会话ID: {session_id}")
    print(f"会话ID长度: {len(session_id)}")
    # 模拟验证会话（实际中需要查询存储的会话信息）
    session_info = parse_session_info(session_id, user_id)
    print(f"会话信息: {session_info}")