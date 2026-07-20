#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from core.utils.excel_export import ExportColumn
from modules.admin.exports import ModuleExportConfig, register_export
from modules.robot.services.robot_event_log_service import RobotEventLogService
from modules.robot.schemas.robot_event_log import RobotEventLogQueryParams
from database.utils.timezone import timezone

# 与列表三色标签一致：严重故障 / 告警提示 / 正常恢复
EVENT_STATUS_MAP = {"critical": "严重故障", "warning": "告警提示", "info": "正常恢复"}


_robot_event_log_columns = [
    ExportColumn("id", "ID", width=20, transform=str),
    ExportColumn("robot_id", "机器人ID", width=15, transform=str),
    ExportColumn("robot_name", "机器人名称", width=20),
    ExportColumn("event_status", "事件状态", width=12,
                 transform=lambda v: EVENT_STATUS_MAP.get(v, v)),
    ExportColumn("event_content", "事件内容", width=40),
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
