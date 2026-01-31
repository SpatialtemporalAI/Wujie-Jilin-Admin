#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from fastapi import Request

from core.config import settings

def get_request_trace_id(request: Request) -> str:
    """
    从请求头中获取追踪 ID

    :param request: FastAPI 请求对象
    :return:
    """
    return (
        request.headers.get(settings.TRACE_ID.REQUEST_HEADER_KEY)
        or settings.TRACE_ID.LOG_DEFAULT_VALUE
    )
