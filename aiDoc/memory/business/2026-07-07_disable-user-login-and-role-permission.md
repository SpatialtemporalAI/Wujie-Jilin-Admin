# 禁用用户不允许登录（+旧会话尽快失效）；禁用角色不加载权限（核实：已实现）

## 需求描述

1. 禁用用户不允许登录。
2. 禁用角色后，拥有该角色的用户登录时不加载该角色的权限。

## 状态

- 需求1 已完成（后端 3 处改动）。`py_compile` 通过；新错误码 `USER_DISABLED(10013)` 验证可访问。
- 需求2 经核实**后端核心已实现，无需改动**（详见下文）。

## 决策（已与用户确认）

- 禁用用户：旧会话也尽快失效（不只挡新登录）。
- 禁用角色：保持现状（核心已实现）。

## 涉及范围

### 后端（需求1，已改）

- `backend/core/response/response_code.py`：新增 `USER_DISABLED = (10013, "用户已被禁用")`。
- `backend/modules/admin/deps/auth/user_manager.py`：
  - `login_by_password`：密码校验通过后加 `if not user.status: raise CustomError(msg="用户已被禁用", error=USER_DISABLED)` —— 登录页展示提示（业务码 10013）。
  - `current_user`：查到用户后加 `if not user.status: raise TokenError(msg="用户已被禁用")` —— 401 触发前端跳登录，已登录会话尽快失效。

### 后端（需求2，未改 —— 已实现）

- 权限码校验 `backend/modules/admin/deps/auth/permission.py:57,104`：`require_permission` / `require_any_permission` 的 JOIN 查询已含 `SysRole.status == True`，禁用角色的按钮权限不会被命中。
- 用户菜单树 `backend/modules/admin/services/sys/menu_service.py` 的 `get_user_menu_tree`：已 `if not role.status: continue` 过滤禁用角色（及禁用菜单），登录后拉 `/admin/sys/menu/user-menus` 不会返回禁用角色的菜单。
- 角色禁用接口 `RoleService.batch_update_roles_status` 已调 `_invalidate_permission_cache()`。

## 约束与备注

- **禁用用户生效延迟**：`current_user` 的 USER 缓存 TTL 30s，`batch_update_users_status` 已调 `_invalidate_user_cache` 清本 worker；多 worker 内存缓存跨进程最长约 30s 完全生效。要更即时需引入 Redis 化会话/缓存或 pub/sub（本次未做）。
- **超管保护**：`batch_update_users_status` 已禁止禁用超级管理员（`user.username == SUPER_ADMIN_USERNAME`），故 `current_user` 的 status 校验不会误伤超管。
- **禁用角色生效延迟**：权限码校验有 ≤60s 多 worker 内存缓存；`_invalidate_permission_cache` 只清本 worker，禁用角色后最长约 60s 完全生效。菜单树无缓存（实时查），登录即最新。
- **JWT 不含权限**：JWT 只放 `user_id`/`session_id`/`role`/`tenant_id`；权限/菜单每次请求或登录后实时查 DB，所以禁用角色对「登录时」立即生效（菜单树实时），仅按钮权限码有缓存延迟。
- **TokenError vs CustomError**：`TokenError`(HTTP 401) 用于踢下线（前端拦截器统一跳登录）；`CustomError`(业务码) 用于登录页提示。`current_user` 用 `TokenError` 让旧会话失效，用户重登时撞 `login_by_password` 的 status 校验看到「用户已被禁用」，闭环。

## 相关文件

- `backend/core/response/response_code.py`（改：加 USER_DISABLED）
- `backend/modules/admin/deps/auth/user_manager.py`（改：login_by_password + current_user）
- 复用（未改，需求2已实现）：`backend/modules/admin/deps/auth/permission.py`、`backend/modules/admin/services/sys/menu_service.py`、`backend/modules/admin/services/sys/role_service.py`、`backend/modules/admin/services/sys/user_service.py`

## 记录日期

2026-07-07
