#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
机器人管理服务
处理机器人相关的业务逻辑
"""
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, Select, update
from sqlalchemy.orm import noload
from typing import List, Tuple

from database.models.business.robot import Robot, RobotStatus
from database.models.business.robot_status_record import RobotStatusRecord
from database.models.business.robot_voice_config import (
    RobotVoiceConfig,
    DEFAULT_WAKE_WORD_ENABLED,
    DEFAULT_WAKE_WORD,
    DEFAULT_TTS_VOICE,
    DEFAULT_TTS_SPEED,
    DEFAULT_TTS_VOLUME,
)
from database.models.business.robot_event_log import RobotEventLog
from database.models.business.robot_model import RobotModel
from database.models.business.scene_map import SceneMap
from database.models.business.task import task_robot_association
from database.utils.timezone import timezone
from core.config import settings
from core.exception.errors import NotFoundError, ConflictError
from modules.robot.schemas.robot import (
    RobotCreate,
    RobotUpdate,
    RobotQueryParams,
    RobotGrpcConfigPayload,
    RobotMapBindingUpdate,
)
from modules.robot.services.robot_schema_service import RobotSchemaService

logger = logging.getLogger(__name__)


class RobotService:
    """
    机器人管理服务类
    """

    @staticmethod
    def build_query(query_params: RobotQueryParams) -> Select:
        """
        构建机器人查询对象（关联 RobotModel 获取 model_name）

        Args:
            query_params: 查询参数

        Returns:
            SQLAlchemy查询对象
        """
        base_query = (
            select(Robot)
            .options(noload(Robot.status_record))
        )

        conditions = [Robot.deleted_at.is_(None)]
        if query_params.name:
            conditions.append(Robot.name.contains(query_params.name))
        if query_params.serial_number:
            conditions.append(Robot.serial_number.contains(query_params.serial_number))
        if query_params.status:
            conditions.append(Robot.status == RobotStatus(query_params.status))
        if query_params.model_id:
            conditions.append(Robot.model_id == query_params.model_id)
        if query_params.map_id:
            conditions.append(Robot.map_id == query_params.map_id)

        if conditions:
            base_query = base_query.where(and_(*conditions))

        base_query = base_query.order_by(Robot.id.desc())

        return base_query

    @staticmethod
    async def get_list(
        db: AsyncSession, query_params: RobotQueryParams
    ) -> Tuple[List[Robot], int]:
        """
        获取机器人列表（分页）

        Args:
            db: 数据库会话
            query_params: 查询参数

        Returns:
            (机器人列表, 总数)
        """
        try:
            await RobotSchemaService.ensure_robot_map_binding(db)
            logger.debug(
                "获取机器人列表，查询参数: %s",
                query_params.model_dump(exclude_none=True),
            )

            base_query = RobotService.build_query(query_params)

            count_query = select(func.count()).select_from(base_query.subquery())
            count_result = await db.execute(count_query)
            total = count_result.scalar() or 0

            query = base_query
            if query_params.page and query_params.page_size:
                offset = (query_params.page - 1) * query_params.page_size
                query = query.offset(offset).limit(query_params.page_size)

            result = await db.execute(query)
            records = result.scalars().all()

            logger.debug("获取机器人列表成功，共 %d 条记录", total)
            return records, total

        except Exception as e:
            logger.error("获取机器人列表失败: %s", str(e), exc_info=True)
            raise

    @staticmethod
    async def get_all(db: AsyncSession) -> List[Robot]:
        """
        获取所有未删除的机器人（不分页，用于下拉选择）

        与 build_query 保持一致的可见性过滤（deleted_at），但不做 status 过滤——
        inactive 设备同样可作为有效下拉项。仅登录认证即可访问，无 require_permission。
        """
        result = await db.execute(
            select(Robot)
            .where(Robot.deleted_at.is_(None))
            .order_by(Robot.id.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def ensure_robots_online(db: AsyncSession, robot_ids: List[int]) -> None:
        """校验机器人在线状态：存在非 online 的机器人时抛 ConflictError。

        用于唤醒词测试、语音合成测试、启动任务等需要实时下发到机器人的前置校验。
        在线判定以 Robot.status == RobotStatus.ONLINE 为准；查询不到（已删除/不存在）
        的机器人不计入，沿用各调用方既有的"不校验存在性"约定。

        Args:
            db: 数据库会话
            robot_ids: 待校验的机器人ID列表

        Raises:
            ConflictError: 存在非在线状态的机器人（消息中列出机器人名称）
        """
        if not robot_ids:
            return
        result = await db.execute(
            select(Robot.id, Robot.name, Robot.status).where(
                Robot.id.in_(robot_ids),
                Robot.deleted_at.is_(None),
            )
        )
        offline_names = [
            name
            for _, name, status in result.all()
            if status != RobotStatus.ONLINE
        ]
        if offline_names:
            raise ConflictError(
                msg=f"机器人 {'、'.join(offline_names)} 不在线，请确保机器人已在线"
            )

    @staticmethod
    async def get(db: AsyncSession, robot_id: int) -> Robot:
        """
        获取单个机器人

        Args:
            db: 数据库会话
            robot_id: 机器人ID

        Returns:
            机器人对象

        Raises:
            NotFoundError: 机器人不存在
        """
        try:
            logger.debug("获取机器人详情，机器人ID: %d", robot_id)

            result = await db.execute(
                select(Robot)
                .options(noload(Robot.status_record))
                .where(Robot.id == robot_id)
                .where(Robot.deleted_at.is_(None))
            )
            robot_obj = result.scalar_one_or_none()

            if not robot_obj:
                logger.warning("机器人不存在，机器人ID: %d", robot_id)
                raise NotFoundError(msg=f"机器人 {robot_id} 不存在")

            logger.debug("获取机器人详情成功，机器人ID: %d", robot_id)
            return robot_obj

        except NotFoundError:
            raise
        except Exception as e:
            logger.error("获取机器人详情失败: %s", str(e), exc_info=True)
            raise

    @staticmethod
    async def create(db: AsyncSession, robot_in: RobotCreate) -> Robot:
        """
        创建机器人

        Args:
            db: 数据库会话
            robot_in: 机器人创建请求

        Returns:
            创建后的机器人对象

        Raises:
            NotFoundError: 关联型号不存在
            ConflictError: 序列号已存在
        """
        try:
            logger.info(
                "创建机器人，请求数据: %s",
                robot_in.model_dump(exclude_none=True),
            )

            # 检查关联型号是否存在
            model_result = await db.execute(
                select(RobotModel)
                .where(RobotModel.id == robot_in.model_id)
                .where(RobotModel.deleted_at.is_(None))
            )
            if not model_result.scalar_one_or_none():
                logger.warning("关联型号不存在，型号ID: %d", robot_in.model_id)
                raise NotFoundError(msg=f"机器人型号 {robot_in.model_id} 不存在")

            if robot_in.map_id is not None:
                map_result = await db.execute(
                    select(SceneMap)
                    .where(SceneMap.id == robot_in.map_id)
                    .where(SceneMap.deleted_at.is_(None))
                )
                if not map_result.scalar_one_or_none():
                    raise NotFoundError(msg=f"场景地图 {robot_in.map_id} 不存在")

            # 检查序列号是否已存在
            sn_result = await db.execute(
                select(Robot)
                .where(Robot.serial_number == robot_in.serial_number)
                .where(Robot.deleted_at.is_(None))
            )
            if sn_result.scalar_one_or_none():
                logger.warning("序列号已存在: %s", robot_in.serial_number)
                raise ConflictError(msg=f"序列号 {robot_in.serial_number} 已存在")

            robot_obj = Robot(
                name=robot_in.name,
                model_id=robot_in.model_id,
                serial_number=robot_in.serial_number,
                map_id=robot_in.map_id,
                status=RobotStatus(robot_in.status),
                speed_level=robot_in.speed_level,
                battery_threshold=robot_in.battery_threshold,
            )

            db.add(robot_obj)
            await db.flush()

            status_record = RobotStatusRecord(robot_id=robot_obj.id)
            db.add(status_record)

            # 初始化默认语音配置：唤醒词默认启用，唤醒词为「小护小护」
            voice_config = RobotVoiceConfig(
                robot_id=robot_obj.id,
                wake_word_enabled=DEFAULT_WAKE_WORD_ENABLED,
                wake_word=DEFAULT_WAKE_WORD,
                tts_voice=DEFAULT_TTS_VOICE,
                tts_speed=DEFAULT_TTS_SPEED,
                tts_volume=DEFAULT_TTS_VOLUME,
            )
            db.add(voice_config)

            await db.commit()
            await db.refresh(robot_obj)

            logger.info("创建机器人成功，机器人ID: %d", robot_obj.id)
            return robot_obj

        except (NotFoundError, ConflictError):
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error("创建机器人失败: %s", str(e), exc_info=True)
            raise

    @staticmethod
    async def update(
        db: AsyncSession, robot_id: int, robot_in: RobotUpdate
    ) -> Robot:
        """
        更新机器人

        Args:
            db: 数据库会话
            robot_id: 机器人ID
            robot_in: 机器人更新请求

        Returns:
            更新后的机器人对象

        Raises:
            NotFoundError: 机器人不存在
            ConflictError: 序列号已被其他机器人占用
        """
        try:
            logger.info(
                "更新机器人，机器人ID: %d，请求数据: %s",
                robot_id,
                robot_in.model_dump(exclude_none=True),
            )

            result = await db.execute(
                select(Robot)
                .options(noload(Robot.status_record))
                .where(Robot.id == robot_id)
                .where(Robot.deleted_at.is_(None))
            )
            existing = result.scalar_one_or_none()

            if not existing:
                logger.warning("机器人不存在，机器人ID: %d", robot_id)
                raise NotFoundError(msg=f"机器人 {robot_id} 不存在")

            # 如果更新序列号，检查唯一性
            update_data = robot_in.model_dump(exclude_unset=True)
            if "serial_number" in update_data and update_data["serial_number"] != existing.serial_number:
                sn_result = await db.execute(
                    select(Robot)
                    .where(Robot.serial_number == update_data["serial_number"])
                    .where(Robot.deleted_at.is_(None))
                )
                if sn_result.scalar_one_or_none():
                    logger.warning(
                        "序列号已被占用: %s", update_data["serial_number"]
                    )
                    raise ConflictError(
                        msg=f"序列号 {update_data['serial_number']} 已存在"
                    )

            # 如果更新型号，检查型号是否存在
            if "model_id" in update_data:
                model_result = await db.execute(
                    select(RobotModel)
                    .where(RobotModel.id == update_data["model_id"])
                    .where(RobotModel.deleted_at.is_(None))
                )
                if not model_result.scalar_one_or_none():
                    raise NotFoundError(
                        msg=f"机器人型号 {update_data['model_id']} 不存在"
                    )

            if "map_id" in update_data and update_data["map_id"] is not None:
                map_result = await db.execute(
                    select(SceneMap)
                    .where(SceneMap.id == update_data["map_id"])
                    .where(SceneMap.deleted_at.is_(None))
                )
                if not map_result.scalar_one_or_none():
                    raise NotFoundError(
                        msg=f"场景地图 {update_data['map_id']} 不存在"
                    )

            # 如果更新状态，转换枚举
            if "status" in update_data and update_data["status"] is not None:
                update_data["status"] = RobotStatus(update_data["status"])

            for field, value in update_data.items():
                setattr(existing, field, value)

            await db.commit()
            await db.refresh(existing)

            logger.info("更新机器人成功，机器人ID: %d", robot_id)
            return existing

        except (NotFoundError, ConflictError):
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error("更新机器人失败: %s", str(e), exc_info=True)
            raise

    @staticmethod
    async def delete(db: AsyncSession, robot_id: int) -> bool:
        """
        删除机器人（软删除，并联动清理关联记录）

        - 一对一/一对多关联表 status_record / voice_config / event_log 外键无
          ondelete 级联，物理删除会触发外键约束，故同步软删除；
        - 多对多关联表 task_robot 无软删除字段，且 robot 为软删除不会触发
          ondelete=CASCADE，故物理删除该 robot 的全部任务关联（即从关联任务
          列表中移除该机器人），避免留下孤儿关联。

        Args:
            db: 数据库会话
            robot_id: 机器人ID

        Returns:
            是否删除成功

        Raises:
            NotFoundError: 机器人不存在
        """
        try:
            logger.info("删除机器人，机器人ID: %d", robot_id)

            result = await db.execute(
                select(Robot)
                .options(noload(Robot.status_record))
                .where(Robot.id == robot_id)
                .where(Robot.deleted_at.is_(None))
            )
            robot_obj = result.scalar_one_or_none()

            if not robot_obj:
                logger.warning("机器人不存在，机器人ID: %d", robot_id)
                raise NotFoundError(msg=f"机器人 {robot_id} 不存在")

            now = timezone.now()
            robot_obj.deleted_at = now

            await db.execute(
                update(RobotStatusRecord)
                .where(
                    RobotStatusRecord.robot_id == robot_id,
                    RobotStatusRecord.deleted_at.is_(None),
                )
                .values(deleted_at=now)
            )

            await db.execute(
                update(RobotVoiceConfig)
                .where(
                    RobotVoiceConfig.robot_id == robot_id,
                    RobotVoiceConfig.deleted_at.is_(None),
                )
                .values(deleted_at=now)
            )

            await db.execute(
                update(RobotEventLog)
                .where(
                    RobotEventLog.robot_id == robot_id,
                    RobotEventLog.deleted_at.is_(None),
                )
                .values(deleted_at=now)
            )

            # 解除该机器人与所有任务的关联（多对多关联表物理删除）：
            # task_robot 无软删除字段，且 robot 为软删除不会触发 ondelete=CASCADE，
            # 需手动清理，否则会留下孤儿关联。
            await db.execute(
                task_robot_association.delete().where(
                    task_robot_association.c.robot_id == robot_id
                )
            )

            await db.commit()

            logger.info("删除机器人成功，机器人ID: %d", robot_id)
            return True

        except NotFoundError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error("删除机器人失败: %s", str(e), exc_info=True)
            raise

    @staticmethod
    async def unbind_map(db: AsyncSession, map_id: int) -> int:
        """解除某场景地图下所有机器人的绑定（map_id 置 null）。
        不 commit，由调用方控制事务。返回解绑的记录数。"""
        result = await db.execute(
            update(Robot)
            .where(
                Robot.map_id == map_id,
                Robot.deleted_at.is_(None),
            )
            .values(map_id=None)
        )
        await db.flush()
        return result.rowcount or 0

    @staticmethod
    async def update_grpc_config(
        db: AsyncSession, robot_id: int, grpc_config: RobotGrpcConfigPayload
    ) -> Robot:
        """
        更新机器人 gRPC 配置（agent / middleware / ros）

        与主表单 edit 权限解耦，单独由 robot:manage:grpc_config 控制。

        Args:
            db: 数据库会话
            robot_id: 机器人ID
            grpc_config: gRPC 配置载体

        Returns:
            更新后的机器人对象

        Raises:
            NotFoundError: 机器人不存在
        """
        try:
            logger.info(
                "更新机器人 gRPC 配置，机器人ID: %d",
                robot_id,
            )

            result = await db.execute(
                select(Robot)
                .where(Robot.id == robot_id)
                .where(Robot.deleted_at.is_(None))
            )
            existing = result.scalar_one_or_none()

            if not existing:
                logger.warning("机器人不存在，机器人ID: %d", robot_id)
                raise NotFoundError(msg=f"机器人 {robot_id} 不存在")

            existing.grpc_config = grpc_config.model_dump(exclude_none=True)

            await db.commit()
            await db.refresh(existing)

            logger.info("更新机器人 gRPC 配置成功，机器人ID: %d", robot_id)
            return existing

        except NotFoundError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error("更新机器人 gRPC 配置失败: %s", str(e), exc_info=True)
            raise

    @staticmethod
    async def update_map_binding(
        db: AsyncSession, robot_id: int, payload: RobotMapBindingUpdate
    ) -> Robot:
        """
        更新机器人绑定场景（地图编辑器专用）

        与主表单 edit 解耦：只改 map_id 一个字段，不接受其他字段。
        map_id=None 表示解绑。新增 / 切换绑定时校验 SceneMap 存在性，并在绑定成功后
        通过 SwitchMap 通知导览服务切换机器人当前地图（与广播地图 NotifyMapSaved 共用
        同一 MapService gRPC 地址，失败仅记日志、不影响绑定结果）。

        Args:
            db: 数据库会话
            robot_id: 机器人ID
            payload: 仅含 map_id

        Returns:
            更新后的机器人对象

        Raises:
            NotFoundError: 机器人不存在 / 场景地图不存在
        """
        try:
            logger.info(
                "更新机器人绑定场景，机器人ID: %d，map_id: %s",
                robot_id,
                payload.map_id,
            )

            result = await db.execute(
                select(Robot)
                .where(Robot.id == robot_id)
                .where(Robot.deleted_at.is_(None))
            )
            existing = result.scalar_one_or_none()

            if not existing:
                logger.warning("机器人不存在，机器人ID: %d", robot_id)
                raise NotFoundError(msg=f"机器人 {robot_id} 不存在")

            map_obj = None
            if payload.map_id is not None:
                map_result = await db.execute(
                    select(SceneMap)
                    .where(SceneMap.id == payload.map_id)
                    .where(SceneMap.deleted_at.is_(None))
                )
                map_obj = map_result.scalar_one_or_none()
                if not map_obj:
                    raise NotFoundError(
                        msg=f"场景地图 {payload.map_id} 不存在"
                    )

            existing.map_id = payload.map_id

            await db.commit()
            await db.refresh(existing)

            # 绑定/切换到新地图后，通知该 robot 的 middleware 切换当前地图。
            # 与「广播地图」(NotifyMapSaved) 一样走 robot.grpc_config.middleware 地址；
            # 失败/离线入重试队列，不影响绑定结果。解绑(map_id=None)不下发。
            if map_obj is not None:
                await RobotService._switch_map_via_grpc(
                    map_obj.id, map_obj.version, robot_id, db
                )

            logger.info("更新机器人绑定场景成功，机器人ID: %d", robot_id)
            return existing

        except NotFoundError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error("更新机器人绑定场景失败: %s", str(e), exc_info=True)
            raise

    @staticmethod
    async def _switch_map_via_grpc(
        map_id: int, version: int, robot_id: int, db: AsyncSession
    ) -> None:
        """切换机器人当前地图（SwitchMap），失败/离线入 grpc_retry_task 重试

        调 RPC 前先取消同 robot 的旧 SwitchMap pending（覆盖语义，旧 GRPC 不再补推）；
        离线或任一已配置 target 推送失败则入队，由定时任务在线后重试。
        下发到该 robot 的 middleware 与 agent 地址各一次，复用「广播地图」同一套按-addr
        缓存的 channel/stub。外层整体吞异常（fire-and-forget）：重试逻辑的任何异常都不抛出，
        不影响已成功的绑定结果。
        """
        if not settings.GRPC.ENABLED:
            return

        try:
            from modules.grpc.addr_provider import get_config_addr_provider
            from modules.grpc.client import MapServiceClient
            from modules.grpc.retry_service import GrpcRetryService

            # 覆盖：取消同 robot 的旧 SwitchMap pending（旧 GRPC 不再补推）
            await GrpcRetryService.cancel_superseded(
                db,
                service_name="map",
                method_name="SwitchMap",
                robot_id=robot_id,
            )

            payload = {"robot_id": robot_id, "map_id": map_id, "version": version}

            # 离线：直接入队，等上线后定时重试
            if not await GrpcRetryService.is_robot_online(db, robot_id):
                await GrpcRetryService.save_pending(
                    db,
                    service_name="map",
                    method_name="SwitchMap",
                    payload=payload,
                    robot_id=robot_id,
                    last_error="机器人离线，等待上线后重试",
                )
                return

            # 在线：对 middleware / agent 各下发一次；任一已配置 target 失败则入队
            failed: List[str] = []
            for target in ("middleware", "agent"):
                addr = await get_config_addr_provider().get_addr(robot_id, target)
                if not addr:
                    logger.info(
                        "switch_map skipped: %s 未配置 robot_id=%s map=%s",
                        target,
                        robot_id,
                        map_id,
                    )
                    continue
                try:
                    resp = await MapServiceClient.switch_map(map_id, version, addr)
                    status = getattr(resp, "status", "")
                    if status == "OK":
                        logger.info(
                            "switch_map ok target=%s map=%s version=%s robot_id=%s addr=%s msg=%s current_id=%s current_version=%s",
                            target,
                            map_id,
                            version,
                            robot_id,
                            addr,
                            resp.message,
                            getattr(resp, "current_id", ""),
                            getattr(resp, "current_version", ""),
                        )
                    else:
                        failed.append(
                            f"{target}: {getattr(resp, 'message', '') or '设备未响应'}"
                        )
                except Exception as exc:  # noqa: BLE001 - 单端失败不影响另一端，最终统一入队
                    logger.warning(
                        "switch_map failed target=%s map=%s version=%s robot_id=%s addr=%s: %s",
                        target,
                        map_id,
                        version,
                        robot_id,
                        addr,
                        exc,
                    )
                    failed.append(f"{target}: {exc}")

            if failed:
                await GrpcRetryService.save_pending(
                    db,
                    service_name="map",
                    method_name="SwitchMap",
                    payload=payload,
                    robot_id=robot_id,
                    last_error="; ".join(failed),
                )
        except Exception as exc:  # noqa: BLE001 - fire-and-forget：不破坏已成功的绑定
            logger.warning(
                "switch_map overall failed (fire-and-forget) map=%s version=%s robot_id=%s: %s",
                map_id,
                version,
                robot_id,
                exc,
            )
