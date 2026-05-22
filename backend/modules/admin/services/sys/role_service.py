#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
角色管理服务
处理角色相关的业务逻辑
"""
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, Select
from sqlalchemy.orm import joinedload
from typing import List, Optional, Tuple

from app.models.sys.role import SysRole
from app.models.sys.menu import SysMenu
from core.exception.errors import NotFoundError, ConflictError, ForbiddenError
from modules.admin.schemas.sys.role import (
    SysRoleCreate,
    SysRoleUpdate,
    SysRoleQueryParams,
)

logger = logging.getLogger(__name__)


class RoleService:
    """
    角色管理服务类
    """

    @staticmethod
    def build_role_query(
        query_params: SysRoleQueryParams,
    ) -> Select:
        """
        构建角色查询对象

        Args:
            query_params: 查询参数

        Returns:
            SQLAlchemy查询对象
        """
        # 构建基础查询
        base_query = select(SysRole)

        # 添加查询条件
        conditions = []
        if query_params.status is not None:
            conditions.append(SysRole.status == query_params.status)
        if query_params.name:
            conditions.append(SysRole.name.like(f"%{query_params.name}%"))
        if query_params.code:
            conditions.append(SysRole.code.like(f"%{query_params.code}%"))
        if query_params.is_system is not None:
            conditions.append(SysRole.is_system == query_params.is_system)

        if conditions:
            base_query = base_query.where(and_(*conditions))

        # 添加排序
        base_query = base_query.order_by(SysRole.sort.asc(), SysRole.created_at.desc())

        return base_query

    @staticmethod
    async def get_role_list(
        db: AsyncSession,
        query_params: SysRoleQueryParams,
    ) -> Tuple[List[SysRole], int]:
        """
        获取角色列表（带分页和查询条件）

        Args:
            db: 数据库会话
            query_params: 查询参数

        Returns:
            Tuple[角色列表, 总记录数]
        """
        logger.info(f"获取角色列表，查询参数: {query_params}")

        # 构建查询
        base_query = RoleService.build_role_query(query_params)

        # 统计总数
        count_query = select(func.count()).select_from(base_query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # 分页
        offset = (query_params.page - 1) * query_params.page_size
        paginated_query = base_query.offset(offset).limit(query_params.page_size)

        # 执行查询
        result = await db.execute(paginated_query)
        roles = result.unique().scalars().all()

        logger.info(f"获取角色列表成功，共 {total} 条记录")
        return roles, total

    @staticmethod
    async def get_role(db: AsyncSession, role_id: int) -> SysRole:
        """
        获取单个角色（包含关联菜单）

        Args:
            db: 数据库会话
            role_id: 角色ID

        Returns:
            角色对象

        Raises:
            NotFoundError: 角色不存在
        """
        logger.info(f"获取角色信息，角色ID: {role_id}")

        result = await db.execute(
            select(SysRole)
            .options(joinedload(SysRole.menus))
            .where(SysRole.id == role_id)
        )
        role = result.unique().scalar_one_or_none()

        if not role:
            logger.warning(f"角色不存在，角色ID: {role_id}")
            raise NotFoundError(msg=f"角色 {role_id} 不存在")

        logger.info(f"获取角色信息成功，角色名: {role.name}")
        return role

    @staticmethod
    async def get_role_by_code(db: AsyncSession, code: str) -> Optional[SysRole]:
        """
        根据角色编码获取角色

        Args:
            db: 数据库会话
            code: 角色编码

        Returns:
            角色对象或None
        """
        result = await db.execute(select(SysRole).where(SysRole.code == code))
        return result.scalar_one_or_none()

    @staticmethod
    async def create_role(
        db: AsyncSession, role_create: SysRoleCreate, *, is_superuser: bool = False
    ) -> SysRole:
        """
        创建角色

        Args:
            db: 数据库会话
            role_create: 角色创建请求模型

        Returns:
            创建后的角色对象

        Raises:
            ConflictError: 角色编码已存在
        """
        logger.info(f"创建角色，角色名: {role_create.name}, 编码: {role_create.code}")

        # 检查角色编码是否已存在
        if await RoleService.get_role_by_code(db, role_create.code):
            logger.warning(f"创建角色失败，角色编码已存在: {role_create.code}")
            raise ConflictError(msg="角色编码已存在")

        # 创建角色对象
        role = SysRole(
            name=role_create.name,
            code=role_create.code,
            desc=role_create.desc,
            status=role_create.status,
            sort=role_create.sort,
            is_system=False if not is_superuser else getattr(role_create, 'is_system', False),
            is_default=False,
        )

        # 分配菜单
        if role_create.menu_ids:
            result = await db.execute(
                select(SysMenu).where(SysMenu.id.in_(role_create.menu_ids))
            )
            menus = result.scalars().all()
            role.menus = menus

        db.add(role)
        await db.commit()
        await db.refresh(role)

        # 重新查询角色，预加载菜单关系，避免异步加载问题
        result = await db.execute(
            select(SysRole)
            .options(joinedload(SysRole.menus))
            .where(SysRole.id == role.id)
        )
        role_with_menus = result.unique().scalar_one()

        logger.info(f"创建角色成功，角色ID: {role.id}")
        return role_with_menus

    @staticmethod
    async def update_role(
        db: AsyncSession,
        role_id: int,
        role_update: SysRoleUpdate,
        *,
        is_superuser: bool = False,
    ) -> SysRole:
        """
        更新角色

        Args:
            db: 数据库会话
            role_id: 角色ID
            role_update: 角色更新请求模型

        Returns:
            更新后的角色对象

        Raises:
            NotFoundError: 角色不存在
            ForbiddenError: 不能修改系统内置角色
        """
        logger.info(f"更新角色信息，角色ID: {role_id}")

        # 获取角色
        role = await RoleService.get_role(db, role_id)

        # 检查是否为系统内置角色
        if role.is_system and not is_superuser:
            logger.warning(f"更新角色失败，不能修改系统内置角色，角色ID: {role_id}")
            raise ForbiddenError(msg="不能修改系统内置角色")

        # 检查角色编码是否已存在（如果要更新编码的话）
        if role_update.code and role_update.code != role.code:
            existing_role = await RoleService.get_role_by_code(db, role_update.code)
            if existing_role:
                logger.warning(f"更新角色失败，角色编码已存在: {role_update.code}")
                raise ConflictError(msg="角色编码已存在")

        # 更新角色信息
        update_data = role_update.model_dump(exclude_unset=True)

        # 处理菜单分配
        if "menu_ids" in update_data:
            menu_ids = update_data.pop("menu_ids")
            if menu_ids:
                result = await db.execute(
                    select(SysMenu).where(SysMenu.id.in_(menu_ids))
                )
                menus = result.scalars().all()
                role.menus = menus
            else:
                role.menus = []

        # 更新其他字段
        for key, value in update_data.items():
            if hasattr(role, key) and value is not None:
                setattr(role, key, value)

        await db.commit()
        await db.refresh(role)

        logger.info(f"更新角色信息成功，角色ID: {role_id}")
        return role

    @staticmethod
    async def assign_menu_to_role(
        db: AsyncSession,
        role_id: int,
        menu_ids: List[int],
        *,
        is_superuser: bool = False,
    ) -> SysRole:
        """
        为角色分配菜单权限

        Args:
            db: 数据库会话
            role_id: 角色ID
            menu_ids: 菜单ID列表

        Returns:
            更新后的角色对象

        Raises:
            NotFoundError: 角色不存在
            ForbiddenError: 不能修改系统内置角色
        """
        logger.info(f"为角色分配菜单权限，角色ID: {role_id}, 菜单ID列表: {menu_ids}")

        # 获取角色
        role = await RoleService.get_role(db, role_id)

        # 检查是否为系统内置角色
        if role.is_system and not is_superuser:
            logger.warning(f"分配菜单失败，不能修改系统内置角色，角色ID: {role_id}")
            raise ForbiddenError(msg="不能修改系统内置角色")

        # 获取菜单
        if menu_ids:
            result = await db.execute(select(SysMenu).where(SysMenu.id.in_(menu_ids)))
            menus = result.scalars().all()
            role.menus = menus
        else:
            role.menus = []

        await db.commit()
        await db.refresh(role)

        logger.info(f"为角色分配菜单权限成功，角色ID: {role_id}")
        return role

    @staticmethod
    async def delete_role(
        db: AsyncSession, role_id: int, *, is_superuser: bool = False
    ) -> bool:
        """
        删除角色

        Args:
            db: 数据库会话
            role_id: 角色ID

        Returns:
            是否删除成功

        Raises:
            NotFoundError: 角色不存在
            ForbiddenError: 不能删除系统内置角色或默认角色
        """
        logger.info(f"删除角色，角色ID: {role_id}")

        # 获取角色
        role = await RoleService.get_role(db, role_id)

        # 检查是否为系统内置角色或默认角色
        if role.is_system and not is_superuser:
            logger.warning(f"删除角色失败，不能删除系统内置角色，角色ID: {role_id}")
            raise ForbiddenError(msg="不能删除系统内置角色")

        if role.is_default:
            logger.warning(f"删除角色失败，不能删除默认角色，角色ID: {role_id}")
            raise ForbiddenError(msg="不能删除默认角色")

        await db.delete(role)
        await db.commit()

        logger.info(f"删除角色成功，角色ID: {role_id}")
        return True

    @staticmethod
    async def batch_delete_roles(
        db: AsyncSession, role_ids: List[int], *, is_superuser: bool = False
    ) -> int:
        """
        批量删除角色

        Args:
            db: 数据库会话
            role_ids: 角色ID列表

        Returns:
            删除的角色数量
        """
        logger.info(f"批量删除角色，角色ID列表: {role_ids}")

        delete_count = 0
        for role_id in role_ids:
            try:
                await RoleService.delete_role(db, role_id, is_superuser=is_superuser)
                delete_count += 1
            except Exception as e:
                logger.error(f"删除角色失败，角色ID: {role_id}, 错误: {str(e)}")
                raise e

        logger.info(f"批量删除角色成功，共删除 {delete_count} 个角色")
        return delete_count

    @staticmethod
    async def batch_update_roles_status(
        db: AsyncSession,
        role_ids: List[int],
        status: bool,
        *,
        is_superuser: bool = False,
    ) -> int:
        """
        批量更新角色状态

        Args:
            db: 数据库会话
            role_ids: 角色ID列表
            status: 要设置的状态（True-启用，False-禁用）

        Returns:
            更新的角色数量
        """
        logger.info(f"批量更新角色状态，角色ID列表: {role_ids}, 状态: {status}")

        # 获取角色
        result = await db.execute(
            select(SysRole).where(SysRole.id.in_(role_ids))
        )
        roles = result.scalars().all()

        # 更新状态
        update_count = 0
        for role in roles:
            if not role.is_system or is_superuser:
                role.status = status
                update_count += 1
            else:
                logger.warning(f"不能修改系统内置角色状态，角色ID: {role.id}")

        await db.commit()

        logger.info(f"批量更新角色状态成功，共 {update_count} 个角色被更新")
        return update_count

    @staticmethod
    async def get_all_roles(db: AsyncSession) -> List[SysRole]:
        """
        获取所有启用的角色

        Args:
            db: 数据库会话

        Returns:
            启用的角色列表
        """
        logger.info("获取所有启用的角色")

        query = (
            select(SysRole)
            .options(joinedload(SysRole.menus))
            .where(SysRole.status == True)
        )
        result = await db.execute(query)
        roles = result.unique().scalars().all()

        logger.info(f"获取所有启用的角色成功，共 {len(roles)} 个角色")
        return roles
