#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import contextvars
from typing import Optional

tenant_id_ctx: contextvars.ContextVar[Optional[int]] = contextvars.ContextVar(
    "tenant_id", default=None
)


def get_current_tenant_id() -> Optional[int]:
    """获取当前请求的租户ID"""
    return tenant_id_ctx.get()


def set_current_tenant_id(tenant_id: Optional[int]) -> contextvars.Token:
    """设置当前请求的租户ID，返回 token 用于重置"""
    return tenant_id_ctx.set(tenant_id)


def reset_tenant_id(token: contextvars.Token) -> None:
    """重置租户ID上下文"""
    tenant_id_ctx.reset(token)
