#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
在线用户监控服务
"""
import json
import logging
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.config import settings
from core.redis import get_redis_util
from core.utils.session_cache import get_session_cache
from app.models.sys.user import SysUser
from app.models.common.page import ResponsePageDataModel
from modules.admin.schemas.sys.online_user import OnlineUserResponse

logger = logging.getLogger(__name__)

SESSION_PREFIX = settings.JWT.SESSION_PREFIX


class OnlineUserService:
    """在线用户监控服务"""

    @staticmethod
    async def _collect_online_sessions(role: str = "admin") -> list[dict]:
        """从 Redis 收集所有在线会话信息"""
        redis_util = get_redis_util()
        sessions = []
        pattern = f"{SESSION_PREFIX}{role}*"

        async for key in redis_util.scan_iter(match=pattern):
            # 从 key 中提取 user_id: JWT_SESSION:admin123 -> 123
            user_id_str = key[len(f"{SESSION_PREFIX}{role}"):]
            try:
                user_id = int(user_id_str)
            except ValueError:
                continue

            all_fields = await redis_util.hgetall(key)
            if not all_fields:
                continue

            for sid, meta_raw in all_fields.items():
                if isinstance(sid, bytes):
                    sid = sid.decode("utf-8")
                if isinstance(meta_raw, bytes):
                    meta_raw = meta_raw.decode("utf-8")
                try:
                    meta = json.loads(meta_raw)
                except (json.JSONDecodeError, TypeError):
                    meta = {"session_id": sid}
                sessions.append({
                    "user_id": user_id,
                    "session_id": sid,
                    "ip": meta.get("ip", ""),
                    "user_agent": meta.get("user_agent", ""),
                    "login_time": meta.get("login_time", ""),
                })
        return sessions

    @staticmethod
    async def get_online_user_page(
        db: AsyncSession,
        role: str = "admin",
        username: str | None = None,
        ip: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> ResponsePageDataModel:
        """获取在线用户分页列表"""
        sessions = await OnlineUserService._collect_online_sessions(role)

        # 按 user_id 批量查询用户信息
        user_ids = list({s["user_id"] for s in sessions})
        user_map = {}
        if user_ids:
            stmt = select(SysUser).where(SysUser.id.in_(user_ids))
            result = await db.execute(stmt)
            for user in result.scalars().all():
                user_map[user.id] = user

        # 组装响应数据并过滤
        records = []
        for s in sessions:
            user = user_map.get(s["user_id"])
            if not user:
                continue
            if username and username not in (user.username or ""):
                continue
            if ip and ip not in (s.get("ip") or ""):
                continue
            records.append(OnlineUserResponse(
                user_id=user.id,
                username=user.username,
                nickname=user.nickname,
                avatar=user.avatar,
                session_id=s["session_id"],
                ip=s.get("ip", ""),
                user_agent=s.get("user_agent", ""),
                login_time=s.get("login_time", ""),
            ))

        # 按 login_time 降序
        records.sort(key=lambda r: r.login_time or "", reverse=True)

        # 手动分页
        total = len(records)
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        start = (page - 1) * page_size
        page_records = records[start:start + page_size]

        return ResponsePageDataModel(
            records=page_records,
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        )

    @staticmethod
    async def kick_user(user_id: int, session_id: str, role: str = "admin") -> bool:
        """踢除指定会话"""
        redis_key = SESSION_PREFIX + role + str(user_id)
        result = await get_redis_util().hdel(redis_key, session_id)
        get_session_cache().invalidate(redis_key, session_id)
        return result > 0

    @staticmethod
    async def kick_all_sessions(user_id: int, role: str = "admin") -> int:
        """踢除用户所有会话"""
        redis_key = SESSION_PREFIX + role + str(user_id)
        all_fields = await get_redis_util().hgetall(redis_key)
        count = len(all_fields) if all_fields else 0
        await get_redis_util().delete(redis_key)
        get_session_cache().invalidate(redis_key)
        return count

    @staticmethod
    async def get_online_count(role: str = "admin") -> int:
        """获取在线用户数（按独立用户计数）"""
        redis_util = get_redis_util()
        pattern = f"{SESSION_PREFIX}{role}*"
        user_ids = set()
        async for key in redis_util.scan_iter(match=pattern):
            user_id_str = key[len(f"{SESSION_PREFIX}{role}"):]
            try:
                user_ids.add(int(user_id_str))
            except ValueError:
                continue
        return len(user_ids)
