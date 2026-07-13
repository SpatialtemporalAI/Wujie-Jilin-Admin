#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
机器人状态记录管理服务
处理机器人状态记录相关的业务逻辑
"""
import logging
from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, Select
from sqlalchemy.orm import noload, selectinload
from typing import List, Tuple, Optional

from database.models.business.robot_status_record import RobotStatusRecord
from database.models.business.robot import Robot, RobotStatus
from database.utils.timezone import timezone
from core.exception.errors import NotFoundError
from modules.robot.schemas.robot_status_record import (
    RobotStatusRecordQueryParams,
    RobotLocationItem,
)

logger = logging.getLogger(__name__)

# 状态记录最新更新时间在该阈值内视为在线（秒）
STATUS_ONLINE_THRESHOLD_SECONDS = 60


class RobotStatusRecordService:
    """
    机器人状态记录管理服务类
    """

    @staticmethod
    def build_query(query_params: RobotStatusRecordQueryParams) -> Select:
        """
        构建机器人状态记录查询对象

        Args:
            query_params: 查询参数

        Returns:
            SQLAlchemy查询对象
        """
        base_query = select(RobotStatusRecord).options(
            noload(RobotStatusRecord.robot)
        )

        conditions = [RobotStatusRecord.deleted_at.is_(None)]
        if query_params.robot_id:
            conditions.append(RobotStatusRecord.robot_id == query_params.robot_id)

        if conditions:
            base_query = base_query.where(and_(*conditions))

        base_query = base_query.order_by(RobotStatusRecord.id.desc())

        return base_query

    @staticmethod
    async def get_list(
        db: AsyncSession, query_params: RobotStatusRecordQueryParams
    ) -> Tuple[List[RobotStatusRecord], int]:
        """
        获取机器人状态记录列表（分页）

        Args:
            db: 数据库会话
            query_params: 查询参数

        Returns:
            (状态记录列表, 总数)
        """
        try:
            logger.debug(
                "获取机器人状态记录列表，查询参数: %s",
                query_params.model_dump(exclude_none=True),
            )

            # 先验证机器人是否存在
            robot_result = await db.execute(
                select(Robot)
                .where(Robot.id == query_params.robot_id)
                .where(Robot.deleted_at.is_(None))
            )
            if not robot_result.scalar_one_or_none():
                raise NotFoundError(
                    msg=f"机器人 {query_params.robot_id} 不存在"
                )

            base_query = RobotStatusRecordService.build_query(query_params)

            count_query = select(func.count()).select_from(base_query.subquery())
            count_result = await db.execute(count_query)
            total = count_result.scalar() or 0

            query = base_query
            if query_params.page and query_params.page_size:
                offset = (query_params.page - 1) * query_params.page_size
                query = query.offset(offset).limit(query_params.page_size)

            result = await db.execute(query)
            records = result.scalars().all()

            logger.debug("获取机器人状态记录列表成功，共 %d 条记录", total)
            return records, total

        except NotFoundError:
            raise
        except Exception as e:
            logger.error("获取机器人状态记录列表失败: %s", str(e), exc_info=True)
            raise

    @staticmethod
    async def get_latest(
        db: AsyncSession, robot_id: int
    ) -> Optional[RobotStatusRecord]:
        """
        获取机器人最新的状态记录

        Args:
            db: 数据库会话
            robot_id: 机器人ID

        Returns:
            最新的状态记录，不存在则返回 None

        Raises:
            NotFoundError: 机器人不存在
        """
        try:
            logger.debug("获取机器人最新状态记录，机器人ID: %d", robot_id)

            # 先验证机器人是否存在
            robot_result = await db.execute(
                select(Robot)
                .where(Robot.id == robot_id)
                .where(Robot.deleted_at.is_(None))
            )
            if not robot_result.scalar_one_or_none():
                raise NotFoundError(msg=f"机器人 {robot_id} 不存在")

            result = await db.execute(
                select(RobotStatusRecord)
                .options(noload(RobotStatusRecord.robot))
                .where(RobotStatusRecord.robot_id == robot_id)
                .where(RobotStatusRecord.deleted_at.is_(None))
                .order_by(RobotStatusRecord.id.desc())
                .limit(1)
            )
            record = result.scalar_one_or_none()

            logger.debug(
                "获取机器人最新状态记录成功，机器人ID: %d，%s",
                robot_id,
                "有记录" if record else "无记录",
            )
            return record

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(
                "获取机器人最新状态记录失败: %s", str(e), exc_info=True
            )
            raise

    @staticmethod
    async def get_latest_with_online_status(
        db: AsyncSession, robot_id: int
    ) -> Tuple[Optional[RobotStatusRecord], RobotStatus]:
        """
        获取机器人最新状态记录，并根据记录更新时间刷新机器人 online/offline 状态。

        判定规则：
        - 最新状态记录存在且更新时间（无更新时间则取创建时间）在
          ``STATUS_ONLINE_THRESHOLD_SECONDS`` 秒内，判定为 online；
        - 无记录或记录超时，判定为 offline；
        - 机器人状态为 inactive 时，仅在记录满足在线条件时才升级为 online，
          否则保持 inactive 不变，避免覆盖管理员手动设置的未激活状态。

        Args:
            db: 数据库会话
            robot_id: 机器人ID

        Returns:
            (最新状态记录, 刷新后的机器人状态)

        Raises:
            NotFoundError: 机器人不存在
        """
        record = await RobotStatusRecordService.get_latest(db, robot_id)

        robot_result = await db.execute(
            select(Robot)
            .where(Robot.id == robot_id)
            .where(Robot.deleted_at.is_(None))
        )
        robot = robot_result.scalar_one_or_none()
        if not robot:
            raise NotFoundError(msg=f"机器人 {robot_id} 不存在")

        now = timezone.now()
        if record:
            last_seen = record.updated_at or record.created_at
            elapsed = (
                (now - last_seen).total_seconds()
                if last_seen
                else float("inf")
            )
            new_status = (
                RobotStatus.ONLINE
                if elapsed <= STATUS_ONLINE_THRESHOLD_SECONDS
                else RobotStatus.OFFLINE
            )
        else:
            new_status = RobotStatus.OFFLINE

        if robot.status != new_status and (
            robot.status != RobotStatus.INACTIVE or new_status == RobotStatus.ONLINE
        ):
            robot.status = new_status
            await db.commit()
            await db.refresh(robot)
            logger.info(
                "机器人状态已刷新，机器人ID: %d，状态: %s",
                robot_id,
                robot.status.value,
            )

        return record, robot.status

    @staticmethod
    async def get_map_robot_locations(
        db: AsyncSession, map_id: int
    ) -> List[RobotLocationItem]:
        """按地图查询其绑定机器人的实时位置（地图编辑器画布展示用）。

        位置数据由外部写入 DB，本方法只读。一次查询取出该地图下所有未删除机器人
        及其一对一状态记录，透传 location_info(JSON) 与 location(Text 历史字段)，
        由前端按优先级解析坐标。

        Args:
            db: 数据库会话
            map_id: 场景地图ID

        Returns:
            机器人位置项列表
        """
        try:
            result = await db.execute(
                select(Robot)
                .options(selectinload(Robot.status_record))
                .where(Robot.map_id == map_id)
                .where(Robot.deleted_at.is_(None))
                .order_by(Robot.id.asc())
            )
            robots = result.unique().scalars().all()

            items: List[RobotLocationItem] = []
            for robot in robots:
                sr = robot.status_record
                items.append(
                    RobotLocationItem(
                        id=robot.id,
                        name=robot.name,
                        status=(
                            robot.status.value
                            if hasattr(robot.status, "value")
                            else robot.status
                        ),
                        map_id=robot.map_id,
                        location_info=sr.location_info if sr else None,
                        location=sr.location if sr else None,
                    )
                )
            return items

        except Exception as e:
            logger.error(
                "按地图查询机器人位置失败 map_id=%s: %s",
                map_id,
                str(e),
                exc_info=True,
            )
            raise
