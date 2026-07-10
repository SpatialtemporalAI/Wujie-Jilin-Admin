#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
机器人视频监控 LiveKit 连接服务

- 维护 Redis 观众计数，保证同一机器人多用户同时观看时摄像头只开关一次
- 生成 LiveKit subscriber-only Token
- 提供心跳刷新与过期观众清理能力
"""

import logging
import re
import uuid
from datetime import timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.exception.errors import ConflictError, ServerError
from core.redis.redis_pool import RedisPool
from modules.grpc.config_client import VideoMonitoringClient
from modules.robot.services.robot_service import RobotService

logger = logging.getLogger(__name__)

# Redis key 前缀
_VIEWERS_SET_KEY = "wj:livekit:viewers:{serial_number}"
_VIEWER_TTL_KEY = "wj:livekit:viewer_ttl:{serial_number}:{viewer_id}"
_ROOM_HASH_KEY = "wj:livekit:room:{serial_number}"

# Lua 脚本：打开视频时原子地清理过期观众、SADD 观众、设置 TTL、刷新集合过期时间，并返回当前集合大小
_OPEN_VIEWER_LUA = """
local viewers_key = KEYS[1]
local ttl_key = KEYS[2]
local viewer_id = ARGV[1]
local ttl_seconds = tonumber(ARGV[2])
local set_ttl_seconds = tonumber(ARGV[3])

-- 从当前 viewer 的 ttl_key 推导出 viewer_ttl 前缀，用于校验其他观众是否过期
local prefix = ttl_key:sub(1, -#viewer_id - 1)

-- 清理集合中已过期的观众（对应的 ttl_key 已不存在）
local members = redis.call('SMEMBERS', viewers_key)
for _, member in ipairs(members) do
    local member_ttl_key = prefix .. member
    if redis.call('EXISTS', member_ttl_key) == 0 then
        redis.call('SREM', viewers_key, member)
    end
end

local added = redis.call('SADD', viewers_key, viewer_id)
redis.call('SETEX', ttl_key, ttl_seconds, 1)
redis.call('EXPIRE', viewers_key, set_ttl_seconds)
local count = redis.call('SCARD', viewers_key)
return {added, count}
"""

# Lua 脚本：关闭视频时原子地 SREM 观众、删除 TTL、刷新集合过期时间，并返回当前集合大小
_CLOSE_VIEWER_LUA = """
local viewers_key = KEYS[1]
local ttl_key = KEYS[2]
local viewer_id = ARGV[1]
local set_ttl_seconds = tonumber(ARGV[2])

local removed = redis.call('SREM', viewers_key, viewer_id)
redis.call('DEL', ttl_key)
redis.call('EXPIRE', viewers_key, set_ttl_seconds)
local count = redis.call('SCARD', viewers_key)
return {removed, count}
"""

# Lua 脚本：心跳时校验观众是否仍在集合中，若存在则刷新 TTL
_HEARTBEAT_LUA = """
local viewers_key = KEYS[1]
local ttl_key = KEYS[2]
local viewer_id = ARGV[1]
local ttl_seconds = tonumber(ARGV[2])

local is_member = redis.call('SISMEMBER', viewers_key, viewer_id)
if is_member == 1 then
    redis.call('SETEX', ttl_key, ttl_seconds, 1)
    return 1
end
return 0
"""


def _viewers_key(serial_number: str) -> str:
    return _VIEWERS_SET_KEY.format(serial_number=serial_number)


def _viewer_ttl_key(serial_number: str, viewer_id: str) -> str:
    return _VIEWER_TTL_KEY.format(serial_number=serial_number, viewer_id=viewer_id)


def _room_key(serial_number: str) -> str:
    return _ROOM_HASH_KEY.format(serial_number=serial_number)


# LiveKit 房间名限制：字母、数字、下划线、连字符，长度 1-64
_ROOM_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")


class LiveKitVideoService:
    """机器人视频监控 LiveKit 连接服务"""

    @staticmethod
    async def open_viewer(
        db: AsyncSession,
        robot_id: int,
        user_id: int,
    ) -> dict:
        """
        打开一个观众连接。

        流程：
        1. 校验机器人在线；
        2. 生成唯一 viewer_id；
        3. Redis 原子加 1；
        4. 若从 0 -> 1，通知机器人 middleware 开启摄像头；
        5. 生成 LiveKit Token 返回。

        失败时会回滚 Redis 计数。
        """
        await RobotService.ensure_robots_online(db, [robot_id])

        robot = await RobotService.get(db, robot_id)
        serial_number = robot.serial_number
        viewer_id = uuid.uuid4().hex

        if not settings.LIVEKIT.ENABLED:
            raise ServerError(msg="LiveKit 未启用，请联系管理员配置")

        if not settings.LIVEKIT.API_KEY or not settings.LIVEKIT.API_SECRET:
            raise ServerError(msg="LiveKit API Key/Secret 未配置")

        if not settings.LIVEKIT.WS_URL:
            raise ServerError(msg="LiveKit WS_URL 未配置")

        client = RedisPool.get_client()
        try:
            result = await client.eval(
                _OPEN_VIEWER_LUA,
                2,
                _viewers_key(serial_number),
                _viewer_ttl_key(serial_number, viewer_id),
                viewer_id,
                settings.LIVEKIT.VIEWER_HEARTBEAT_TTL_SECONDS,
                settings.LIVEKIT.VIEWERS_SET_TTL_SECONDS,
            )
            added, count = int(result[0]), int(result[1])
        except Exception as exc:
            logger.error("Redis 打开观众失败 robot_id=%s: %s", robot_id, exc)
            raise ServerError(msg="打开视频监控失败，请稍后重试") from exc

        # 需要开启摄像头：首个观众，或摄像头未处于开启状态（兼容 Redis 中残留过期观众）
        camera_on = await client.hget(_room_key(serial_number), "camera_on")
        should_turn_on = added == 1 and (count == 1 or camera_on != "1")
        logger.info(
            "视频监控观众状态 robot_id=%s added=%s count=%s camera_on=%s turn_on=%s",
            robot_id,
            added,
            count,
            camera_on,
            should_turn_on,
        )
        if should_turn_on:
            try:
                resp = await VideoMonitoringClient.notify_video_monitoring_changed(
                    robot_id=robot_id, enabled=True
                )
                if not resp.success:
                    logger.warning(
                        "开启摄像头 gRPC 失败 robot_id=%s msg=%s", robot_id, resp.message
                    )
                    await LiveKitVideoService._rollback_open(
                        serial_number, viewer_id
                    )
                    raise ConflictError(
                        msg=resp.message or "开启摄像头失败，请确保机器人已在线"
                    )
                await client.hset(_room_key(serial_number), "camera_on", "1")
            except ConflictError:
                raise
            except Exception as exc:
                logger.error(
                    "通知机器人开启摄像头异常 robot_id=%s: %s", robot_id, exc
                )
                await LiveKitVideoService._rollback_open(serial_number, viewer_id)
                raise ServerError(msg="开启摄像头失败，请稍后重试") from exc

        token = LiveKitVideoService._generate_token(serial_number, user_id, viewer_id)

        logger.info(
            "视频监控已打开 robot_id=%s serial=%s viewer=%s count=%s",
            robot_id,
            serial_number,
            viewer_id,
            count,
        )
        return {
            "room": serial_number,
            "token": token,
            "server_url": settings.LIVEKIT.WS_URL,
            "viewer_id": viewer_id,
            "robot_serial_number": serial_number,
        }

    @staticmethod
    async def close_viewer(
        db: AsyncSession,
        robot_id: int,
        viewer_id: str,
    ) -> None:
        """
        关闭一个观众连接。

        流程：
        1. 从 Redis 原子减 1；
        2. 若从 1 -> 0，通知机器人 middleware 关闭摄像头。
        """
        robot = await RobotService.get(db, robot_id)
        serial_number = robot.serial_number

        client = RedisPool.get_client()
        try:
            result = await client.eval(
                _CLOSE_VIEWER_LUA,
                2,
                _viewers_key(serial_number),
                _viewer_ttl_key(serial_number, viewer_id),
                viewer_id,
                settings.LIVEKIT.VIEWERS_SET_TTL_SECONDS,
            )
            removed, count = int(result[0]), int(result[1])
        except Exception as exc:
            logger.error("Redis 关闭观众失败 robot_id=%s: %s", robot_id, exc)
            raise ServerError(msg="关闭视频监控失败，请稍后重试") from exc

        if removed == 0:
            logger.warning(
                "关闭视频监控时观众不存在 robot_id=%s viewer=%s", robot_id, viewer_id
            )

        # 最后一个观众离开（关闭前 count 为 1）：通知机器人关闭摄像头
        if removed == 1 and count == 0:
            try:
                resp = await VideoMonitoringClient.notify_video_monitoring_changed(
                    robot_id=robot_id, enabled=False
                )
                if not resp.success:
                    logger.warning(
                        "关闭摄像头 gRPC 失败 robot_id=%s msg=%s", robot_id, resp.message
                    )
                else:
                    await client.hset(_room_key(serial_number), "camera_on", "0")
            except Exception as exc:
                logger.error(
                    "通知机器人关闭摄像头异常 robot_id=%s: %s", robot_id, exc
                )

        logger.info(
            "视频监控已关闭 robot_id=%s serial=%s viewer=%s count=%s",
            robot_id,
            serial_number,
            viewer_id,
            count,
        )

    @staticmethod
    async def heartbeat(
        db: AsyncSession,
        robot_id: int,
        viewer_id: str,
    ) -> bool:
        """刷新观众心跳 TTL。若观众已不存在返回 False。"""
        robot = await RobotService.get(db, robot_id)
        serial_number = robot.serial_number

        client = RedisPool.get_client()
        try:
            result = await client.eval(
                _HEARTBEAT_LUA,
                2,
                _viewers_key(serial_number),
                _viewer_ttl_key(serial_number, viewer_id),
                viewer_id,
                settings.LIVEKIT.VIEWER_HEARTBEAT_TTL_SECONDS,
            )
            return bool(int(result))
        except Exception as exc:
            logger.error("视频监控心跳失败 robot_id=%s: %s", robot_id, exc)
            return False

    @staticmethod
    async def cleanup_expired_viewers() -> None:
        """
        定时清理过期观众。

        扫描所有观众集合，移除 TTL 已过期的 viewer_id；若集合变空且 camera_on=1，
        则通知对应机器人关闭摄像头。
        """
        client = RedisPool.get_client()
        try:
            async for key in client.scan_iter(
                match=_VIEWERS_SET_KEY.format(serial_number="*"), count=50
            ):
                serial_number = key.split(":")[-1]
                try:
                    await LiveKitVideoService._cleanup_room(client, serial_number)
                except Exception as exc:
                    logger.error(
                        "清理房间 %s 过期观众失败: %s", serial_number, exc
                    )
        except Exception as exc:
            logger.error("扫描 LiveKit 观众集合失败: %s", exc)

    @staticmethod
    async def _cleanup_room(client, serial_number: str) -> None:
        """清理单个房间过期观众，必要时关闭摄像头。"""
        viewers_key = _viewers_key(serial_number)
        viewer_ids = await client.smembers(viewers_key)
        if not viewer_ids:
            return

        expired_viewers = []
        for viewer_id in viewer_ids:
            ttl_key = _viewer_ttl_key(serial_number, viewer_id)
            if not await client.exists(ttl_key):
                expired_viewers.append(viewer_id)

        if not expired_viewers:
            return

        removed = await client.srem(viewers_key, *expired_viewers)
        count = await client.scard(viewers_key)
        logger.info(
            "清理过期观众 serial=%s removed=%s remaining=%s",
            serial_number,
            removed,
            count,
        )

        if count == 0:
            camera_on = await client.hget(_room_key(serial_number), "camera_on")
            if camera_on == "1":
                # 尝试关闭摄像头；这里无法直接映射 serial_number -> robot_id，
                # 因此通过数据库反查 robot_id
                from database.db_manager import get_session

                async for db in get_session():
                    from database.models.business.robot import Robot
                    from sqlalchemy import select

                    result = await db.execute(
                        select(Robot.id).where(
                            Robot.serial_number == serial_number,
                            Robot.deleted_at.is_(None),
                        )
                    )
                    robot_id = result.scalar_one_or_none()
                    if robot_id is None:
                        logger.warning(
                            "清理时发现无对应机器人 serial=%s", serial_number
                        )
                        return

                    try:
                        resp = await VideoMonitoringClient.notify_video_monitoring_changed(
                            robot_id=robot_id, enabled=False
                        )
                        if resp.success:
                            await client.hset(
                                _room_key(serial_number), "camera_on", "0"
                            )
                            logger.info(
                                "清理任务已关闭摄像头 robot_id=%s", robot_id
                            )
                        else:
                            logger.warning(
                                "清理任务关闭摄像头失败 robot_id=%s msg=%s",
                                robot_id,
                                resp.message,
                            )
                    except Exception as exc:
                        logger.error(
                            "清理任务关闭摄像头异常 robot_id=%s: %s", robot_id, exc
                        )
                    break

    @staticmethod
    async def reset_room(serial_number: str) -> None:
        """强制清空某机器人的视频监控房间状态（机器人离线/删除时调用）。"""
        client = RedisPool.get_client()
        viewers_key = _viewers_key(serial_number)
        room_key = _room_key(serial_number)

        try:
            viewer_ids = await client.smembers(viewers_key)
            if viewer_ids:
                ttl_keys = [_viewer_ttl_key(serial_number, vid) for vid in viewer_ids]
                await client.delete(*ttl_keys)
            await client.delete(viewers_key)
            await client.delete(room_key)
            logger.info("视频监控房间已重置 serial=%s", serial_number)
        except Exception as exc:
            logger.error("重置视频监控房间失败 serial=%s: %s", serial_number, exc)

    @staticmethod
    async def _rollback_open(serial_number: str, viewer_id: str) -> None:
        """打开失败时回滚 Redis 计数。"""
        client = RedisPool.get_client()
        try:
            await client.srem(_viewers_key(serial_number), viewer_id)
            await client.delete(_viewer_ttl_key(serial_number, viewer_id))
        except Exception as exc:
            logger.error(
                "回滚打开观众失败 serial=%s viewer=%s: %s",
                serial_number,
                viewer_id,
                exc,
            )

    @staticmethod
    def _generate_token(serial_number: str, user_id: int, viewer_id: str) -> str:
        """生成 LiveKit subscriber-only Token。"""
        if not _ROOM_NAME_PATTERN.match(serial_number):
            raise ServerError(
                msg=f"机器人序列号 '{serial_number}' 不符合 LiveKit 房间名规则，"
                f"只能包含字母、数字、下划线、连字符，长度 1-64"
            )
        try:
            from livekit import api

            identity = f"viewer:{user_id}:{viewer_id}"
            ttl = settings.LIVEKIT.TOKEN_TTL_SECONDS
            token_builder = (
                api.AccessToken(
                    settings.LIVEKIT.API_KEY, settings.LIVEKIT.API_SECRET
                )
                .with_identity(identity)
                .with_name(identity)
                .with_grants(
                    api.VideoGrants(
                        room_join=True,
                        room=serial_number,
                        can_subscribe=True,
                        can_publish=False,
                        can_publish_data=False,
                    )
                )
            )
            if ttl > 0:
                token_builder = token_builder.with_ttl(timedelta(seconds=ttl))
            token = token_builder.to_jwt()
            logger.info(
                "生成 LiveKit Token serial=%s user_id=%s viewer=%s ttl=%s key=%s...",
                serial_number,
                user_id,
                viewer_id,
                ttl,
                settings.LIVEKIT.API_KEY[:4] if settings.LIVEKIT.API_KEY else None,
            )
            return token
        except Exception as exc:
            logger.error("生成 LiveKit Token 失败: %s", exc)
            raise ServerError(msg="生成视频连接凭证失败") from exc
