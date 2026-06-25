#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
路由管理服务
根据用户角色构建动态路由
"""
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload, noload
from typing import List, Optional

from database.models.sys.user import SysUser
from database.models.sys.menu import SysMenu, MenuType
from database.models.sys.role import SysRole
from modules.admin.schemas.sys.route import (
    MenuRouteResponse,
    RouteMetaResponse,
    UserRouteResponse,
)

logger = logging.getLogger(__name__)


class RouteService:
    """路由管理服务类"""

    @staticmethod
    def _menu_to_route(
        menu: SysMenu,
        children_map: Optional[dict] = None,
    ) -> MenuRouteResponse:
        """将 SysMenu 模型转换为 MenuRouteResponse

        Args:
            menu: 菜单对象
            children_map: 可选的 {parent_id: [children]} 映射。普通用户场景下
                传入此参数以使用经 menu_ids 过滤后的内存树，避免依赖 ORM 自动
                加载（ORM 会把所有兄弟子菜单带出来导致权限越界）。
        """
        route_name = menu.name

        meta = RouteMetaResponse(
            title=menu.name,
            i18nKey=f"route.{menu.name}",
            icon=menu.meta_icon,
            order=menu.sort if menu.sort else None,
            hideInMenu=menu.meta_hidden if menu.meta_hidden else None,
            keepAlive=menu.meta_keep_alive if menu.meta_keep_alive else None,
            href=menu.meta_href if menu.meta_href else None,
        )

        children = None
        if children_map is not None:
            raw_children = children_map.get(menu.id, [])
        else:
            raw_children = menu.children

        if raw_children:
            child_routes = [
                RouteService._menu_to_route(child, children_map)
                for child in raw_children
                if child.type != MenuType.BUTTON
                and child.status
                and child.deleted_at is None
            ]
            if child_routes:
                children = child_routes

        # Flatten: if a catalog has a single child with the same route name and no
        # component on the catalog itself, merge them into one route to avoid
        # Vue Router "same name as ancestor" conflicts.
        if children and len(children) == 1 and not menu.component:
            only_child = children[0]
            if only_child.name == route_name:
                return MenuRouteResponse(
                    id=only_child.id,
                    name=only_child.name,
                    path=menu.path or only_child.path,
                    component=only_child.component,
                    redirect=only_child.redirect or menu.redirect,
                    meta=only_child.meta,
                    children=only_child.children,
                )

        return MenuRouteResponse(
            id=str(menu.id),
            name=route_name,
            path=menu.path or "",
            component=None if menu.meta_href else menu.component,
            redirect=menu.redirect,
            meta=meta,
            children=children,
        )

    @staticmethod
    def _find_first_leaf_route_name(
        routes: List[MenuRouteResponse],
    ) -> Optional[str]:
        """按菜单顺序递归查找第一个可访问的叶子路由名（组件含 `view.` 的页面）。

        用于动态决定登录后的默认访问页，避免始终硬编码为 "home"。
        """
        for route in routes:
            if route.component and "view." in route.component:
                return route.name
            if route.children:
                child = RouteService._find_first_leaf_route_name(route.children)
                if child:
                    return child
        return None

    @staticmethod
    async def get_user_routes(
        db: AsyncSession, user: SysUser
    ) -> UserRouteResponse:
        """
        获取当前用户可用的路由树以及按钮权限标识列表
        - 超级用户返回所有非 BUTTON 类型的启用菜单 + 所有 BUTTON 权限
        - 普通用户通过 user.roles → role.menus 获取
        """
        buttons: list[str] = []
        if user.is_superuser:
            stmt = (
                select(SysMenu)
                .where(
                    SysMenu.type != MenuType.BUTTON,
                    SysMenu.status == True,
                    SysMenu.parent_id.is_(None),
                )
                .options(
                    selectinload(SysMenu.children).selectinload(SysMenu.children),
                    noload(SysMenu.roles),
                    noload(SysMenu.parent),
                )
                .order_by(SysMenu.sort, SysMenu.id)
            )
            result = await db.execute(stmt)
            menus = result.unique().scalars().all()

            btn_stmt = select(SysMenu).options(
                noload(SysMenu.children),
                noload(SysMenu.parent),
                noload(SysMenu.roles),
            ).where(
                SysMenu.type == MenuType.BUTTON,
                SysMenu.status == True,
            )
            btn_result = await db.execute(btn_stmt)
            buttons = [
                m.permission for m in btn_result.scalars().all() if m.permission
            ]
            routes = [RouteService._menu_to_route(menu) for menu in menus]
            home = RouteService._find_first_leaf_route_name(routes) or "home"
            return UserRouteResponse(routes=routes, home=home, buttons=buttons)
        else:
            # 预加载 user.roles.menus
            stmt = (
                select(SysUser)
                .options(
                    joinedload(SysUser.roles).options(
                        joinedload(SysRole.menus)
                    )
                )
                .where(SysUser.id == user.id)
            )
            result = await db.execute(stmt)
            user_with_relations = result.unique().scalar_one()

            # 收集所有启用的非 BUTTON 菜单 ID 以及 BUTTON 权限标识
            # 注意：分配了按钮 → 其父菜单必须可见（否则按钮无页面承载）
            # 所以 BUTTON 的 parent_id 也加入 menu_ids,后续祖先补全会把
            # 完整路径（如 log 目录 → log_login-log）一并加入
            menu_ids: set[int] = set()
            seen_perms: set[str] = set()
            for role in user_with_relations.roles:
                if not role.status:
                    continue
                for menu in role.menus:
                    if not menu.status:
                        continue
                    if menu.type == MenuType.BUTTON:
                        if menu.permission and menu.permission not in seen_perms:
                            seen_perms.add(menu.permission)
                            buttons.append(menu.permission)
                        if menu.parent_id:
                            menu_ids.add(menu.parent_id)
                        continue
                    menu_ids.add(menu.id)

            # 一次性加载 id->parent_id 映射，在内存中解析祖先
            if menu_ids:
                parent_result = await db.execute(
                    select(SysMenu.id, SysMenu.parent_id)
                )
                parent_map = dict(parent_result.all())
                queue = list(menu_ids)
                while queue:
                    current = queue.pop()
                    pid = parent_map.get(current)
                    if pid and pid not in menu_ids:
                        menu_ids.add(pid)
                        queue.append(pid)

            if not menu_ids:
                return UserRouteResponse(routes=[], home="home", buttons=buttons)

            # Flat 查询所有相关菜单（按 menu_ids 过滤），不依赖 ORM 关系加载
            stmt = (
                select(SysMenu)
                .where(
                    SysMenu.id.in_(menu_ids),
                    SysMenu.status == True,
                )
                .options(
                    noload(SysMenu.children),
                    noload(SysMenu.parent),
                    noload(SysMenu.roles),
                )
                .order_by(SysMenu.sort, SysMenu.id)
            )
            result = await db.execute(stmt)
            all_menus = result.scalars().all()

            # 在内存中构建 parent_id -> children 映射，递归生成 route
            # 这一步天然按 menu_ids 过滤了子菜单（因为 all_menus 只含用户有权限的菜单）
            children_map: dict[int | None, list[SysMenu]] = {}
            for m in all_menus:
                children_map.setdefault(m.parent_id, []).append(m)

            menu_id_set = {m.id for m in all_menus}
            # 顶层：parent_id 为 None，或其父菜单不在结果集（理论上祖先补全已避免）
            root_menus = [
                m for m in all_menus
                if m.parent_id is None or m.parent_id not in menu_id_set
            ]

            routes = [
                RouteService._menu_to_route(m, children_map) for m in root_menus
            ]
            home = RouteService._find_first_leaf_route_name(routes) or "home"
            return UserRouteResponse(routes=routes, home=home, buttons=buttons)

    @staticmethod
    async def get_constant_routes() -> list[MenuRouteResponse]:
        """返回常量路由（登录页、错误页等），这些路由不需要权限控制"""
        routes = [
            MenuRouteResponse(
                id="login",
                name="login",
                path="/login/:module(pwd-login|code-login|register|reset-pwd|bind-wechat)?",
                component="layout.blank$view.login",
                meta=RouteMetaResponse(title="login", order=1),
            ),
            MenuRouteResponse(
                id="403",
                name="403",
                path="/403",
                component="layout.blank$view.403",
                meta=RouteMetaResponse(title="403"),
            ),
            MenuRouteResponse(
                id="404",
                name="404",
                path="/404",
                component="layout.blank$view.404",
                meta=RouteMetaResponse(title="404"),
            ),
            MenuRouteResponse(
                id="500",
                name="500",
                path="/500",
                component="layout.blank$view.500",
                meta=RouteMetaResponse(title="500"),
            ),
        ]
        return routes

    @staticmethod
    async def is_route_exist(db: AsyncSession, route_name: str) -> bool:
        """检查路由名称是否存在于菜单表中"""
        stmt = select(SysMenu.id).where(SysMenu.name == route_name)
        result = await db.execute(stmt)
        return result.scalar_one_or_none() is not None
