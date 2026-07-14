---
name: role-edit-duplicate-name-check
description: 角色编辑改名重名应抛 ConflictError 409，而非 IntegrityError 兜底成 500
metadata:
  type: business
---

# 2026-07-14 角色编辑重名校验

## 需求

角色管理「编辑角色」时，若把名称改成已存在的角色名，期望提示"角色名称已存在"（HTTP 409），而不是报"服务器错误"（HTTP 500）。

## 背景 / 根因

`SysRole.name` 在模型层 `unique=True`。`RoleService.update_role` 此前未做重名校验，编辑改名命中已存在名称时，`db.commit()` 触发数据库唯一约束 → SQLAlchemy 抛 `IntegrityError`。

项目全局异常处理器（`errors_handler.py`）未注册 `IntegrityError`，落入兜底的 `generic_exception_handler` → 返回 `HTTP 500 服务器内部错误`。因此前端看到的是"服务器错误"，实际语义应是名称冲突。

对比 [[role-create-duplicate-name-check]]（2026-07-03 新增场景已有校验），编辑场景此前靠 DB `unique` 约束兜底——但该兜底是不友好的 500，正是本次要修的点。

## 实现

沿用 `create_role` 的重名查询模式，在 `update_role` 取出 `update_data` 后、commit 前补校验：

- 仅当请求显式携带 `name`（`exclude_unset=True`，未传 name 不校验）且新名与原名不同时才查询
- 查询排除自身 `SysRole.id != role_id`，避免对自己查重
- 命中则 `raise ConflictError(msg="角色名称已存在")`

异常渲染链路与新增一致，前端无需改动：`conflict_error_handler` → `base_exception_handler` 返回 409，前端 `createFlatRequest` 的 `onError` 读 `error.response.data.msg` 自动 toast。

## 涉及文件

- 后端服务：`backend/modules/admin/services/sys/role_service.py`（`update_role` 增加重名查询 + docstring `Raises` 补 `ConflictError`）
- 关联前序：[[role-create-duplicate-name-check]]（`create_role` 重名校验）
- 异常处理器：`backend/core/exception/errors_handler.py`（`conflict_error_handler`、`generic_exception_handler` 兜底）
- 模型：`backend/database/models/sys/role.py`（`name` 列 `unique=True`）

## 约束与备注

- 角色为物理删除：`delete_role` 用 `db.delete(role)`，不写 `deleted_at`（模型虽继承 `LogicMixin` 有该列，但删除时始终为 NULL），故重名查询无需排除软删除记录
- 仅在请求携带 `name` 时校验，纯改描述 / 菜单 / 状态不触发
- 未改前端，提示依赖全局响应拦截器

## 记录日期

2026-07-14
