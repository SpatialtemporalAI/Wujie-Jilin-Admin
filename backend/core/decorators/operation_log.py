#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
操作日志装饰器
用于标注需要记录操作日志的端点
"""
import json
import time
import logging
from functools import wraps
from typing import Callable

from fastapi import BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from app.models.sys.operation_log import SysOperationLog
from core.middleware.share_middleware import request_ctx

logger = logging.getLogger(__name__)


async def _write_log(
    user_id: int,
    username: str,
    module: str,
    action: str,
    description: str | None,
    method: str,
    path: str,
    ip: str,
    request_params: str | None,
    response_code: int | None,
    elapsed_ms: float | None,
):
    """异步写入操作日志到数据库"""
    try:
        async for db in get_session():
            log_entry = SysOperationLog(
                user_id=user_id,
                username=username,
                module=module,
                action=action,
                description=description,
                method=method,
                path=path,
                ip=ip,
                request_params=request_params,
                response_code=response_code,
                elapsed_ms=elapsed_ms,
            )
            db.add(log_entry)
            await db.commit()
    except Exception as e:
        logger.error(f"写入操作日志失败: {e}")


def log_operation(
    module: str,
    action: str,
    description: str | None = None,
):
    """
    操作日志装饰器

    用法:
        @log_operation(module="user", action="create", description="创建用户")
        async def create_user(...):
            ...

    要求被装饰的端点函数的第一个参数或依赖中包含 Request 对象，
    且通过 Depends(current_user) 注入的用户对象具有 id 和 username 属性。
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.monotonic()

            # 执行原始函数
            result = await func(*args, **kwargs)

            elapsed_ms = (time.monotonic() - start) * 1000

            # 在后台任务中记录日志，不阻塞主请求
            try:
                request: Request | None = kwargs.get("request")
                user = kwargs.get("user")
                background_tasks: BackgroundTasks | None = kwargs.get(
                    "background_tasks"
                )

                if not user or not request:
                    # 尝试从 args 中提取
                    return result

                ip = request.client.host if request.client else None
                response_code = None
                if hasattr(result, "status_code"):
                    response_code = result.status_code

                # 序列化请求参数（排除敏感信息）
                request_params = None
                try:
                    params = {}
                    if request.query_params:
                        params["query"] = dict(request.query_params)
                    if hasattr(request, "_body"):
                        body = request._body
                        if body:
                            params["body"] = json.loads(body)
                    request_params = json.dumps(params, ensure_ascii=False) if params else None
                except Exception:
                    pass

                user_id = user.id if hasattr(user, "id") else 0
                username = user.username if hasattr(user, "username") else "unknown"

                if background_tasks:
                    background_tasks.add_task(
                        _write_log,
                        user_id,
                        username,
                        module,
                        action,
                        description,
                        request.method,
                        str(request.url.path),
                        ip,
                        request_params,
                        response_code,
                        elapsed_ms,
                    )
                else:
                    import asyncio

                    asyncio.create_task(
                        _write_log(
                            user_id,
                            username,
                            module,
                            action,
                            description,
                            request.method,
                            str(request.url.path),
                            ip,
                            request_params,
                            response_code,
                            elapsed_ms,
                        )
                    )
            except Exception as e:
                logger.error(f"操作日志记录异常: {e}")

            return result

        return wrapper

    return decorator
