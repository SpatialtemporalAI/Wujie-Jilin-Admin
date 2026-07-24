#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

from core.utils.excel_export import ExportColumn
from modules.admin.exports import ModuleExportConfig, register_export
from modules.robot.services.robot_event_log_service import RobotEventLogService
from modules.robot.schemas.robot_event_log import RobotEventLogQueryParams
from database.utils.timezone import timezone


def _extract_event_message(value: str | None) -> str:
    """从 event_content JSON 中提取 message 字段用于展示。

    与前端 parseEventContentMessage 逻辑保持一致：event_content 以 JSON
    字符串存储（如 {"message": "...", ...}），安全解析后返回 message；
    非 JSON、解析失败或缺少 message 时回退到原始内容。
    """
    if not value:
        return ""
    try:
        obj = json.loads(value)
    except (ValueError, TypeError):
        return value
    if isinstance(obj, dict):
        msg = obj.get("message")
        if isinstance(msg, str) and msg:
            return msg
    return value


# 与列表三色标签一致：严重故障 / 告警提示 / 正常恢复
EVENT_STATUS_MAP = {"critical": "严重故障", "warning": "告警提示", "info": "正常恢复"}


_robot_event_log_columns = [
    ExportColumn("id", "ID", width=20, transform=str),
    ExportColumn("robot_id", "机器人ID", width=15, transform=str),
    ExportColumn("robot_name", "机器人名称", width=20),
    ExportColumn("event_status", "事件状态", width=12,
                 transform=lambda v: EVENT_STATUS_MAP.get(v, v)),
    ExportColumn("event_content", "事件内容", width=40, transform=_extract_event_message),
    ExportColumn("created_at", "创建时间", width=22,
                 transform=timezone.ftime),
]

register_export(ModuleExportConfig(
    name="机器人事件日志",
    module_key="robot_event_log",
    columns=_robot_event_log_columns,
    build_query_fn=RobotEventLogService.build_event_log_query,
    query_params_class=RobotEventLogQueryParams,
    enrich_fn=RobotEventLogService.fill_robot_names,
))
