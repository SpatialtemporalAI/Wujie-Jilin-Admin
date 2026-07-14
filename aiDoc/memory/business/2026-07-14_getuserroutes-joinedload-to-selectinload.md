# get_user_routes 改 selectinload 修复权限并集丢失

## 需求描述

用户登录后 `getPermissions` 返回的角色权限**并集存在丢失**（多角色用户少了部分权限）。

## 根因

`get_user_routes` 普通用户分支用 `joinedload(SysUser.roles).joinedload(SysRole.menus)`
**把关系加载并进主 SELECT**。两个全局 `do_orm_execute` 过滤器——
[setup_database.py](backend/database/plugins/setup_database.py) 软删、
[tenant_filter.py](backend/plugins/multi_tenant/database/tenant_filter.py) 租户——都带
`not execute_state.is_relationship_load`，即**只在主查询生效、跳过关系查询**。

joinedload 时 `is_relationship_load=False`，过滤**作用到 roles/menus 上**：
- 多租户开启（`.env.backup` 即如此）+ `sys_role` 严格隔离 → `sys_role.tenant_id == 当前租户`，
  分配给用户的**全局角色（tenant_id=NULL）被裁掉**，整组权限丢失；
- 软删过滤同样作用到 join（活数据不丢，但属同类隐患）。

## 状态

已完成

## 涉及范围

### 后端

- `backend/modules/admin/services/sys/route_service.py` `get_user_routes` 普通用户分支：
  - `joinedload(SysUser.roles).options(joinedload(SysRole.menus))`
    → `selectinload(SysUser.roles).selectinload(SysRole.menus)`
  - `result.unique().scalar_one()` → `result.scalar_one()`（selectinload 不产生重复主行，无需 unique）
  - import 去掉 `joinedload`
- 软删由循环内 `menu.deleted_at is not None` 兜底（selectinload 关系查询不被全局软删过滤）

## 关键决策

### selectinload 而非给查询加 ignore_tenant

权限是「该用户所有角色」的并集，角色已由 `user.roles` 关联界定，再按租户裁 `sys_role`
是多余且有害的。selectinload 让关系查询天然绕过全局过滤（`is_relationship_load=True`），
语义最干净；也顺带消除了嵌套集合 joinedload 的笛卡尔积，是 SA 官方推荐写法。

### 与上一条软删过滤修复的关系

承接 [[2026-07-14_route-getpermissions-soft-delete-filter]]：那次补的是显式查询的 deleted_at；
这次解决的是「关系加载被全局过滤裁剪」导致的并集丢失，两者正交。

### 当前 dev/prod 关着多租户

`.env.dev`/`.env.prod` 无 PLUGINS 行（默认 `[]`）。本修复在关多租户时是预防性的
（活数据本就不丢），在 `.env.backup` 这类开了多租户的部署里才直接命中并修复丢失。
若现象仍存在且确认关着多租户，需查数据（角色是否禁用、按钮是否在 sys_role_menu 显式分配）。

## 验证

- `python -m py_compile backend/modules/admin/services/sys/route_service.py` 通过
- `graphify update .` 重建通过

## 相关文件

- `backend/modules/admin/services/sys/route_service.py`
- `backend/database/plugins/setup_database.py`（全局软删过滤）
- `backend/plugins/multi_tenant/database/tenant_filter.py`（全局租户过滤）
- `backend/plugins/multi_tenant/plugin.py`（`sys_role` strict / `sys_menu` optional）

## 记录日期

2026-07-14
