#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
敏感数据脱敏工具

供商户开放 API 调用日志等审计场景使用：
- mask_api_key：对外暴露的 API Key 掩码（保留首尾，中间打码）
- mask_secret_fields：递归清洗 dict/list，把凭证类字段的值替换为 ***，
  但保留业务字段（robot_sn / point_ids / task_id / map_id / text 等，排查问题必需）

注意：签名（X-Signature）、密钥（api_secret）等凭证绝不应进入日志，
调用方在采集阶段就不要把它们传进来；本工具只做第二道防线。
"""
import re
from typing import Any

# 命中以下关键字的字段值会被整体替换为 ***
# 仅匹配字段名，不匹配业务字段（robot_sn / point_id / task_id / map_id / text 等）
_SECRET_KEY_PATTERN = re.compile(
    r"(secret|sign|signature|password|passwd|token|authorization|api[-_]?key)",
    re.IGNORECASE,
)

# 单个字符串值最长保留长度，超出截断（防止整段播报文本/大响应撑爆日志表）
_MAX_VALUE_LENGTH = 500


def mask_api_key(api_key: str | None, head: int = 6, tail: int = 4) -> str:
    """对 API Key 做掩码：保留首 head 位与末 tail 位，中间用 **** 代替。

    None / 空串返回空串；过短则只保留少量可见字符。
    """
    if not api_key:
        return ""
    if len(api_key) <= head + tail:
        # 过短：保留首 2 位，其余打码
        keep = min(2, len(api_key))
        return api_key[:keep] + "****"
    return f"{api_key[:head]}{'****'}{api_key[-tail:]}"


def _truncate(value: str) -> str:
    if len(value) > _MAX_VALUE_LENGTH:
        return value[:_MAX_VALUE_LENGTH] + "...(truncated)"
    return value


def mask_secret_fields(obj: Any) -> Any:
    """递归遍历 dict/list，对凭证类字段值替换为 ***，并截断超长字符串。

    - dict：key 命中 _SECRET_KEY_PATTERN 时 value -> "***"；否则递归处理 value
    - list：逐项递归
    - str：截断
    - 其它类型：原样返回
    """
    if isinstance(obj, dict):
        masked: dict[str, Any] = {}
        for k, v in obj.items():
            if isinstance(k, str) and _SECRET_KEY_PATTERN.search(k):
                masked[k] = "***"
            else:
                masked[k] = mask_secret_fields(v)
        return masked
    if isinstance(obj, list):
        return [mask_secret_fields(item) for item in obj]
    if isinstance(obj, str):
        return _truncate(obj)
    return obj
