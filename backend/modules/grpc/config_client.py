"""
ConfigService gRPC 客户端

覆盖 voice / speed / battery / face_recognition 四个配置类 RPC：
- 通用 _dispatch 内核：统一处理 ENABLED 短路、stub 复用、超时、异常吞掉、日志
- 每个业务一个 Client 类（类方法风格，无需实例化），方法签名强类型

调用约定：
- 所有方法在 GRPC.ENABLED=false 时返回 success=False 的哨兵响应，不抛异常
- 所有方法在 gRPC 调用失败时返回 success=False 的失败响应，不抛异常
- 业务层据此决定提示文案，而非冒泡 500 给前端
"""
import logging
from typing import Any, Awaitable, Callable, TypeVar

import grpc

from app.grpc.generated.config import (
    battery_pb2,
    battery_pb2_grpc,
    face_recognition_pb2,
    face_recognition_pb2_grpc,
    speed_pb2,
    speed_pb2_grpc,
    voice_pb2,
    voice_pb2_grpc,
)

from core.config import settings
from modules.grpc.channel import get_config_channel

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def _dispatch(
    stub_coro_factory: Callable[[], Awaitable[Any]],
    method_name: str,
    request: Any,
    failure_factory: Callable[[str], T],
    log_ctx: dict,
) -> T:
    """通用调度内核

    Args:
        stub_coro_factory: 返回 stub 协程的工厂（带缓存）
        method_name: stub 上的 RPC 方法名（如 "NotifyWakeWordChanged"）
        request: proto 请求对象
        failure_factory: 失败时构造响应的工厂，入参为 message
        log_ctx: 日志上下文（robot_id / operation 等）

    Returns:
        proto 响应对象；ENABLED=false 或调用异常时返回 failure_factory 构造的哨兵响应
    """
    if not settings.GRPC.ENABLED:
        return failure_factory("gRPC 未启用")

    try:
        stub = await stub_coro_factory()
        rpc: Callable[..., Awaitable[T]] = getattr(stub, method_name)
        return await rpc(request, timeout=settings.GRPC.TIMEOUT_SECONDS)
    except grpc.aio.AioRpcError as e:
        logger.warning(
            "grpc config call failed method=%s code=%s details=%s ctx=%s",
            method_name,
            e.code(),
            e.details(),
            log_ctx,
        )
        return failure_factory(f"gRPC 调用失败: {e.code().name}")
    except Exception as e:  # noqa: BLE001 - 兜底，保证不阻塞业务
        logger.exception(
            "grpc config call unexpected error method=%s ctx=%s",
            method_name,
            log_ctx,
        )
        return failure_factory(f"gRPC 调用异常: {e}")


# ==================== VoiceConfigClient ====================


class VoiceConfigClient:
    """语音配置 gRPC 客户端（唤醒词 + TTS 音色/语速/音量）"""

    _stub: voice_pb2_grpc.VoiceConfigServiceStub | None = None

    @classmethod
    async def _ensure_stub(cls) -> voice_pb2_grpc.VoiceConfigServiceStub:
        """协程入口：先确保 channel 已建好，再创建/复用 stub"""
        if cls._stub is None:
            channel = await get_config_channel()
            cls._stub = voice_pb2_grpc.VoiceConfigServiceStub(channel)
        return cls._stub

    @classmethod
    def _reset_stub(cls) -> None:
        """供 channel 重建时清空缓存（扩展点，本次未启用）"""
        cls._stub = None

    @classmethod
    async def notify_wake_word(
        cls, robot_id: int, wake_word_enabled: bool, wake_word: str
    ) -> voice_pb2.WakeWordChangedResponse:
        request = voice_pb2.WakeWordChangedRequest(
            robot_id=robot_id,
            wake_word_enabled=wake_word_enabled,
            wake_word=wake_word or "",
        )
        return await _dispatch(
            cls._ensure_stub,
            "NotifyWakeWordChanged",
            request,
            lambda msg: voice_pb2.WakeWordChangedResponse(success=False, message=msg),
            {"robot_id": robot_id, "rpc": "notify_wake_word"},
        )

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
        return await _dispatch(
            cls._ensure_stub,
            "NotifyTTSConfigChanged",
            request,
            lambda msg: voice_pb2.TTSConfigChangedResponse(success=False, message=msg),
            {"robot_id": robot_id, "rpc": "notify_tts"},
        )

    @classmethod
    async def test_wake_word(
        cls, robot_id: int, wake_word: str
    ) -> voice_pb2.TestWakeWordResponse:
        request = voice_pb2.TestWakeWordRequest(
            robot_id=robot_id, wake_word=wake_word or ""
        )
        return await _dispatch(
            cls._ensure_stub,
            "TestWakeWord",
            request,
            lambda msg: voice_pb2.TestWakeWordResponse(success=False, message=msg),
            {"robot_id": robot_id, "rpc": "test_wake_word"},
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
        return await _dispatch(
            cls._ensure_stub,
            "TestTTSConfig",
            request,
            lambda msg: voice_pb2.TestTTSConfigResponse(success=False, message=msg),
            {"robot_id": robot_id, "rpc": "test_tts"},
        )


# ==================== SpeedConfigClient ====================


class SpeedConfigClient:
    """行走速度配置 gRPC 客户端"""

    _stub: speed_pb2_grpc.SpeedConfigServiceStub | None = None

    @classmethod
    async def _ensure_stub(cls) -> speed_pb2_grpc.SpeedConfigServiceStub:
        if cls._stub is None:
            channel = await get_config_channel()
            cls._stub = speed_pb2_grpc.SpeedConfigServiceStub(channel)
        return cls._stub

    @classmethod
    async def notify_speed_level(
        cls, robot_id: int, speed_level: str
    ) -> speed_pb2.SpeedLevelChangedResponse:
        request = speed_pb2.SpeedLevelChangedRequest(
            robot_id=robot_id, speed_level=speed_level or ""
        )
        return await _dispatch(
            cls._ensure_stub,
            "NotifySpeedLevelChanged",
            request,
            lambda msg: speed_pb2.SpeedLevelChangedResponse(success=False, message=msg),
            {
                "robot_id": robot_id,
                "rpc": "notify_speed_level",
                "speed_level": speed_level,
            },
        )


# ==================== BatteryConfigClient ====================


class BatteryConfigClient:
    """电量报警阈值配置 gRPC 客户端"""

    _stub: battery_pb2_grpc.BatteryConfigServiceStub | None = None

    @classmethod
    async def _ensure_stub(cls) -> battery_pb2_grpc.BatteryConfigServiceStub:
        if cls._stub is None:
            channel = await get_config_channel()
            cls._stub = battery_pb2_grpc.BatteryConfigServiceStub(channel)
        return cls._stub

    @classmethod
    async def notify_battery_threshold(
        cls, robot_id: int, battery_threshold: int
    ) -> battery_pb2.BatteryThresholdChangedResponse:
        request = battery_pb2.BatteryThresholdChangedRequest(
            robot_id=robot_id, battery_threshold=battery_threshold
        )
        return await _dispatch(
            cls._ensure_stub,
            "NotifyBatteryThresholdChanged",
            request,
            lambda msg: battery_pb2.BatteryThresholdChangedResponse(
                success=False, message=msg
            ),
            {
                "robot_id": robot_id,
                "rpc": "notify_battery_threshold",
                "battery_threshold": battery_threshold,
            },
        )


# ==================== FaceRecognitionClient ====================


class FaceRecognitionClient:
    """人脸识别 TTS 库变更推送 gRPC 客户端"""

    _stub: face_recognition_pb2_grpc.FaceRecognitionServiceStub | None = None

    @classmethod
    async def _ensure_stub(cls) -> face_recognition_pb2_grpc.FaceRecognitionServiceStub:
        if cls._stub is None:
            channel = await get_config_channel()
            cls._stub = face_recognition_pb2_grpc.FaceRecognitionServiceStub(channel)
        return cls._stub

    @classmethod
    async def notify_changed(
        cls,
        operation: int,
        face_id: int = 0,
        person_name: str = "",
        photo_url: str = "",
        broadcast_text: str = "",
    ) -> face_recognition_pb2.FaceRecognitionChangedResponse:
        """推送人脸库增量变更

        operation 取值：FACE_OPERATION_CREATE / UPDATE / DELETE
        create/update 需要全量字段；delete 仅需 face_id
        """
        item = face_recognition_pb2.FaceRecognitionItem(
            face_id=face_id,
            person_name=person_name,
            photo_url=photo_url,
            broadcast_text=broadcast_text,
        )
        request = face_recognition_pb2.FaceRecognitionChangedRequest(
            operation=operation, item=item
        )
        return await _dispatch(
            cls._ensure_stub,
            "NotifyFaceRecognitionChanged",
            request,
            lambda msg: face_recognition_pb2.FaceRecognitionChangedResponse(
                success=False, message=msg
            ),
            {
                "rpc": "notify_face_recognition",
                "operation": operation,
                "face_id": face_id,
            },
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
