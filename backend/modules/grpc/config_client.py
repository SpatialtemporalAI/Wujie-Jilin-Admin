"""
ConfigService gRPC 客户端

覆盖 voice / speed / battery / face_recognition 四个配置类 RPC：
- 通用 _dispatch_with_target 内核：ENABLED 短路、按 robot_id+target 解析地址、stub 按 addr 缓存、超时、异常吞掉、日志
- 每个业务一个 Client 类（类方法风格，无需实例化），方法签名强类型

地址解析规则（target 对应 robot.grpc_config 的子键）：
- voice.notify_wake_word → middleware + agent（保存唤醒词，同时双推两端）
- voice.notify_tts → middleware（保存 TTS 配置）
- voice.notify_greeting_mode → agent（保存打招呼模式，仅推 agent 端）
- voice.test_wake_word / voice.test_tts → agent（测试推送，发送到机器人 agent）
- speed.notify_speed_level → middleware
- battery.notify_battery_threshold → agent
- face_recognition.notify_changed → agent（广播给所有启用 agent 的 robot）
- video.notify_video_monitoring → middleware

调用约定：
- GRPC.ENABLED=false → 返回 success=False 的哨兵响应，不抛异常
- robot.grpc_config[target] 缺失 / enabled=false / 无 host/port → 返回 success=False 哨兵（不回退 settings）
- gRPC 调用失败 → 返回 success=False 的失败响应，不抛异常
- 业务层据此决定提示文案，而非冒泡 500 给前端
"""

import asyncio
import logging
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple, TypeVar

import grpc

from app.grpc.generated.config import (
    battery_pb2,
    battery_pb2_grpc,
    face_recognition_pb2,
    face_recognition_pb2_grpc,
    speed_pb2,
    speed_pb2_grpc,
    video_pb2,
    video_pb2_grpc,
    voice_pb2,
    voice_pb2_grpc,
)

from core.config import settings
from modules.grpc.addr_provider import get_config_addr_provider
from modules.grpc.channel import get_config_channel_by_addr

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def _dispatch_with_target(
    robot_id: Optional[int],
    target: str,
    stub_factory: Callable[[str], Awaitable[Any]],
    method_name: str,
    request: Any,
    failure_factory: Callable[[str], T],
    log_ctx: dict,
) -> T:
    """通用调度内核（按 robot_id + target 解析地址）

    Args:
        robot_id: 目标机器人 ID（用于查 grpc_config）
        target: gRPC 子键名（agent / middleware / ros）
        stub_factory: 输入 addr，返回对应 stub 的协程工厂（按 addr 缓存 stub）
        method_name: stub 上的 RPC 方法名（如 "NotifyWakeWordChanged"）
        request: proto 请求对象
        failure_factory: 失败时构造响应的工厂，入参为 message
        log_ctx: 日志上下文（robot_id / operation 等）

    Returns:
        proto 响应对象；未启用 / 未配置 / 调用异常时返回 failure_factory 构造的哨兵响应
    """
    if not settings.GRPC.ENABLED:
        return failure_factory("gRPC 未启用")

    addr = await get_config_addr_provider().get_addr(robot_id, target)
    if not addr:
        return failure_factory(
            f"gRPC 地址未配置 (robot_id={robot_id}, target={target})"
        )

    try:
        stub = await stub_factory(addr)
        rpc: Callable[..., Awaitable[T]] = getattr(stub, method_name)
        return await rpc(request, timeout=settings.GRPC.TIMEOUT_SECONDS)
    except grpc.aio.AioRpcError as e:
        logger.warning(
            "grpc config call failed method=%s code=%s details=%s addr=%s ctx=%s",
            method_name,
            e.code(),
            e.details(),
            addr,
            log_ctx,
        )
        return failure_factory(f"gRPC 调用失败: {e.code().name}")
    except Exception as e:  # noqa: BLE001 - 兜底，保证不阻塞业务
        logger.exception(
            "grpc config call unexpected error method=%s addr=%s ctx=%s",
            method_name,
            addr,
            log_ctx,
        )
        return failure_factory(f"gRPC 调用异常: {e}")


# ==================== VoiceConfigClient ====================


class VoiceConfigClient:
    """语音配置 gRPC 客户端（唤醒词 + TTS 音色/语速/音量）

    保存唤醒词（notify_wake_word）同时推 middleware + agent；保存 TTS（notify_tts）走 middleware；
    测试推送（test_wake_word / test_tts）走 agent。
    """

    _stubs_by_addr: Dict[str, voice_pb2_grpc.VoiceConfigServiceStub] = {}

    @classmethod
    async def _get_stub_for_addr(
        cls, addr: str
    ) -> voice_pb2_grpc.VoiceConfigServiceStub:
        if addr not in cls._stubs_by_addr:
            channel = await get_config_channel_by_addr(addr)
            cls._stubs_by_addr[addr] = voice_pb2_grpc.VoiceConfigServiceStub(channel)
        return cls._stubs_by_addr[addr]

    @classmethod
    async def notify_wake_word(
        cls, robot_id: int, wake_word_enabled: bool, wake_word: str
    ) -> voice_pb2.WakeWordChangedResponse:
        """推送唤醒词变更：同时下发给 middleware 和 agent（仅推已配置且启用的端）。

        聚合语义（配合上层 _push_with_retry 的最终一致模型）：
        - 两端均未配置 → success=False 哨兵（按失败处理，可入重试队列等待配置）
        - 至少一端配置：所有「已配置端」全部成功才视为 success；
          任一已配置端失败 → success=False（message 拼接各失败端原因），由上层入重试队列，
          重试时两端都重推（NotifyWakeWord 全量覆盖语义，重复推送幂等）。
        并发双推：middleware / agent 是两个独立地址，asyncio.gather 并行下发，互不阻塞。
        """
        request = voice_pb2.WakeWordChangedRequest(
            robot_id=robot_id,
            wake_word_enabled=wake_word_enabled,
            wake_word=wake_word or "",
        )
        log_ctx = {"robot_id": robot_id, "rpc": "notify_wake_word"}

        def failure(msg: str) -> voice_pb2.WakeWordChangedResponse:
            return voice_pb2.WakeWordChangedResponse(success=False, message=msg)

        if not settings.GRPC.ENABLED:
            return failure("gRPC 未启用")

        # 仅推「已配置且启用」的 target；未配置端跳过（不计入失败），兼容只配一端的机器人
        provider = get_config_addr_provider()
        push_targets: List[Tuple[str, str]] = []
        for target in ("middleware", "agent"):
            addr = await provider.get_addr(robot_id, target)
            if addr:
                push_targets.append((target, addr))

        if not push_targets:
            return failure(f"middleware/agent 地址均未配置 (robot_id={robot_id})")

        async def call_one(
            target: str, addr: str
        ) -> voice_pb2.WakeWordChangedResponse:
            try:
                stub = await cls._get_stub_for_addr(addr)
                rpc: Callable[..., Awaitable[voice_pb2.WakeWordChangedResponse]] = (
                    stub.NotifyWakeWordChanged
                )
                return await rpc(request, timeout=settings.GRPC.TIMEOUT_SECONDS)
            except grpc.aio.AioRpcError as e:
                logger.warning(
                    "grpc config call failed method=NotifyWakeWordChanged "
                    "target=%s code=%s details=%s addr=%s ctx=%s",
                    target,
                    e.code(),
                    e.details(),
                    addr,
                    log_ctx,
                )
                return failure(f"{target} gRPC 调用失败: {e.code().name}")
            except Exception as e:  # noqa: BLE001 - 兜底，保证不阻塞另一端
                logger.exception(
                    "grpc config call unexpected error method=NotifyWakeWordChanged "
                    "target=%s addr=%s ctx=%s",
                    target,
                    addr,
                    log_ctx,
                )
                return failure(f"{target} gRPC 调用异常: {e}")

        resps = await asyncio.gather(*[call_one(t, a) for t, a in push_targets])

        failed = [
            f"{t}: {getattr(r, 'message', '') or '设备未响应'}"
            for (t, _), r in zip(push_targets, resps)
            if not getattr(r, "success", False)
        ]
        if not failed:
            return voice_pb2.WakeWordChangedResponse(success=True, message="ok")
        return failure("；".join(failed))

    @classmethod
    async def notify_tts(
        cls, robot_id: int, tts_voice: str, tts_speed: float, tts_volume: int
    ) -> voice_pb2.TTSConfigChangedResponse:
        request = voice_pb2.TTSConfigChangedRequest(
            robot_id=robot_id,
            tts_voice=tts_voice,
            tts_speed=tts_speed,
            tts_volume=tts_volume,
        )
        return await _dispatch_with_target(
            robot_id=robot_id,
            target="middleware",
            stub_factory=cls._get_stub_for_addr,
            method_name="NotifyTTSConfigChanged",
            request=request,
            failure_factory=lambda msg: voice_pb2.TTSConfigChangedResponse(
                success=False, message=msg
            ),
            log_ctx={"robot_id": robot_id, "rpc": "notify_tts"},
        )

    @classmethod
    async def notify_greeting_mode(
        cls, robot_id: int, greeting_mode: str
    ) -> voice_pb2.GreetingModeChangedResponse:
        """推送打招呼模式变更（wave/no_wave）：仅下发给 agent 端"""
        request = voice_pb2.GreetingModeChangedRequest(
            robot_id=robot_id, greeting_mode=greeting_mode or ""
        )
        return await _dispatch_with_target(
            robot_id=robot_id,
            target="agent",
            stub_factory=cls._get_stub_for_addr,
            method_name="NotifyGreetingModeChanged",
            request=request,
            failure_factory=lambda msg: voice_pb2.GreetingModeChangedResponse(
                success=False, message=msg
            ),
            log_ctx={
                "robot_id": robot_id,
                "rpc": "notify_greeting_mode",
                "greeting_mode": greeting_mode,
            },
        )

    @classmethod
    async def test_wake_word(
        cls, robot_id: int, wake_word: str
    ) -> voice_pb2.TestWakeWordResponse:
        request = voice_pb2.TestWakeWordRequest(
            robot_id=robot_id, wake_word=wake_word or ""
        )
        return await _dispatch_with_target(
            robot_id=robot_id,
            target="agent",
            stub_factory=cls._get_stub_for_addr,
            method_name="TestWakeWord",
            request=request,
            failure_factory=lambda msg: voice_pb2.TestWakeWordResponse(
                success=False, message=msg
            ),
            log_ctx={"robot_id": robot_id, "rpc": "test_wake_word"},
        )

    @classmethod
    async def test_tts(
        cls, robot_id: int, tts_voice: str, tts_speed: float, tts_volume: int, text: str
    ) -> voice_pb2.TestTTSConfigResponse:
        request = voice_pb2.TestTTSConfigRequest(
            robot_id=robot_id,
            tts_voice=tts_voice,
            tts_speed=tts_speed,
            tts_volume=tts_volume,
            text=text,
        )
        return await _dispatch_with_target(
            robot_id=robot_id,
            target="agent",
            stub_factory=cls._get_stub_for_addr,
            method_name="TestTTSConfig",
            request=request,
            failure_factory=lambda msg: voice_pb2.TestTTSConfigResponse(
                success=False, message=msg
            ),
            log_ctx={"robot_id": robot_id, "rpc": "test_tts"},
        )


# ==================== SpeedConfigClient ====================


class SpeedConfigClient:
    """行走速度配置 gRPC 客户端（走 middleware）"""

    _stubs_by_addr: Dict[str, speed_pb2_grpc.SpeedConfigServiceStub] = {}

    @classmethod
    async def _get_stub_for_addr(
        cls, addr: str
    ) -> speed_pb2_grpc.SpeedConfigServiceStub:
        if addr not in cls._stubs_by_addr:
            channel = await get_config_channel_by_addr(addr)
            cls._stubs_by_addr[addr] = speed_pb2_grpc.SpeedConfigServiceStub(channel)
        return cls._stubs_by_addr[addr]

    @classmethod
    async def notify_speed_level(
        cls, robot_id: int, speed_level: str
    ) -> speed_pb2.SpeedLevelChangedResponse:
        request = speed_pb2.SpeedLevelChangedRequest(
            robot_id=robot_id, speed_level=speed_level or ""
        )
        return await _dispatch_with_target(
            robot_id=robot_id,
            target="middleware",
            stub_factory=cls._get_stub_for_addr,
            method_name="NotifySpeedLevelChanged",
            request=request,
            failure_factory=lambda msg: speed_pb2.SpeedLevelChangedResponse(
                success=False, message=msg
            ),
            log_ctx={
                "robot_id": robot_id,
                "rpc": "notify_speed_level",
                "speed_level": speed_level,
            },
        )


# ==================== VideoMonitoringClient ====================


class VideoMonitoringClient:
    """视频监控启停 gRPC 客户端（走 middleware）

    实时控制类 RPC（fire-and-forget）：启动 / 停止视频监控。
    """

    _stubs_by_addr: Dict[str, video_pb2_grpc.VideoMonitoringServiceStub] = {}

    @classmethod
    async def _get_stub_for_addr(
        cls, addr: str
    ) -> video_pb2_grpc.VideoMonitoringServiceStub:
        if addr not in cls._stubs_by_addr:
            channel = await get_config_channel_by_addr(addr)
            cls._stubs_by_addr[addr] = video_pb2_grpc.VideoMonitoringServiceStub(
                channel
            )
        return cls._stubs_by_addr[addr]

    @classmethod
    async def notify_video_monitoring_changed(
        cls, robot_id: int, enabled: bool
    ) -> video_pb2.VideoMonitoringChangedResponse:
        request = video_pb2.VideoMonitoringChangedRequest(
            robot_id=robot_id,
            enabled=enabled,
        )
        return await _dispatch_with_target(
            robot_id=robot_id,
            target="middleware",
            stub_factory=cls._get_stub_for_addr,
            method_name="NotifyVideoMonitoringChanged",
            request=request,
            failure_factory=lambda msg: video_pb2.VideoMonitoringChangedResponse(
                success=False, message=msg
            ),
            log_ctx={
                "robot_id": robot_id,
                "rpc": "notify_video_monitoring",
                "enabled": enabled,
            },
        )


# ==================== BatteryConfigClient ====================


class BatteryConfigClient:
    """电量报警阈值配置 gRPC 客户端（走 agent）"""

    _stubs_by_addr: Dict[str, battery_pb2_grpc.BatteryConfigServiceStub] = {}

    @classmethod
    async def _get_stub_for_addr(
        cls, addr: str
    ) -> battery_pb2_grpc.BatteryConfigServiceStub:
        if addr not in cls._stubs_by_addr:
            channel = await get_config_channel_by_addr(addr)
            cls._stubs_by_addr[addr] = battery_pb2_grpc.BatteryConfigServiceStub(
                channel
            )
        return cls._stubs_by_addr[addr]

    @classmethod
    async def notify_battery_threshold(
        cls, robot_id: int, battery_threshold: int
    ) -> battery_pb2.BatteryThresholdChangedResponse:
        request = battery_pb2.BatteryThresholdChangedRequest(
            robot_id=robot_id, battery_threshold=battery_threshold
        )
        return await _dispatch_with_target(
            robot_id=robot_id,
            target="agent",
            stub_factory=cls._get_stub_for_addr,
            method_name="NotifyBatteryThresholdChanged",
            request=request,
            failure_factory=lambda msg: battery_pb2.BatteryThresholdChangedResponse(
                success=False, message=msg
            ),
            log_ctx={
                "robot_id": robot_id,
                "rpc": "notify_battery_threshold",
                "battery_threshold": battery_threshold,
            },
        )


# ==================== FaceRecognitionClient ====================


class FaceRecognitionClient:
    """人脸识别 TTS 库变更推送 gRPC 客户端

    人脸配置不绑定具体 robot，采用广播：遍历所有 grpc_config.agent 启用的 robot 逐个推送，
    任一成功即整体 success=True。
    """

    _stubs_by_addr: Dict[str, face_recognition_pb2_grpc.FaceRecognitionServiceStub] = {}

    @classmethod
    async def _get_stub_for_addr(
        cls, addr: str
    ) -> face_recognition_pb2_grpc.FaceRecognitionServiceStub:
        if addr not in cls._stubs_by_addr:
            channel = await get_config_channel_by_addr(addr)
            cls._stubs_by_addr[addr] = (
                face_recognition_pb2_grpc.FaceRecognitionServiceStub(channel)
            )
        return cls._stubs_by_addr[addr]

    @classmethod
    async def notify_changed(
        cls,
        operation: int,
        face_id: int = 0,
        person_name: str = "",
        photo_url: str = "",
        broadcast_text: str = "",
    ) -> face_recognition_pb2.FaceRecognitionChangedResponse:
        """广播推送人脸库增量变更给所有启用 agent 的 robot

        operation 取值：FACE_OPERATION_CREATE / UPDATE / DELETE
        create/update 需要全量字段；delete 仅需 face_id
        """
        if not settings.GRPC.ENABLED:
            return face_recognition_pb2.FaceRecognitionChangedResponse(
                success=False, message="gRPC 未启用"
            )

        targets: List[Tuple[int, str]] = (
            await get_config_addr_provider().find_addrs_by_target("agent")
        )
        if not targets:
            return face_recognition_pb2.FaceRecognitionChangedResponse(
                success=False, message="无启用 agent 的机器人"
            )

        item = face_recognition_pb2.FaceRecognitionItem(
            face_id=face_id,
            person_name=person_name,
            photo_url=photo_url,
            broadcast_text=broadcast_text,
        )
        request = face_recognition_pb2.FaceRecognitionChangedRequest(
            operation=operation, item=item
        )

        success_any = False
        last_msg = "全部失败"
        for robot_id, addr in targets:
            try:
                stub = await cls._get_stub_for_addr(addr)
                resp = await stub.NotifyFaceRecognitionChanged(
                    request, timeout=settings.GRPC.TIMEOUT_SECONDS
                )
                if getattr(resp, "success", False):
                    success_any = True
                    logger.info(
                        "face broadcast ok robot_id=%s addr=%s operation=%s face_id=%s",
                        robot_id,
                        addr,
                        operation,
                        face_id,
                    )
                else:
                    last_msg = getattr(resp, "message", "") or "设备未响应"
                    logger.warning(
                        "face broadcast failed robot_id=%s addr=%s msg=%s",
                        robot_id,
                        addr,
                        last_msg,
                    )
            except grpc.aio.AioRpcError as e:
                last_msg = f"gRPC 调用失败: {e.code().name}"
                logger.warning(
                    "face broadcast rpc error robot_id=%s addr=%s code=%s details=%s",
                    robot_id,
                    addr,
                    e.code(),
                    e.details(),
                )
            except Exception as e:  # noqa: BLE001 - 兜底，保证广播继续下一个
                last_msg = f"gRPC 调用异常: {e}"
                logger.exception(
                    "face broadcast raised robot_id=%s addr=%s",
                    robot_id,
                    addr,
                )

        if success_any:
            return face_recognition_pb2.FaceRecognitionChangedResponse(
                success=True, message="ok"
            )
        return face_recognition_pb2.FaceRecognitionChangedResponse(
            success=False, message=last_msg
        )

    @classmethod
    async def notify_create(
        cls, face_id: int, person_name: str, photo_url: str, broadcast_text: str
    ) -> face_recognition_pb2.FaceRecognitionChangedResponse:
        return await cls.notify_changed(
            face_recognition_pb2.FACE_OPERATION_CREATE,
            face_id=face_id,
            person_name=person_name,
            photo_url=photo_url,
            broadcast_text=broadcast_text,
        )

    @classmethod
    async def notify_update(
        cls, face_id: int, person_name: str, photo_url: str, broadcast_text: str
    ) -> face_recognition_pb2.FaceRecognitionChangedResponse:
        return await cls.notify_changed(
            face_recognition_pb2.FACE_OPERATION_UPDATE,
            face_id=face_id,
            person_name=person_name,
            photo_url=photo_url,
            broadcast_text=broadcast_text,
        )

    @classmethod
    async def notify_delete(
        cls, face_id: int
    ) -> face_recognition_pb2.FaceRecognitionChangedResponse:
        return await cls.notify_changed(
            face_recognition_pb2.FACE_OPERATION_DELETE, face_id=face_id
        )
