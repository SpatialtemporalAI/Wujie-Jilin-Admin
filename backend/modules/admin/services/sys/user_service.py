#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
用户管理服务
处理用户相关的业务逻辑
"""
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import joinedload
from typing import List, Optional, Tuple

from app.models.sys.user import SysUser
from app.models.sys.role import SysRole
from core.exception.errors import NotFoundError, ConflictError, ForbiddenError
from core.security.oauth.jwt import JWTAuthManager
from modules.admin.schemas.sys.user import (
    SysUserCreate,
    SysUserUpdate,
    SysUserPasswordUpdate,
    SysUserQueryParams,
)

logger = logging.getLogger(__name__)


class UserService:
    """
    用户管理服务类
    """

    @staticmethod
    async def get_user_list(
        db: AsyncSession,
        query_params: SysUserQueryParams,
    ) -> Tuple[List[SysUser], int]:
        """
        获取用户列表（带分页和查询条件）

        Args:
            db: 数据库会话
            query_params: 查询参数

        Returns:
            Tuple[用户列表, 总记录数]
        """
        logger.info(f"获取用户列表，查询参数: {query_params}")

        # 构建基础查询
        base_query = select(SysUser).options(joinedload(SysUser.roles))

        # 添加查询条件
        conditions = []
        if query_params.status is not None:
            conditions.append(SysUser.status == query_params.status)
        if query_params.username:
            conditions.append(SysUser.username.like(f"%{query_params.username}%"))
        if query_params.nickname:
            conditions.append(SysUser.nickname.like(f"%{query_params.nickname}%"))
        if query_params.email:
            conditions.append(SysUser.email.like(f"%{query_params.email}%"))
        if query_params.phone:
            conditions.append(SysUser.phone.like(f"%{query_params.phone}%"))
        if query_params.is_superuser is not None:
            conditions.append(SysUser.is_superuser == query_params.is_superuser)
        if query_params.role_ids:
            base_query = base_query.join(SysUser.roles).where(
                SysRole.id.in_(query_params.role_ids)
            )

        if conditions:
            base_query = base_query.where(and_(*conditions))

        # 统计总数
        count_query = select(func.count()).select_from(base_query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # 添加排序
        base_query = base_query.order_by(SysUser.created_at.desc())

        # 分页
        offset = (query_params.page - 1) * query_params.page_size
        paginated_query = base_query.offset(offset).limit(query_params.page_size)

        # 执行查询
        result = await db.execute(paginated_query)
        users = result.unique().scalars().all()

        logger.info(f"获取用户列表成功，共 {total} 条记录")
        return users, total

    @staticmethod
    async def get_user(db: AsyncSession, user_id: int) -> SysUser:
        """
        获取单个用户（包含关联角色）

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            用户对象

        Raises:
            NotFoundError: 用户不存在
        """
        logger.info(f"获取用户信息，用户ID: {user_id}")

        result = await db.execute(
            select(SysUser)
            .options(joinedload(SysUser.roles))
            .where(SysUser.id == user_id)
        )
        user = result.unique().scalar_one_or_none()

        if not user:
            logger.warning(f"用户不存在，用户ID: {user_id}")
            raise NotFoundError(msg=f"用户 {user_id} 不存在")

        logger.info(f"获取用户信息成功，用户名: {user.username}")
        return user

    @staticmethod
    async def get_user_by_username(
        db: AsyncSession, username: str
    ) -> Optional[SysUser]:
        """
        根据用户名获取用户

        Args:
            db: 数据库会话
            username: 用户名

        Returns:
            用户对象或None
        """
        result = await db.execute(select(SysUser).where(SysUser.username == username))
        return result.scalar_one_or_none()

    @staticmethod
    async def create_user(db: AsyncSession, user_create: SysUserCreate) -> SysUser:
        """
        创建用户

        Args:
            db: 数据库会话
            user_create: 用户创建请求模型

        Returns:
            创建后的用户对象

        Raises:
            ConflictError: 用户名/邮箱/手机号已存在
        """
        logger.info(f"创建用户，用户名: {user_create.username}")

        # 检查用户名是否已存在
        if await UserService.get_user_by_username(db, user_create.username):
            logger.warning(f"创建用户失败，用户名已存在: {user_create.username}")
            raise ConflictError(msg="用户名已存在")

        # 检查邮箱是否已存在
        if user_create.email and user_create.email.strip():
            result = await db.execute(
                select(SysUser).where(SysUser.email == user_create.email)
            )
            if result.scalar_one_or_none():
                logger.warning(f"创建用户失败，邮箱已存在: {user_create.email}")
                raise ConflictError(msg="邮箱已存在")

        # 检查手机号是否已存在
        if user_create.phone and user_create.phone.strip():
            result = await db.execute(
                select(SysUser).where(SysUser.phone == user_create.phone)
            )
            if result.scalar_one_or_none():
                logger.warning(f"创建用户失败，手机号已存在: {user_create.phone}")
                raise ConflictError(msg="手机号已存在")

        # 加密密码
        pwd, salt = JWTAuthManager.create_password_hash(user_create.password)

        # 创建用户对象
        user = SysUser(
            username=user_create.username,
            nickname=user_create.nickname,
            email=user_create.email,
            password=pwd,
            salt=salt,
            phone=user_create.phone,
            avatar=user_create.avatar,
            status=user_create.status,
            is_superuser=False,
        )

        # 分配角色
        if user_create.role_ids:
            result = await db.execute(
                select(SysRole).where(SysRole.id.in_(user_create.role_ids))
            )
            roles = result.scalars().all()
            user.roles = roles

        db.add(user)
        await db.commit()
        await db.refresh(user)

        logger.info(f"创建用户成功，用户ID: {user.id}")
        return user

    @staticmethod
    async def update_user(
        db: AsyncSession, user_id: int, user_update: SysUserUpdate
    ) -> SysUser:
        """
        更新用户

        Args:
            db: 数据库会话
            user_id: 用户ID
            user_update: 用户更新请求模型

        Returns:
            更新后的用户对象

        Raises:
            NotFoundError: 用户不存在
            ConflictError: 用户名/邮箱/手机号已被其他用户使用
        """
        logger.info(f"更新用户信息，用户ID: {user_id}")

        # 获取用户
        user = await UserService.get_user(db, user_id)

        # 检查用户名是否已被其他用户使用
        if (
            user_update.username
            and user_update.username.strip()
            and user_update.username != user.username
        ):
            result = await db.execute(
                select(SysUser).where(
                    SysUser.username == user_update.username, SysUser.id != user_id
                )
            )
            if result.scalar_one_or_none():
                logger.warning(
                    f"更新用户失败，用户名已被其他用户使用: {user_update.username}"
                )
                raise ConflictError(msg="用户名已被其他用户使用")

        # 检查邮箱是否已被其他用户使用
        if (
            user_update.email
            and user_update.email.strip()
            and user_update.email != user.email
        ):
            result = await db.execute(
                select(SysUser).where(
                    SysUser.email == user_update.email, SysUser.id != user_id
                )
            )
            if result.scalar_one_or_none():
                logger.warning(
                    f"更新用户失败，邮箱已被其他用户使用: {user_update.email}"
                )
                raise ConflictError(msg="邮箱已被其他用户使用")

        # 检查手机号是否已被其他用户使用
        if (
            user_update.phone
            and user_update.phone.strip()
            and user_update.phone != user.phone
        ):
            result = await db.execute(
                select(SysUser).where(
                    SysUser.phone == user_update.phone, SysUser.id != user_id
                )
            )
            if result.scalar_one_or_none():
                logger.warning(
                    f"更新用户失败，手机号已被其他用户使用: {user_update.phone}"
                )
                raise ConflictError(msg="手机号已被其他用户使用")

        # 更新用户信息
        update_data = user_update.model_dump(exclude_unset=True)

        # 处理角色分配
        if "role_ids" in update_data:
            role_ids = update_data.pop("role_ids")
            if role_ids:
                result = await db.execute(
                    select(SysRole).where(SysRole.id.in_(role_ids))
                )
                roles = result.scalars().all()
                user.roles = roles
            else:
                user.roles = []

        # 更新其他字段
        for key, value in update_data.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)

        await db.commit()
        await db.refresh(user)

        logger.info(f"更新用户信息成功，用户ID: {user_id}")
        return user

    @staticmethod
    async def assign_roles_to_user(
        db: AsyncSession, user_id: int, role_ids: List[int]
    ) -> SysUser:
        """
        为用户分配角色

        Args:
            db: 数据库会话
            user_id: 用户ID
            role_ids: 角色ID列表

        Returns:
            更新后的用户对象

        Raises:
            NotFoundError: 用户不存在
        """
        logger.info(f"为用户分配角色，用户ID: {user_id}, 角色ID列表: {role_ids}")

        # 获取用户
        user = await UserService.get_user(db, user_id)

        # 获取角色
        if role_ids:
            result = await db.execute(select(SysRole).where(SysRole.id.in_(role_ids)))
            roles = result.scalars().all()
            user.roles = roles
        else:
            user.roles = []

        await db.commit()
        await db.refresh(user)

        logger.info(f"为用户分配角色成功，用户ID: {user_id}")
        return user

    @staticmethod
    async def delete_user(db: AsyncSession, user_id: int) -> bool:
        """
        删除用户

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            是否删除成功

        Raises:
            NotFoundError: 用户不存在
            ForbiddenError: 不能删除超级管理员
        """
        logger.info(f"删除用户，用户ID: {user_id}")

        # 获取用户
        user = await UserService.get_user(db, user_id)

        # 检查是否为超级管理员
        if user.is_superuser:
            logger.warning(f"删除用户失败，不能删除超级管理员，用户ID: {user_id}")
            raise ForbiddenError(msg="不能删除超级管理员")

        await db.delete(user)
        await db.commit()

        logger.info(f"删除用户成功，用户ID: {user_id}")
        return True

    @staticmethod
    async def batch_delete_users(db: AsyncSession, user_ids: List[int]) -> int:
        """
        批量删除用户

        Args:
            db: 数据库会话
            user_ids: 用户ID列表

        Returns:
            删除的用户数量

        Raises:
            ForbiddenError: 不能删除超级管理员
        """
        logger.info(f"批量删除用户，用户ID列表: {user_ids}")

        delete_count = 0
        for user_id in user_ids:
            try:
                await UserService.delete_user(db, user_id)
                delete_count += 1
            except Exception as e:
                logger.error(f"删除用户失败，用户ID: {user_id}, 错误: {str(e)}")
                raise e

        logger.info(f"批量删除用户成功，共删除 {delete_count} 个用户")
        return delete_count

    @staticmethod
    async def update_user_password(
        db: AsyncSession,
        user_id: int,
        password_update: SysUserPasswordUpdate,
        current_user: Optional[SysUser] = None,
    ) -> bool:
        """
        修改用户密码

        Args:
            db: 数据库会话
            user_id: 用户ID
            password_update: 密码更新请求模型
            current_user: 当前操作用户（用于验证旧密码）

        Returns:
            是否修改成功

        Raises:
            NotFoundError: 用户不存在
            ForbiddenError: 密码错误或无权限修改超级管理员密码
        """
        logger.info(f"修改用户密码，用户ID: {user_id}")

        # 获取用户
        user = await UserService.get_user(db, user_id)

        # 检查是否为超级管理员（只有超级管理员自己可以修改自己的密码）
        if user.is_superuser and (not current_user or current_user.id != user_id):
            logger.warning(f"修改密码失败，无权限修改超级管理员密码，用户ID: {user_id}")
            raise ForbiddenError(msg="无权限修改超级管理员密码")

        # 如果提供了旧密码，需要验证
        if password_update.old_password:
            if not JWTAuthManager.verify_password(
                password_update.old_password, user.password, user.salt
            ):
                logger.warning(f"修改密码失败，旧密码错误，用户ID: {user_id}")
                raise ForbiddenError(msg="旧密码错误")

        # 加密新密码
        pwd, salt = JWTAuthManager.create_password_hash(password_update.new_password)
        user.password = pwd
        user.salt = salt

        await db.commit()

        logger.info(f"修改用户密码成功，用户ID: {user_id}")
        return True

    @staticmethod
    async def batch_update_users_status(
        db: AsyncSession, user_ids: List[int], status: bool
    ) -> int:
        """
        批量更新用户状态

        Args:
            db: 数据库会话
            user_ids: 用户ID列表
            status: 要设置的状态

        Returns:
            更新的用户数量
        """
        logger.info(f"批量更新用户状态，用户ID列表: {user_ids}, 状态: {status}")

        # 获取用户
        result = await db.execute(select(SysUser).where(SysUser.id.in_(user_ids)))
        users = result.scalars().all()

        # 更新状态
        update_count = 0
        for user in users:
            user.status = status
            update_count += 1

        await db.commit()

        logger.info(f"批量更新用户状态成功，共更新 {update_count} 个用户")
        return update_count
