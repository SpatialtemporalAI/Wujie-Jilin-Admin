# getPermissions 路由/按钮查询补软删除过滤

## 需求描述

`GET /route/getPermissions`（`RouteService.get_user_routes`）此前各查询与遍历都**没有**
`deleted_at IS NULL` 过滤。`soft_delete()` 只置 `deleted_at`、不动 `status`，于是被软删但
`status=True` 的菜单/按钮仍会进入返回结果：超管分支必中，普通用户若曾分配过也会带出，
属于脏数据泄露（方向与「权限没查全」相反）。

排查「用户按钮权限没有查全」时顺带确认了这一点，本次统一补软删过滤。

## 根因（为何按钮「查全」是另一回事，本次只修脏数据）

普通用户按钮权限来自 `role.menus`（`sys_role_menu` 逐行勾选的 BUTTON 记录），**不继承父菜单**：
给角色勾某页面不会自动带其下的 add/edit/delete 按钮。所以按钮「缺失」一般是没分配（如
迁移 0024 拆出的 `scene:map-editor:add` 老角色未勾），属数据问题，不是查询 bug。本次仅修
软删过滤，让软删菜单/按钮彻底退出路由与按钮权限。

## 状态

已完成

## 涉及范围

### 后端

- `backend/modules/admin/services/sys/route_service.py` `get_user_routes`，5 处补 `deleted_at.is_(None)`：
  1. 超管路由查询（顶层 root）
  2. 超管按钮查询（`type=BUTTON`）
  3. 普通用户 `role.menus` 遍历：`if not menu.status or menu.deleted_at is not None: continue`
  4. 祖先补全的 `parent_map` 查询（`select(id, parent_id)`）
  5. 普通 menu_ids 最终查询
- 方法 docstring 补一条过滤说明
- `_menu_to_route` 子节点过滤本就有 `deleted_at is None`，无需改

## 关键决策

### 只加过滤，不改「显式分配」语义

不引入「勾父菜单自动带子按钮」的继承逻辑——按钮粒度仍由 `sys_role_menu` 显式控制。
若以后要改继承语义，需另行评估。

### parent_map 也过滤

祖先补全只遍历 `deleted_at IS NULL` 的行：软删的中途目录会断链，其下的可见菜单
（若存在）不会被挂到已删目录下，符合「软删即不可见」。

## 验证

- `python -m py_compile backend/modules/admin/services/sys/route_service.py` 通过
- `graphify update .` 重建通过

## 相关文件

- `backend/modules/admin/services/sys/route_service.py`
- `backend/modules/admin/endpoints/sys/route.py`（`/route/getPermissions` 入口）
- `backend/database/models/base.py`（`LogicMixin.soft_delete` 仅置 `deleted_at`）

## 记录日期

2026-07-14
