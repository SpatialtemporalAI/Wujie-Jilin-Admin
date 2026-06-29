#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
商户管理服务
处理商户 CRUD、机器人绑定、api_key/secret 生成与重置
"""
import logging
from typing import List, Optional, Tuple

from sqlalchemy import select, and_, func, Select, delete, insert
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.business.merchant import Merchant
from database.models.business.merchant_robot import merchant_robot_association
from database.models.business.robot import Robot
from core.exception.errors import NotFoundError, ConflictError
from modules.merchant.schemas.merchant import (
    MerchantCreate,
    MerchantUpdate,
    MerchantQueryParams,
)
from modules.merchant.services.api_key_service import ApiKeyService

logger = logging.getLogger(__name__)


class MerchantService:
    """商户管理服务类"""

    @staticmethod
    def build_list_query(query_params: MerchantQueryParams) -> Select:
        """构建商户列表查询"""
        base_query = select(Merchant).where(Merchant.deleted_at.is_(None))
        conditions = []
        if query_params.name:
            conditions.append(Merchant.name.like(f"%{query_params.name}%"))
        if query_params.code:
            conditions.append(Merchant.code.like(f"%{query_params.code}%"))
        if query_params.status is not None:
            conditions.append(Merchant.status == query_params.status)
        if conditions:
            base_query = base_query.where(and_(*conditions))
        return base_query.order_by(Merchant.created_at.desc())

    @staticmethod
    async def get(db: AsyncSession, merchant_id: int) -> Merchant:
        result = await db.execute(
            select(Merchant)
            .where(Merchant.id == merchant_id)
            .where(Merchant.deleted_at.is_(None))
        )
        merchant = result.scalar_one_or_none()
        if not merchant:
            raise NotFoundError(msg=f"商户 {merchant_id} 不存在")
        return merchant

    @staticmethod
    async def get_by_api_key(db: AsyncSession, api_key: str) -> Optional[Merchant]:
        """按 api_key 查询商户（含已禁用，由调用方判断状态）"""
        result = await db.execute(
            select(Merchant)
            .where(Merchant.api_key == api_key)
            .where(Merchant.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_robot_ids(db: AsyncSession, merchant_id: int) -> List[int]:
        """获取商户绑定的机器人ID列表"""
        result = await db.execute(
            select(merchant_robot_association.c.robot_id).where(
                merchant_robot_association.c.merchant_id == merchant_id
            )
        )
        return [row[0] for row in result.all()]

    @staticmethod
    async def _replace_robots(
        db: AsyncSession, merchant_id: int, robot_ids: List[int]
    ) -> None:
        """全量替换商户绑定的机器人"""
        await db.execute(
            delete(merchant_robot_association).where(
                merchant_robot_association.c.merchant_id == merchant_id
            )
        )
        # 校验机器人存在
        if robot_ids:
            robot_result = await db.execute(
                select(Robot.id)
                .where(Robot.id.in_(robot_ids), Robot.deleted_at.is_(None))
            )
            valid_ids = [row[0] for row in robot_result.all()]
            if len(valid_ids) != len(set(robot_ids)):
                raise NotFoundError(msg="部分机器人不存在")
            for robot_id in valid_ids:
                await db.execute(
                    insert(merchant_robot_association).values(
                        merchant_id=merchant_id, robot_id=robot_id
                    )
                )

    @staticmethod
    async def _unique_api_key(db: AsyncSession) -> str:
        """生成不重复的 api_key（碰撞概率极低，兜底重试）"""
        for _ in range(5):
            api_key = ApiKeyService.generate_api_key()
            exists = await db.execute(
                select(Merchant.id)
                .where(Merchant.api_key == api_key)
                .where(Merchant.deleted_at.is_(None))
            )
            if exists.scalar_one_or_none() is None:
                return api_key
        raise ConflictError(msg="api_key 生成失败，请重试")

    @staticmethod
    async def create(
        db: AsyncSession, merchant_in: MerchantCreate
    ) -> Tuple[Merchant, str]:
        """创建商户，返回 (商户对象, api_secret 明文)"""
        logger.info("创建商户，编码: %s", merchant_in.code)

        # code 唯一性
        exists = await db.execute(
            select(Merchant.id)
            .where(Merchant.code == merchant_in.code)
            .where(Merchant.deleted_at.is_(None))
        )
        if exists.scalar_one_or_none() is not None:
            raise ConflictError(msg="商户编码已存在")

        api_key = await MerchantService._unique_api_key(db)
        plaintext_secret = ApiKeyService.generate_api_secret()

        merchant = Merchant(
            name=merchant_in.name,
            code=merchant_in.code,
            api_key=api_key,
            api_secret_encrypted=ApiKeyService.encrypt_secret(plaintext_secret),
            contact_name=merchant_in.contact_name,
            contact_phone=merchant_in.contact_phone,
            contact_email=merchant_in.contact_email,
            status=merchant_in.status,
            remark=merchant_in.remark,
        )
        db.add(merchant)
        await db.flush()

        if merchant_in.robot_ids:
            await MerchantService._replace_robots(db, merchant.id, merchant_in.robot_ids)

        await db.commit()
        await db.refresh(merchant)

        logger.info("创建商户成功，商户ID: %s", merchant.id)
        return merchant, plaintext_secret

    @staticmethod
    async def update(
        db: AsyncSession, merchant_id: int, merchant_in: MerchantUpdate
    ) -> Merchant:
        logger.info("更新商户，商户ID: %s", merchant_id)
        merchant = await MerchantService.get(db, merchant_id)

        update_data = merchant_in.model_dump(exclude_unset=True)

        # code 唯一性
        if update_data.get("code") and update_data["code"] != merchant.code:
            exists = await db.execute(
                select(Merchant.id)
                .where(
                    Merchant.code == update_data["code"],
                    Merchant.id != merchant_id,
                    Merchant.deleted_at.is_(None),
                )
            )
            if exists.scalar_one_or_none() is not None:
                raise ConflictError(msg="商户编码已被其他商户使用")

        robot_ids = update_data.pop("robot_ids", None)

        for key, value in update_data.items():
            if hasattr(merchant, key) and value is not None:
                setattr(merchant, key, value)

        if robot_ids is not None:
            await MerchantService._replace_robots(db, merchant.id, robot_ids)

        await db.commit()
        await db.refresh(merchant)

        logger.info("更新商户成功，商户ID: %s", merchant_id)
        return merchant

    @staticmethod
    async def delete(db: AsyncSession, merchant_id: int) -> bool:
        logger.info("删除商户，商户ID: %s", merchant_id)
        merchant = await MerchantService.get(db, merchant_id)
        merchant.soft_delete()
        await db.commit()
        logger.info("删除商户成功，商户ID: %s", merchant_id)
        return True

    @staticmethod
    async def reset_api_key(
        db: AsyncSession, merchant_id: int
    ) -> Tuple[Merchant, str]:
        """重置 api_key + api_secret，返回 (商户对象, api_secret 明文)"""
        logger.info("重置商户 API 密钥，商户ID: %s", merchant_id)
        merchant = await MerchantService.get(db, merchant_id)

        merchant.api_key = await MerchantService._unique_api_key(db)
        plaintext_secret = ApiKeyService.generate_api_secret()
        merchant.api_secret_encrypted = ApiKeyService.encrypt_secret(plaintext_secret)

        await db.commit()
        await db.refresh(merchant)

        logger.info("重置商户 API 密钥成功，商户ID: %s", merchant_id)
        return merchant, plaintext_secret
