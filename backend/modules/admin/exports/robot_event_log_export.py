#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from core.utils.excel_export import ExportColumn
from modules.admin.exports import ModuleExportConfig, register_export
from modules.robot.services.robot_event_log_service import RobotEventLogService
from modules.robot.schemas.robot_event_log import RobotEventLogQueryParams

EVENT_TYPE_MAP = {"task": "任务", "alarm": "告警"}
EVENT_STATUS_MAP = {"normal": "正常", "abnormal": "异常"}


_robot_event_log_columns = [
    ExportColumn("id", "ID", width=20, transform=str),
    ExportColumn("robot_id", "机器人ID", width=15, transform=str),
    ExportColumn("event_type", "事件类型", width=12,
                 transform=lambda v: EVENT_TYPE_MAP.get(v, v)),
    ExportColumn("event_status", "事件状态", width=12,
                 transform=lambda v: EVENT_STATUS_MAP.get(v, v)),
    ExportColumn("event_content", "事件内容", width=40),
    ExportColumn("created_at", "创建时间", width=22,
                 transform=lambda v: v.strftime("%Y-%m-%d %H:%M:%S") if v else ""),
]

register_export(ModuleExportConfig(
    name="机器人事件日志",
    module_key="robot_event_log",
    columns=_robot_event_log_columns,
    build_query_fn=RobotEventLogService.build_event_log_query,
    query_params_class=RobotEventLogQueryParams,
))
