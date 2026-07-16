"""
RouteTaskService gRPC 客户端

任务运行时变更通知，按任务关联的 robot 列表逐个推送到 agent：
- notify_task_changed：单 robot 维度，走 target=agent
- broadcast_task_changed：按 robot_ids 批量推送，聚合结果（任一成功即记 ok）

operation 取值（与 task.proto 注释保持一致）：
- run_now  —— 启动任务（手动 start / 定时命中）
- pause    —— 暂停任务
- resume   —— 恢复任务
- stop     —— 停止任务

调用约定（对齐 config_client._dispatch_with_target）：
- GRPC.ENABLED=false → 返回 success=False 哨兵，不抛异常
- robot.grpc_config[agent] 缺失 / enabled=false / 无 host:port → success=False 哨兵
- gRPC 调用失败 → 返回 success=False 失败响应，不抛异常
- 业务层（endpoint）据此仅记日志，不阻塞主流程
"""
import logging
from typing import Dict, List

from app.grpc.generated.task import task_pb2, task_pb2_grpc

from modules.grpc.config_client import _dispatch_with_target
from modules.grpc.channel import get_config_channel_by_addr

logger = logging.getLogger(__name__)


class TaskConfigClient:
    """任务运行时变更 gRPC 客户端（走 agent）"""

    _stubs_by_addr: Dict[str, task_pb2_grpc.RouteTaskServiceStub] = {}

    @classmethod
    async def _get_stub_for_addr(
        cls, addr: str
    ) -> task_pb2_grpc.RouteTaskServiceStub:
        if addr not in cls._stubs_by_addr:
            channel = await get_config_channel_by_addr(addr)
            cls._stubs_by_addr[addr] = task_pb2_grpc.RouteTaskServiceStub(channel)
        return cls._stubs_by_addr[addr]

    @classmethod
    async def notify_task_changed(
        cls, robot_id: int, task_id: int, operation: str
    ) -> task_pb2.TaskChangedResponse:
        """单 robot 推送任务变更到 agent"""
        request = task_pb2.TaskChangedRequest(
            task_id=task_id,
            operation=operation,
        )
        return await _dispatch_with_target(
            robot_id=robot_id,
            target="agent",
            stub_factory=cls._get_stub_for_addr,
            method_name="NotifyTaskChanged",
            request=request,
            failure_factory=lambda msg: task_pb2.TaskChangedResponse(
                success=False, message=msg
            ),
            log_ctx={
                "robot_id": robot_id,
                "rpc": "notify_task_changed",
                "task_id": task_id,
                "operation": operation,
            },
        )

    @classmethod
    async def broadcast_task_changed(
        cls, task_id: int, operation: str, robot_ids: List[int]
    ) -> Dict[str, object]:
        """按 robot_ids 逐个推送，聚合结果（含成功/失败的 robot_id 列表）。

        Returns:
            {"total": N, "success_count": N, "failed_count": N,
             "success_robot_ids": [...], "failed_robot_ids": [...]}
            任一 robot 推送成功即业务层提示成功；全部失败仅日志，不抛异常。
        """
        total = len(robot_ids)
        if total == 0:
            return {
                "total": 0,
                "success_count": 0,
                "failed_count": 0,
                "success_robot_ids": [],
                "failed_robot_ids": [],
            }

        success_robot_ids: List[int] = []
        failed_robot_ids: List[int] = []
        for robot_id in robot_ids:
            try:
                resp = await cls.notify_task_changed(robot_id, task_id, operation)
            except Exception as e:  # noqa: BLE001 - _dispatch 已吞，这里是双保险
                logger.exception(
                    "grpc task broadcast raised task_id=%s robot_id=%s operation=%s",
                    task_id,
                    robot_id,
                    operation,
                )
                failed_robot_ids.append(robot_id)
                continue

            if getattr(resp, "success", False):
                success_robot_ids.append(robot_id)
                logger.info(
                    "grpc task notify ok task_id=%s robot_id=%s operation=%s",
                    task_id,
                    robot_id,
                    operation,
                )
            else:
                failed_robot_ids.append(robot_id)
                logger.warning(
                    "grpc task notify failed task_id=%s robot_id=%s operation=%s msg=%s",
                    task_id,
                    robot_id,
                    operation,
                    getattr(resp, "message", "") or "未知错误",
                )

        return {
            "total": total,
            "success_count": len(success_robot_ids),
            "failed_count": len(failed_robot_ids),
            "success_robot_ids": success_robot_ids,
            "failed_robot_ids": failed_robot_ids,
        }
