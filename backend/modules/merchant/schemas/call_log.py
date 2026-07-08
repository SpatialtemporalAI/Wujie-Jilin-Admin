#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""商户开放 API 调用日志相关 Schema"""
from datetime import datetime

from pydantic import Field

from app.models.common.base import BaseEntity, BaseRespEntity, OptionalIntField, BoolField


class CallLogQueryParams(BaseEntity):
    """调用日志查询参数"""

    merchant_id: OptionalIntField = Field(None, description="商户ID")
    action: str | None = Field(None, description="动作（goto_point/speak/...）")
    success: BoolField = Field(None, description="是否成功")
    start_time: str | None = Field(None, description="开始时间")
    end_time: str | None = Field(None, description="结束时间")
    api_key: str | None = Field(None, description="API Key（模糊匹配脱敏值）")


class CallLogResponse(BaseRespEntity):
    """调用日志列表响应（不含请求参数/响应结果，详情接口提供）"""

    id: int
    merchant_id: int | None
    merchant_name: str | None
    merchant_code: str | None
    api_key_masked: str | None
    method: str | None
    path: str | None
    action: str | None
    ip: str | None
    response_code: int | None
    success: bool | None
    elapsed_ms: float | None
    error_msg: str | None
    created_at: datetime | None


class CallLogDetailResponse(BaseRespEntity):
    """调用日志详情响应（含脱敏后的请求参数/响应结果）"""

    id: int
    merchant_id: int | None
    merchant_name: str | None
    merchant_code: str | None
    api_key_masked: str | None
    method: str | None
    path: str | None
    action: str | None
    ip: str | None
    request_params: str | None
    response_code: int | None
    response_result: str | None
    success: bool | None
    elapsed_ms: float | None
    error_msg: str | None
    created_at: datetime | None
