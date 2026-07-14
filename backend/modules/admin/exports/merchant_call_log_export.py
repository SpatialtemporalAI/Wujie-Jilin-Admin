#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from core.utils.excel_export import ExportColumn
from modules.admin.exports import ModuleExportConfig, register_export
from modules.merchant.services.call_log_service import CallLogService
from modules.merchant.schemas.call_log import CallLogQueryParams
from database.utils.timezone import timezone

_merchant_call_log_columns = [
    ExportColumn("id", "ID", width=20, transform=str),
    ExportColumn("merchant_name", "商户名称", width=20),
    ExportColumn("merchant_code", "商户编码", width=15),
    ExportColumn("api_key_masked", "API Key", width=20),
    ExportColumn("method", "HTTP方法", width=10),
    ExportColumn("action", "动作", width=15),
    ExportColumn("path", "请求路径", width=30),
    ExportColumn("ip", "IP地址", width=18),
    ExportColumn("response_code", "响应码", width=10),
    ExportColumn(
        "success",
        "是否成功",
        width=10,
        transform=lambda v: "成功" if v else "失败",
    ),
    ExportColumn("elapsed_ms", "耗时(ms)", width=10),
    ExportColumn("error_msg", "错误信息", width=30),
    ExportColumn(
        "created_at",
        "调用时间",
        width=22,
        transform=timezone.ftime,
    ),
]

register_export(ModuleExportConfig(
    name="商户调用日志",
    module_key="merchant_call_log",
    columns=_merchant_call_log_columns,
    build_query_fn=CallLogService.build_call_log_query,
    query_params_class=CallLogQueryParams,
))
