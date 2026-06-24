"""
gRPC 推送失败重试服务

职责：
1. save_pending：业务层 gRPC 推送失败时调用，把任务持久化到 grpc_retry_task 表
2. run_pending_once：调度任务调用，扫描到期任务并重试
3. _dispatch_retry：根据 service_name + method_name 路由到对应 client（复用 config_client.py）

指数退避：60s -> 120s -> 240s（共 3 次），超过 max_retries 标记 dead。
"""
import logging
from datetime import timedelta
from typing import Any, Awaitable, Callable, Dict, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.business.grpc_retry_task import GrpcRetryTask
from database.utils.timezone import timezone
from modules.grpc.config_client import (
    BatteryConfigClient,
    FaceRecognitionClient,
    SpeedConfigClient,
    VoiceConfigClient,
)

logger = logging.getLogger(__name__)


# 指数退避间隔（秒）：第 1 次 60s、第 2 次 120s、第 3 次 240s
_BACKOFF_SECONDS: Tuple[int, ...] = (60, 120, 240)

# (service_name, method_name) → (client_method_ref, required_payload_keys)
# 用于把任务表的 service/method/payload 路由到对应 client 方法
_ROUTING: Dict[Tuple[str, str], Tuple[Callable[..., Awaitable[Any]], Tuple[str, ...]]] = {
    ("voice", "NotifyWakeWordChanged"): (
        VoiceConfigClient.notify_wake_word,
        ("robot_id", "wake_word_enabled", "wake_word"),
    ),
    ("voice", "NotifyTTSConfigChanged"): (
        VoiceConfigClient.notify_tts,
        ("robot_id", "tts_voice", "tts_speed", "tts_volume"),
    ),
    ("speed", "NotifySpeedLevelChanged"): (
        SpeedConfigClient.notify_speed_level,
        ("robot_id", "speed_level"),
    ),
    ("battery", "NotifyBatteryThresholdChanged"): (
        BatteryConfigClient.notify_battery_threshold,
        ("robot_id", "battery_threshold"),
    ),
    ("face_recognition", "NotifyFaceRecognitionChanged"): (
        FaceRecognitionClient.notify_changed,
        ("operation", "face_id", "person_name", "photo_url", "broadcast_text"),
    ),
}


def _calc_next_retry(retry_count: int) -> timedelta:
    """根据已重试次数计算下次退避时长（指数退避，封顶 240s）"""
    idx = min(retry_count, len(_BACKOFF_SECONDS) - 1)
    return timedelta(seconds=_BACKOFF_SECONDS[idx])


class GrpcRetryService:
    """gRPC 推送失败重试服务"""

    @staticmethod
    async def save_pending(
        db: AsyncSession,
        *,
        service_name: str,
        method_name: str,
        payload: Dict[str, Any],
        robot_id: Optional[int] = None,
        max_retries: int = 3,
        last_error: Optional[str] = None,
    ) -> GrpcRetryTask:
        """业务层 gRPC 推送失败时调用：写入待重试任务

        next_retry_at = now() + 第一次退避（60s）
        """
        task = GrpcRetryTask(
            service_name=service_name,
            method_name=method_name,
            payload=payload,
            robot_id=robot_id,
            status="pending",
            retry_count=0,
            max_retries=max_retries,
            next_retry_at=timezone.now() + _calc_next_retry(0),
            last_error=last_error,
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)
        logger.info(
            "grpc retry task saved service=%s method=%s robot_id=%s task_id=%s",
            service_name,
            method_name,
            robot_id,
            task.id,
        )
        return task

    @staticmethod
    async def run_pending_once(db: AsyncSession, limit: int = 50) -> Dict[str, int]:
        """扫描到期任务并重试

        Returns:
            {"scanned": N, "completed": N, "rescheduled": N, "dead": N, "failed": N}
        """
        stats = {"scanned": 0, "completed": 0, "rescheduled": 0, "dead": 0, "failed": 0}
        now = timezone.now()

        result = await db.execute(
            select(GrpcRetryTask)
            .where(GrpcRetryTask.status == "pending")
            .where(GrpcRetryTask.next_retry_at <= now)
            .where(GrpcRetryTask.deleted_at.is_(None))
            .order_by(GrpcRetryTask.next_retry_at.asc())
            .limit(limit)
        )
        tasks = list(result.scalars().all())
        stats["scanned"] = len(tasks)

        for task in tasks:
            outcome = await GrpcRetryService._retry_one(db, task)
            stats[outcome] += 1

        return stats

    @staticmethod
    async def _retry_one(db: AsyncSession, task: GrpcRetryTask) -> str:
        """重试单条任务，返回结果分类: completed / rescheduled / dead"""
        routing = _ROUTING.get((task.service_name, task.method_name))
        if routing is None:
            logger.error(
                "grpc retry task has no routing service=%s method=%s task_id=%s",
                task.service_name,
                task.method_name,
                task.id,
            )
            task.status = "dead"
            task.last_error = f"无路由配置: {task.service_name}/{task.method_name}"
            await db.commit()
            return "dead"

        client_method, required_keys = routing
        payload = task.payload or {}

        # 校验 payload 必需字段，缺失直接标记 dead（避免反复失败）
        missing = [k for k in required_keys if k not in payload]
        if missing:
            logger.error(
                "grpc retry task payload missing keys=%s task_id=%s",
                missing,
                task.id,
            )
            task.status = "dead"
            task.last_error = f"payload 缺失字段: {missing}"
            await db.commit()
            return "dead"

        try:
            kwargs = {k: payload[k] for k in required_keys}
            resp = await client_method(**kwargs)
        except Exception as e:  # noqa: BLE001 - client 内部已吞，这里是双保险
            logger.exception(
                "grpc retry call raised task_id=%s service=%s method=%s",
                task.id,
                task.service_name,
                task.method_name,
            )
            task.last_error = f"调用异常: {e}"
            GrpcRetryService._advance_fields(task)
            await db.commit()
            return "dead" if task.status == "dead" else "rescheduled"

        if getattr(resp, "success", False):
            task.status = "completed"
            task.completed_at = timezone.now()
            task.last_error = None
            await db.commit()
            logger.info(
                "grpc retry task completed task_id=%s service=%s method=%s",
                task.id,
                task.service_name,
                task.method_name,
            )
            return "completed"

        # resp.success=False（client 已吞掉异常并返回失败响应）
        task.last_error = getattr(resp, "message", "") or "设备未响应"
        GrpcRetryService._advance_fields(task)
        await db.commit()
        return "dead" if task.status == "dead" else "rescheduled"

    @staticmethod
    def _advance_fields(task: GrpcRetryTask) -> None:
        """推进 retry_count，按上限置 dead 或重新计算 next_retry_at（只改字段，不 commit）"""
        task.retry_count += 1
        if task.retry_count >= task.max_retries:
            task.status = "dead"
            task.next_retry_at = None  # dead 不再调度，但记录保留以便审计
            logger.warning(
                "grpc retry task dead task_id=%s retries=%s last_error=%s",
                task.id,
                task.retry_count,
                task.last_error,
            )
        else:
            task.next_retry_at = timezone.now() + _calc_next_retry(task.retry_count)
            logger.info(
                "grpc retry task rescheduled task_id=%s retry_count=%s next_retry_at=%s",
                task.id,
                task.retry_count,
                task.next_retry_at,
            )
