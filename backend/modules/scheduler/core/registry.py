#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
定时任务装饰器注册器
通过 @scheduled_task 装饰器声明式注册定时任务元数据
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger(__name__)

_TASK_REGISTRY: dict[str, "TaskDefinition"] = {}


@dataclass
class TaskDefinition:
    """装饰器注册的任务定义"""

    task_key: str
    name: str
    description: str
    cron_expression: str
    trigger_type: str  # "cron" | "interval" | "date"
    trigger_params: dict
    function: Callable
    module: str
    function_path: str
    timeout: int = 300
    max_retries: int = 0
    concurrent_policy: str = "skip"
    is_system: bool = False


def scheduled_task(
    *,
    cron: str | None = None,
    interval: int | None = None,
    date: str | None = None,
    name: str,
    description: str = "",
    task_key: str | None = None,
    timeout: int = 300,
    max_retries: int = 0,
    concurrent_policy: str = "skip",
    is_system: bool = False,
):
    """
    装饰器：将函数注册为可管理的定时任务。

    用法::

        @scheduled_task(cron="0 */5 * * *", name="清理日志", description="清理过期日志")
        async def cleanup_logs():
            ...

    Args:
        cron: Cron 表达式（如 "0 */5 * * *"）
        interval: 固定间隔（秒）
        date: 一次性执行时间（ISO 格式字符串）
        name: 任务显示名称
        description: 任务描述
        task_key: 唯一标识，默认自动生成 module.function
        timeout: 超时秒数
        max_retries: 最大重试次数
        concurrent_policy: 并发策略 skip/replace/run
        is_system: 系统任务不可通过 UI 删除
    """

    def decorator(func: Callable) -> Callable:
        trigger_type, trigger_params, cron_expr = _resolve_trigger(cron, interval, date)

        key = task_key or f"{func.__module__}.{func.__qualname__}"
        func_path = f"{func.__module__}.{func.__qualname__}"

        definition = TaskDefinition(
            task_key=key,
            name=name,
            description=description,
            cron_expression=cron_expr,
            trigger_type=trigger_type,
            trigger_params=trigger_params,
            function=func,
            module=func.__module__,
            function_path=func_path,
            timeout=timeout,
            max_retries=max_retries,
            concurrent_policy=concurrent_policy,
            is_system=is_system,
        )

        _TASK_REGISTRY[key] = definition
        logger.debug("注册定时任务: %s (%s)", name, key)
        return func

    return decorator


def _resolve_trigger(
    cron: str | None, interval: int | None, date: str | None
) -> tuple[str, dict, str]:
    """解析触发器参数，返回 (trigger_type, trigger_params, cron_expression)"""
    provided = sum(x is not None for x in [cron, interval, date])
    if provided == 0:
        raise ValueError("必须指定 cron、interval 或 date 之一")
    if provided > 1:
        raise ValueError("cron、interval、date 只能指定一个")

    if cron is not None:
        return "cron", {}, cron
    if interval is not None:
        return "interval", {"seconds": interval}, str(interval)
    # date
    return "date", {"run_date": date}, date or ""


def get_registered_tasks() -> dict[str, TaskDefinition]:
    """返回所有通过装饰器注册的任务"""
    return dict(_TASK_REGISTRY)


def get_task_definition(task_key: str) -> TaskDefinition | None:
    """按 task_key 获取注册的任务定义"""
    return _TASK_REGISTRY.get(task_key)
