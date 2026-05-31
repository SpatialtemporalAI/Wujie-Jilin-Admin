#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, Select
from typing import List, Optional

from plugins.multi_tenant.models.tenant import Tenant, sys_user_tenant_association
from app.models.sys.user import SysUser
from core.exception.errors import NotFoundError, ConflictError, ForbiddenError
from plugins.multi_tenant.schemas.tenant import (
    TenantCreate,
    TenantUpdate,
    TenantQueryParams,
)

logger = logging.getLogger(__name__)


class TenantService:
    """租户管理服务"""

    @staticmethod
    def build_tenant_query(query_params: TenantQueryParams) -> Select:
        """构建租户查询"""
        base_query = select(Tenant)
        conditions = []
        if query_params.status is not None:
            conditions.append(Tenant.status == query_params.status)
        if query_params.name:
            conditions.append(Tenant.name.like(f"%{query_params.name}%"))
        if query_params.code:
            conditions.append(Tenant.code.like(f"%{query_params.code}%"))
        if conditions:
            base_query = base_query.where(and_(*conditions))
        base_query = base_query.order_by(Tenant.created_at.desc())
        return base_query

    @staticmethod
    async def get_tenant(db: AsyncSession, tenant_id: int) -> Tenant:
        """获取单个租户"""
        result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise NotFoundError(msg=f"租户 {tenant_id} 不存在")
        return tenant

    @staticmethod
    async def get_tenant_by_code(db: AsyncSession, code: str) -> Optional[Tenant]:
        """根据编码获取租户"""
        result = await db.execute(select(Tenant).where(Tenant.code == code))
        return result.scalar_one_or_none()

    @staticmethod
    async def create_tenant(db: AsyncSession, tenant_create: TenantCreate) -> Tenant:
        """创建租户"""
        if await TenantService.get_tenant_by_code(db, tenant_create.code):
            raise ConflictError(msg="租户编码已存在")

        # 检查名称唯一
        result = await db.execute(select(Tenant).where(Tenant.name == tenant_create.name))
        if result.scalar_one_or_none():
            raise ConflictError(msg="租户名称已存在")

        tenant = Tenant(
            name=tenant_create.name,
            code=tenant_create.code,
            description=tenant_create.description,
            contact_name=tenant_create.contact_name,
            contact_email=tenant_create.contact_email,
            contact_phone=tenant_create.contact_phone,
            max_users=tenant_create.max_users,
        )
        db.add(tenant)
        await db.commit()
        await db.refresh(tenant)
        logger.info("创建租户成功，ID: %s, 编码: %s", tenant.id, tenant.code)
        return tenant

    @staticmethod
    async def update_tenant(
        db: AsyncSession, tenant_id: int, tenant_update: TenantUpdate
    ) -> Tenant:
        """更新租户"""
        tenant = await TenantService.get_tenant(db, tenant_id)
        update_data = tenant_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(tenant, key) and value is not None:
                setattr(tenant, key, value)
        await db.commit()
        await db.refresh(tenant)
        logger.info("更新租户成功，ID: %s", tenant_id)
        return tenant

    @staticmethod
    async def delete_tenant(db: AsyncSession, tenant_id: int) -> bool:
        """删除租户"""
        tenant = await TenantService.get_tenant(db, tenant_id)
        await db.delete(tenant)
        await db.commit()
        logger.info("删除租户成功，ID: %s", tenant_id)
        return True

    @staticmethod
    async def update_status(db: AsyncSession, tenant_id: int, status: bool) -> Tenant:
        """更新租户状态"""
        tenant = await TenantService.get_tenant(db, tenant_id)
        tenant.status = status
        await db.commit()
        await db.refresh(tenant)
        return tenant

    @staticmethod
    async def get_user_tenants(
        db: AsyncSession, user_id: int
    ) -> List[Tenant]:
        """获取用户所属的所有租户"""
        result = await db.execute(
            select(Tenant)
            .join(sys_user_tenant_association, Tenant.id == sys_user_tenant_association.c.tenant_id)
            .where(sys_user_tenant_association.c.user_id == user_id)
            .where(Tenant.status == True)
        )
        return list(result.scalars().all())

    @staticmethod
    async def assign_user(
        db: AsyncSession, tenant_id: int, user_id: int, role: str = "member"
    ) -> bool:
        """分配用户到租户"""
        tenant = await TenantService.get_tenant(db, tenant_id)

        # 检查用户是否存在
        result = await db.execute(select(SysUser).where(SysUser.id == user_id))
        if not result.scalar_one_or_none():
            raise NotFoundError(msg=f"用户 {user_id} 不存在")

        # 检查是否已分配
        result = await db.execute(
            select(sys_user_tenant_association).where(
                and_(
                    sys_user_tenant_association.c.user_id == user_id,
                    sys_user_tenant_association.c.tenant_id == tenant_id,
                )
            )
        )
        if result.first():
            raise ConflictError(msg="用户已在该租户中")

        # 检查用户数限制
        count_result = await db.execute(
            select(sys_user_tenant_association).where(
                sys_user_tenant_association.c.tenant_id == tenant_id
            )
        )
        current_count = len(count_result.all())
        if current_count >= tenant.max_users:
            raise ForbiddenError(msg=f"租户用户数已达上限 ({tenant.max_users})")

        await db.execute(
            sys_user_tenant_association.insert().values(
                user_id=user_id, tenant_id=tenant_id, role=role
            )
        )
        await db.commit()
        logger.info("分配用户 %s 到租户 %s，角色: %s", user_id, tenant_id, role)
        return True

    @staticmethod
    async def remove_user(
        db: AsyncSession, tenant_id: int, user_id: int
    ) -> bool:
        """从租户中移除用户"""
        await TenantService.get_tenant(db, tenant_id)

        # 检查是否是 owner
        result = await db.execute(
            select(sys_user_tenant_association).where(
                and_(
                    sys_user_tenant_association.c.user_id == user_id,
                    sys_user_tenant_association.c.tenant_id == tenant_id,
                )
            )
        )
        row = result.first()
        if not row:
            raise NotFoundError(msg="用户不在该租户中")
        if row.role == "owner":
            # 检查是否还有其他 owner
            count_result = await db.execute(
                select(sys_user_tenant_association).where(
                    and_(
                        sys_user_tenant_association.c.tenant_id == tenant_id,
                        sys_user_tenant_association.c.role == "owner",
                    )
                )
            )
            owners = count_result.all()
            if len(owners) <= 1:
                raise ForbiddenError(msg="不能移除最后一个 owner")

        await db.execute(
            sys_user_tenant_association.delete().where(
                and_(
                    sys_user_tenant_association.c.user_id == user_id,
                    sys_user_tenant_association.c.tenant_id == tenant_id,
                )
            )
        )
        await db.commit()
        logger.info("从租户 %s 移除用户 %s", tenant_id, user_id)
        return True

    @staticmethod
    async def get_tenant_users(
        db: AsyncSession, tenant_id: int
    ) -> List[dict]:
        """获取租户中的用户列表"""
        await TenantService.get_tenant(db, tenant_id)
        result = await db.execute(
            select(SysUser, sys_user_tenant_association.c.role.label("tenant_role"))
            .join(
                sys_user_tenant_association,
                SysUser.id == sys_user_tenant_association.c.user_id,
            )
            .where(sys_user_tenant_association.c.tenant_id == tenant_id)
        )
        rows = result.all()
        users = []
        for row in rows:
            user_dict = {
                "id": row.SysUser.id,
                "username": row.SysUser.username,
                "nickname": row.SysUser.nickname,
                "email": row.SysUser.email,
                "phone": row.SysUser.phone,
                "status": row.SysUser.status,
                "tenant_role": row.tenant_role,
            }
            users.append(user_dict)
        return users
