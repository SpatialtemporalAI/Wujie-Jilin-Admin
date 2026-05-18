#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from fastapi import Request

from core.config import settings

def get_request_trace_id(request: Request) -> str:
    """
    获取追踪 ID，优先从 request.state 获取（中间件生成的 UUID）

    :param request: FastAPI 请求对象
    :return: 追踪 ID
    """
    return (
        getattr(request.state, "request_id", None)
        or request.headers.get(settings.TRACE_ID.REQUEST_HEADER_KEY)
        or settings.TRACE_ID.LOG_DEFAULT_VALUE
    )
