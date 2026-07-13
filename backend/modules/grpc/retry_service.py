"""
gRPC 推送失败重试服务

职责：
1. cancel_superseded：业务层每次推送前调用，取消同业务键的旧 pending 任务（无论本次成败）
2. save_pending：业务层推送失败/离线时调用，把任务持久化到 grpc_retry_task 表
3. run_pending_once：调度任务调用，扫描到期任务并重试

覆盖语义（同机器人同类消息覆盖，旧 GRPC 无需再推）：
- voice/speed/battery：覆盖键 = (method, robot_id)
- 保存地图 NotifyMapSaved：覆盖键 = (method, robot_id, map_id)
- 切换地图 SwitchMap：覆盖键 = (method, robot_id)
注意：cancel_superseded 由推送入口在「调 RPC 之前」调用，因此新推送即使成功也会取消旧 pending，
避免旧值被定时任务补推造成设备端数据回退。

在线前置（定时重试先检测在线）：
- 机器人软删 → 任务置 cancelled（不无限等待）
- 机器人离线 → next_retry_at 延后 _ONLINE_WAIT_SECONDS，不推进 retry_count、不标 dead，
  等机器人上线后再推；只有真正的推送失败才消耗退避次数。

指数退避：60s -> 120s -> 240s（共 3 次），超过 max_retries 标记 dead。

调用容错：单次重试用 asyncio.wait_for 加 _CALL_TIMEOUT_SECONDS 硬超时，
无论超时 / 抛异常 / resp.success=False，都视为一次失败并推进 retry_count，
避免对端 hang 或 grpc.aio 未按 deadline 抛错时任务永远停在 pending。
"""
import asyncio
import logging
from datetime import timedelta
from typing import Any, Awaitable, Callable, Dict, Optional, Tuple

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.business.grpc_retry_task import GrpcRetryTask
from database.utils.timezone import timezone
from modules.grpc.config_client import (
    BatteryConfigClient,
    SpeedConfigClient,
    VoiceConfigClient,
)
from modules.grpc.map_retry_helper import MapRetryHelper
from modules.grpc.result import RetryCallResult

logger = logging.getLogger(__name__)


# 指数退避间隔（秒）：第 1 次 60s、第 2 次 120s、第 3 次 240s
_BACKOFF_SECONDS: Tuple[int, ...] = (60, 120, 240)

# 离线任务的再扫间隔（秒）：离线不消耗退避，每分钟重试在线状态
_ONLINE_WAIT_SECONDS: int = 60

# 单次重试的硬超时（秒）：兜底 settings.GRPC.TIMEOUT_SECONDS，
# 防止 grpc.aio 在某些场景未按 deadline 抛错时把整个扫描卡死
_CALL_TIMEOUT_SECONDS: float = 30.0


async def _wrap_voice_wake(
    robot_id: int, wake_word_enabled: bool, wake_word: str
) -> RetryCallResult:
    resp = await VoiceConfigClient.notify_wake_word(
        robot_id, wake_word_enabled, wake_word
    )
    return RetryCallResult(
        success=getattr(resp, "success", False),
        message=getattr(resp, "message", ""),
    )


async def _wrap_voice_tts(
    robot_id: int, tts_voice: str, tts_speed: float, tts_volume: int
) -> RetryCallResult:
    resp = await VoiceConfigClient.notify_tts(robot_id, tts_voice, tts_speed, tts_volume)
    return RetryCallResult(
        success=getattr(resp, "success", False),
        message=getattr(resp, "message", ""),
    )


async def _wrap_speed(robot_id: int, speed_level: str) -> RetryCallResult:
    resp = await SpeedConfigClient.notify_speed_level(robot_id, speed_level)
    return RetryCallResult(
        success=getattr(resp, "success", False),
        message=getattr(resp, "message", ""),
    )


async def _wrap_battery(robot_id: int, battery_threshold: int) -> RetryCallResult:
    resp = await BatteryConfigClient.notify_battery_threshold(
        robot_id, battery_threshold
    )
    return RetryCallResult(
        success=getattr(resp, "success", False),
        message=getattr(resp, "message", ""),
    )


# (service_name, method_name) → (retry_callable, required_payload_keys)
# retry_callable 统一返回 RetryCallResult；kwargs 由 payload 按 required_keys 构造
_ROUTING: Dict[Tuple[str, str], Tuple[Callable[..., Awaitable[RetryCallResult]], Tuple[str, ...]]] = {
    ("voice", "NotifyWakeWordChanged"): (
        _wrap_voice_wake,
        ("robot_id", "wake_word_enabled", "wake_word"),
    ),
    ("voice", "NotifyTTSConfigChanged"): (
        _wrap_voice_tts,
        ("robot_id", "tts_voice", "tts_speed", "tts_volume"),
    ),
    ("speed", "NotifySpeedLevelChanged"): (
        _wrap_speed,
        ("robot_id", "speed_level"),
    ),
    ("battery", "NotifyBatteryThresholdChanged"): (
        _wrap_battery,
        ("robot_id", "battery_threshold"),
    ),
    ("map", "NotifyMapSaved"): (
        MapRetryHelper.notify_map_saved,
        ("robot_id", "map_id", "version"),
    ),
    ("map", "SwitchMap"): (
        MapRetryHelper.switch_map,
        ("robot_id", "map_id", "version"),
    ),
}


def _calc_next_retry(retry_count: int) -> timedelta:
    """根据已重试次数计算下次退避时长（指数退避，封顶 240s）"""
    idx = min(retry_count, len(_BACKOFF_SECONDS) - 1)
    return timedelta(seconds=_BACKOFF_SECONDS[idx])


def _superseded_clause(
    service_name: str,
    method_name: str,
    robot_id: Optional[int],
    map_id: Optional[int] = None,
):
    """构造「同业务键的 pending 任务」WHERE 条件列表

    覆盖键规则：
    - voice/speed/battery/切换地图：method + robot_id（map_id 均为 NULL）
    - 保存地图：method + robot_id + map_id（不同地图互不覆盖）
    robot_id 为 None 时不取消（兼容未来无 robot 上下文任务）。
    """
    if robot_id is None:
        return None

    conditions = [
        GrpcRetryTask.status == "pending",
        GrpcRetryTask.deleted_at.is_(None),
        GrpcRetryTask.service_name == service_name,
        GrpcRetryTask.method_name == method_name,
        GrpcRetryTask.robot_id == robot_id,
    ]
    # NULL-safe：map_id 为空只覆盖 map_id IS NULL 的旧任务；非空只覆盖同 map_id
    if map_id is None:
        conditions.append(GrpcRetryTask.map_id.is_(None))
    else:
        conditions.append(GrpcRetryTask.map_id == map_id)
    return conditions


class GrpcRetryService:
    """gRPC 推送失败重试服务"""

    @staticmethod
    async def cancel_superseded(
        db: AsyncSession,
        *,
        service_name: str,
        method_name: str,
        robot_id: Optional[int],
        map_id: Optional[int] = None,
    ) -> int:
        """取消被新操作覆盖的旧 pending 任务（同业务键）。

        由推送入口在「调 RPC 之前」调用：无论本次推送成功或失败，旧同键 pending 都先取消，
        避免定时任务把旧值补推造成设备端数据回退。内部自带 commit（独立于 save_pending）。

        Returns:
            取消条数
        """
        conditions = _superseded_clause(service_name, method_name, robot_id, map_id)
        if conditions is None:
            return 0

        result = await db.execute(
            update(GrpcRetryTask)
            .where(*conditions)
            .values(status="cancelled", last_error="被新操作覆盖，不再重试")
            .execution_options(synchronize_session=False)
        )
        cancelled = result.rowcount or 0
        if cancelled:
            await db.commit()
            logger.info(
                "grpc retry superseded %s old task(s) service=%s method=%s robot_id=%s map_id=%s",
                cancelled,
                service_name,
                method_name,
                robot_id,
                map_id,
            )
        return cancelled

    @staticmethod
    async def save_pending(
        db: AsyncSession,
        *,
        service_name: str,
        method_name: str,
        payload: Dict[str, Any],
        robot_id: Optional[int] = None,
        map_id: Optional[int] = None,
        max_retries: int = 3,
        last_error: Optional[str] = None,
    ) -> GrpcRetryTask:
        """业务层 gRPC 推送失败/离线时调用：写入待重试任务

        本方法不再取消同键旧任务——调用方需在推送入口先调 cancel_superseded。
        next_retry_at = now() + 第一次退避（60s）。
        """
        task = GrpcRetryTask(
            service_name=service_name,
            method_name=method_name,
            payload=payload,
            robot_id=robot_id,
            map_id=map_id,
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
            "grpc retry task saved service=%s method=%s robot_id=%s map_id=%s task_id=%s",
            service_name,
            method_name,
            robot_id,
            map_id,
            task.id,
        )
        return task

    @staticmethod
    async def _robot_active(db: AsyncSession, robot_id: Optional[int]) -> bool:
        """机器人存在且未软删（用于把已删机器人的任务判 cancelled）"""
        if robot_id is None:
            return True
        from database.models.business.robot import Robot

        result = await db.execute(
            select(Robot.id).where(
                Robot.id == robot_id, Robot.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def is_robot_online(db: AsyncSession, robot_id: Optional[int]) -> bool:
        """机器人是否在线（status == ONLINE 且未软删）；robot_id 为 None 视为在线。

        作为「在线判定」的唯一真源，供推送入口（config / 地图保存 / 切换地图）与定时重试复用。
        """
        if robot_id is None:
            return True
        from database.models.business.robot import Robot, RobotStatus

        result = await db.execute(
            select(Robot.status).where(
                Robot.id == robot_id, Robot.deleted_at.is_(None)
            )
        )
        status = result.scalar_one_or_none()
        return status == RobotStatus.ONLINE

    @staticmethod
    async def run_pending_once(db: AsyncSession, limit: int = 50) -> Dict[str, int]:
        """扫描到期任务并重试

        Returns:
            {"scanned": N, "completed": N, "rescheduled": N, "dead": N,
             "failed": N, "waiting_online": N, "cancelled": N}
        """
        stats = {
            "scanned": 0,
            "completed": 0,
            "rescheduled": 0,
            "dead": 0,
            "failed": 0,
            "waiting_online": 0,
            "cancelled": 0,
        }
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
        """重试单条任务，返回结果分类:
        completed / rescheduled / dead / waiting_online / cancelled"""
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

        # 在线前置：机器人已删 → cancelled；离线 → 等待，不消耗退避
        if task.robot_id is not None:
            if not await GrpcRetryService._robot_active(db, task.robot_id):
                task.status = "cancelled"
                task.last_error = "机器人已删除"
                await db.commit()
                return "cancelled"
            if not await GrpcRetryService.is_robot_online(db, task.robot_id):
                task.next_retry_at = timezone.now() + timedelta(
                    seconds=_ONLINE_WAIT_SECONDS
                )
                await db.commit()
                return "waiting_online"

        try:
            kwargs = {k: payload[k] for k in required_keys}
            resp = await asyncio.wait_for(
                client_method(**kwargs), timeout=_CALL_TIMEOUT_SECONDS
            )
        except asyncio.TimeoutError:
            logger.warning(
                "grpc retry call hard timeout task_id=%s service=%s method=%s",
                task.id,
                task.service_name,
                task.method_name,
            )
            task.last_error = f"调用超时（{_CALL_TIMEOUT_SECONDS}s）"
            GrpcRetryService._advance_fields(task)
            await db.commit()
            return "dead" if task.status == "dead" else "rescheduled"
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

        # resp 为统一 RetryCallResult
        if getattr(resp, "cancel", False):
            task.status = "cancelled"
            task.last_error = resp.message or "任务取消"
            await db.commit()
            logger.info(
                "grpc retry task cancelled task_id=%s service=%s method=%s",
                task.id,
                task.service_name,
                task.method_name,
            )
            return "cancelled"

        if resp.success:
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

        # 推送失败（resp.success=False）
        task.last_error = resp.message or "设备未响应"
        GrpcRetryService._advance_fields(task)
        await db.commit()
        return "dead" if task.status == "dead" else "rescheduled"

    @staticmethod
    def _advance_fields(task: GrpcRetryTask) -> None:
        """推进 retry_count，按上限置 dead 或重新计算 next_retry_at（只改字段，不 commit）"""
        task.retry_count += 1
        if task.retry_count >= task.max_retries:
            task.status = "dead"
            # next_retry_at 保持原值：该列 NOT NULL 不能置 None；
            # dead 任务不会再被调度（run_pending_once 的 status=='pending' 过滤已排除），
            # 记录保留以便审计。
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
