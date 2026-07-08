"""
gRPC 重试路由统一返回类型

重试服务（retry_service._retry_one）通过 _ROUTING 调用各配置 client / 地图 helper，
统一用 RetryCallResult 判定本次重试结果，屏蔽各 proto 响应字段差异
（config client 返回带 .success 的 proto；map 响应只有 .status）。
"""
from dataclasses import dataclass


@dataclass
class RetryCallResult:
    """单次重试调用的统一结果

    Attributes:
        success: True → 本次推送成功，任务置 completed
        message: 失败原因（写 last_error 用于排障）
        cancel: True → 任务应被取消（如地图/机器人已删除），不再重试也不标 dead
    """

    success: bool
    message: str = ""
    cancel: bool = False
