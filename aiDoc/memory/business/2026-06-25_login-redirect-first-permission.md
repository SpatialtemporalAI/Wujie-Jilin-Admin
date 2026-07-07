# 登录后默认跳转到权限列表的第一个页面（跳过 /home 仪表盘）

## 需求描述

用户登录后，默认访问页应改为该用户权限列表中的第一个**业务**页面，而不是 `/home` 仪表盘。

- 2026-06-25：去掉硬编码 `home="home"`，改为按菜单顺序取第一个叶子路由。
- 2026-07-06：用户反馈「home 没有权限，登录后自动跳 home 会 404」。明确要求**跳过 `home`**，落在第一个业务菜单，并彻底避免 404。

## 状态

已完成

## 涉及范围

### 后端

- `RouteService.get_user_routes` 在超级用户与普通用户两个分支中，都不再硬编码 `home="home"`
- `RouteService._find_first_leaf_route_name(routes)`：按菜单顺序递归查找第一个组件含 `view.` 的叶子路由名；**跳过名为 `home` 的首页仪表盘**；未找到时回退到 `"home"`

### 前端

- `useRouterPush.redirectFromLogin`：登录后改为**按路由名跳转**到第一个可访问菜单（不再 `toHome()` 走 root 重定向）。按名跳转直接匹配已注册路由，永不回落到 `/home`，根治「home 无权限 → 404」
- `route/shared.ts` 新增 `getFirstMenuRouteKey(menus)`：递归取第一个业务叶子（跳过 `home`），用于决定登录落地页
- 调用 `routeStore.initAuthRoute()` 确保登录跳转前菜单已加载（登录时点 menus 尚未初始化）

## 约束与备注

- **为什么不能只改后端**：前端 root 路由重定向依赖 `getRoutePath(home)`，而 `getRoutePath` 只是 `src/views/` 编译期生成的**静态 routeMap** 查表；当后端回退 `home="home"`（用户无可渲染叶子菜单）或自定义菜单名不在 routeMap 时，root 重定向不更新、保持 `/home`，对无 home 权限的账号 → 被 `:pathMatch(.*)*` 兜底 → 404。前端按名跳转绕开 routeMap，直接用已注册路由，才彻底避免 404
- 叶子路由判定标准：`route.component` 中包含 `view.`（如 `view.manage_user`），过滤掉只作为分组的 catalog 路由
- **跳过 `home`**：`home` 菜单 `sort=1`、`meta_hidden=false`、可见于侧边栏；超级用户若不跳过会落在 `/home`。跳过后用户仍可在侧边栏点击 home 进入仪表盘
- 当用户除 home 外无任何菜单时，`getFirstMenuRouteKey` 返回 null，回退 `toHome()`（保持原行为）
- 其它走 root 重定向的入口（已登录访问 /login、错误页「返回首页」按钮）仍用后端 `home` 值 + `getRoutePath`；对静态菜单正常，自定义菜单仍可能落到 `/home`（本次未改，登录主路径已根治）

## 相关文件

- backend/modules/admin/services/sys/route_service.py
- frontend/src/hooks/common/router.ts
- frontend/src/store/modules/route/shared.ts
- frontend/src/store/modules/route/index.ts（消费 `home` 值，未修改）

## 记录日期

2026-06-25（2026-07-06 更新：跳过 home 仪表盘 + 前端按名跳转根治 404）
