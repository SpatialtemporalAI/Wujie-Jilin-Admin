# 登录后默认跳转到权限列表的第一个页面

## 需求描述

用户登录后，默认访问页应改为该用户权限列表中的第一个页面，而不是始终硬编码重定向到 `/home`。

## 状态

已完成

## 涉及范围

### 后端

- `RouteService.get_user_routes` 在超级用户与普通用户两个分支中，都不再硬编码 `home="home"`
- 新增 `RouteService._find_first_leaf_route_name(routes)` 工具方法：按菜单顺序递归查找第一个组件含 `view.` 的叶子路由名（即真实页面），未找到时回退到 `"home"`

### 前端

无。前端 `initDynamicAuthRoute` 已正确使用后端返回的 `home` 值（`setRouteHome(home)` + `handleUpdateRootRouteRedirect(home)`），无需改动。

## 约束与备注

- 叶子路由判定标准：`route.component` 中包含 `view.`（如 `view.manage_user` 或 `layout.base$view.home`），过滤掉只作为分组的 catalog 路由
- 当用户无任何可访问路由（如未分配角色或角色被禁用）时，仍回退到 `"home"`，保持与原行为兼容
- 若返回的 `home` 名称不在前端 `routeMap` 中（如自定义菜单），`getRoutePath` 返回 `undefined`，`handleUpdateRootRouteRedirect` 不更新根路由，最终使用 `ROOT_ROUTE` 默认 `/home` 重定向
- 超级用户场景下由于菜单按 `sort, id` 排序，`home` 菜单 sort=1，因此仍会被选为首页（行为上等价）；本变更主要影响普通用户

## 相关文件

- backend/modules/admin/services/sys/route_service.py
- frontend/src/store/modules/route/index.ts（消费 `home` 值，未修改）

## 记录日期

2026-06-25
