#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
视频监控相关定时任务
"""

from modules.scheduler.core.registry import scheduled_task


@scheduled_task(
    interval=30,
    name="清理过期视频监控观众",
    description="清理 Redis 中过期的 LiveKit 观众，空房间时关闭机器人摄像头",
    task_key="robot.cleanup_expired_video_viewers",
    is_system=True,
)
async def cleanup_expired_video_viewers():
    """清理过期视频监控观众"""
    from modules.robot.services.livekit_video_service import LiveKitVideoService

    await LiveKitVideoService.cleanup_expired_viewers()
    return {"status": "ok"}
