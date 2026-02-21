#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional, List
from pydantic import Field, ConfigDict
from datetime import datetime
from app.models.common.base import BaseRespEntity, BaseEntity
from app.models.common.page import PageRequest
from app.models.sys.menu import MenuType


class SysMenuQueryParams(BaseEntity):
    """
    系统菜单查询参数模型
    用于菜单列表查询时的筛选条件
    """

    name: Optional[str] = Field(None, description="菜单名称，支持模糊查询")
    status: Optional[bool] = Field(None, description="菜单状态：True-启用，False-禁用")
    type: Optional[MenuType] = Field(None, description="菜单类型")


class SysMenuCreate(BaseEntity):
    """
    系统菜单创建请求模型
    用于创建新菜单时的请求数据
    """

    parent_id: Optional[int] = Field(None, description="父菜单ID，顶级菜单为None")
    name: str = Field(..., description="菜单名称", max_length=100)
    path: Optional[str] = Field(None, description="路由路径", max_length=255)
    component: Optional[str] = Field(None, description="组件路径", max_length=255)
    redirect: Optional[str] = Field(None, description="重定向路径", max_length=255)
    permission: Optional[str] = Field(None, description="权限标识", max_length=100)
    meta_title: Optional[str] = Field(None, description="路由标题", max_length=100)
    meta_icon: Optional[str] = Field(None, description="路由图标", max_length=50)
    meta_hidden: bool = Field(False, description="是否隐藏菜单")
    meta_affix: bool = Field(False, description="是否固定标签")
    meta_breadcrumb: bool = Field(True, description="是否显示面包屑")
    status: bool = Field(True, description="菜单状态：True-启用，False-禁用")
    type: MenuType = Field(MenuType.MENU, description="菜单类型")
    sort: int = Field(0, description="排序号")


class SysMenuUpdate(BaseEntity):
    """
    系统菜单更新请求模型
    用于更新菜单信息时的请求数据
    """

    parent_id: Optional[int] = Field(None, description="父菜单ID，顶级菜单为None")
    name: Optional[str] = Field(None, description="菜单名称", max_length=100)
    path: Optional[str] = Field(None, description="路由路径", max_length=255)
    component: Optional[str] = Field(None, description="组件路径", max_length=255)
    redirect: Optional[str] = Field(None, description="重定向路径", max_length=255)
    permission: Optional[str] = Field(None, description="权限标识", max_length=100)
    meta_title: Optional[str] = Field(None, description="路由标题", max_length=100)
    meta_icon: Optional[str] = Field(None, description="路由图标", max_length=50)
    meta_hidden: Optional[bool] = Field(None, description="是否隐藏菜单")
    meta_affix: Optional[bool] = Field(None, description="是否固定标签")
    meta_breadcrumb: Optional[bool] = Field(None, description="是否显示面包屑")
    status: Optional[bool] = Field(None, description="菜单状态：True-启用，False-禁用")
    type: Optional[MenuType] = Field(None, description="菜单类型")
    sort: Optional[int] = Field(None, description="排序号")


class SysMenuSimpleResponse(BaseRespEntity):
    """
    系统菜单简单响应模型
    用于只需要展示基本菜单信息的场景
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="菜单ID")
    parent_id: Optional[int] = Field(None, description="父菜单ID")
    name: str = Field(..., description="菜单名称")
    path: Optional[str] = Field(None, description="路由路径")
    type: MenuType = Field(..., description="菜单类型")
    status: bool = Field(..., description="菜单状态")
    sort: int = Field(..., description="排序号")


class SysMenuTreeResponse(BaseRespEntity):
    """
    系统菜单树形响应模型
    用于展示菜单树形结构
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="菜单ID")
    parent_id: Optional[int] = Field(None, description="父菜单ID")
    name: str = Field(..., description="菜单名称")
    path: Optional[str] = Field(None, description="路由路径")
    component: Optional[str] = Field(None, description="组件路径")
    redirect: Optional[str] = Field(None, description="重定向路径")
    permission: Optional[str] = Field(None, description="权限标识")
    meta_title: Optional[str] = Field(None, description="路由标题")
    meta_icon: Optional[str] = Field(None, description="路由图标")
    meta_hidden: bool = Field(..., description="是否隐藏菜单")
    meta_affix: bool = Field(..., description="是否固定标签")
    meta_breadcrumb: bool = Field(..., description="是否显示面包屑")
    status: bool = Field(..., description="菜单状态")
    type: MenuType = Field(..., description="菜单类型")
    sort: int = Field(..., description="排序号")
    children: List["SysMenuTreeResponse"] = Field([], description="子菜单列表")


class SysMenuResponseData(BaseRespEntity):
    """
    系统菜单详细响应模型
    用于展示菜单完整信息
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="菜单ID")
    parentId: Optional[int] = Field(None, description="父菜单ID")
    menuName: str = Field(..., description="菜单名称")
    routeName: Optional[str] = Field(None, description="路由名称")
    routePath: Optional[str] = Field(None, description="路由路径")
    component: Optional[str] = Field(None, description="组件路径")
    icon: Optional[str] = Field(None, description="图标")
    iconType: Optional[str] = Field(None, description="图标类型")
    menuType: str = Field(..., description="菜单类型：1-目录，2-菜单")
    order: int = Field(..., description="排序号")
    i18nKey: Optional[str] = Field(None, description="国际化键")
    keepAlive: bool = Field(False, description="是否缓存")
    constant: bool = Field(False, description="是否常量路由")
    href: Optional[str] = Field(None, description="外链地址")
    hideInMenu: bool = Field(False, description="是否隐藏菜单")
    activeMenu: Optional[str] = Field(None, description="激活的菜单")
    multiTab: bool = Field(True, description="是否多标签")
    fixedIndexInTab: Optional[int] = Field(None, description="固定标签索引")
    query: Optional[dict] = Field(None, description="路由查询参数")
    status: str = Field(..., description="菜单状态：1-启用，2-禁用")
    createTime: str = Field(..., description="创建时间")
    updateTime: Optional[str] = Field(None, description="更新时间")


class SysMenuTreeResponse(BaseRespEntity):
    """
    系统菜单树形响应模型
    用于展示菜单树形结构
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="菜单ID")
    label: str = Field(..., description="菜单标签")
    pId: Optional[int] = Field(None, description="父菜单ID")
    children: List["SysMenuTreeResponse"] = Field([], description="子菜单列表")


class SysMenuBatchUpdateStatus(BaseEntity):
    """
    系统菜单批量更新状态请求模型
    用于批量启用或禁用菜单
    """

    menu_ids: List[int] = Field(..., description="菜单ID列表")
    status: bool = Field(..., description="要设置的状态：True-启用，False-禁用")
