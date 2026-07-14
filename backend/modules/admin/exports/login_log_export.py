#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from core.utils.excel_export import ExportColumn
from modules.admin.exports import ModuleExportConfig, register_export
from modules.admin.services.sys.login_log_service import LoginLogService
from modules.admin.schemas.sys.login_log import LoginLogQueryParams
from database.utils.timezone import timezone

_login_log_columns = [
    ExportColumn("id", "ID", width=20, transform=str),
    ExportColumn("username", "用户名", width=20),
    ExportColumn("ip", "IP地址", width=18),
    ExportColumn("status", "状态", width=10,
                 transform=lambda v: "成功" if v else "失败"),
    ExportColumn("detail", "详情", width=30),
    ExportColumn("user_agent", "登录设备", width=30),
    ExportColumn("login_time", "登录时间", width=22,
                 transform=timezone.ftime),
]

register_export(ModuleExportConfig(
    name="登录日志",
    module_key="login_log",
    columns=_login_log_columns,
    build_query_fn=LoginLogService.build_login_log_query,
    query_params_class=LoginLogQueryParams,
))
