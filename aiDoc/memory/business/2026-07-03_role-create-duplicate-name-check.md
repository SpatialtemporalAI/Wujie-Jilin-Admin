---
name: role-create-duplicate-name-check
description: 角色新增时名称重复需抛出友好异常提示
metadata:
  type: business
---

# 2026-07-03 角色新增重名校验

## 需求

角色管理新增角色时，若角色名称与已有角色同名，需抛出友好异常提示"角色名称已存在"，而不是落到数据库 `unique` 约束的 `IntegrityError`。

## 背景

`SysRole.name` 在模型层是 `unique=True`，但 `RoleService.create_role` 的 docstring 虽声明 `Raises: ConflictError: 角色名称已存在`，代码实际未做重名校验，直接 `db.add` 后 commit，重名时只触发底层 IntegrityError，前端拿不到清晰提示。

## 实现

沿用字典 `DictService.create_dict` 校验 `code` 唯一的模式：创建前先查同名角色，存在则 `raise ConflictError(msg="角色名称已存在")`。

异常渲染链路（无需改前端）：
- 后端 `conflict_error_handler` → `base_exception_handler` 返回 `HTTP 409` + 统一响应体 `{ code: 409, msg: "角色名称已存在", ... }`
- 前端 `createFlatRequest` 的 `onError` 读 `error.response.data.msg` → `showErrorMsg` → `window.$message.error(msg)` 自动弹出

## 涉及文件

- 后端服务：`backend/modules/admin/services/sys/role_service.py`（`create_role` 增加重名查询）
- 参考实现：`backend/modules/admin/services/sys/dict_service.py`（`create_dict` 校验 `code`）
- 异常处理器：`backend/core/exception/errors_handler.py`（`conflict_error_handler`）
- 前端拦截器：`frontend/src/service/request/index.ts`（`onError`）+ `shared.ts`（`showErrorMsg`）
- 模型：`backend/database/models/sys/role.py`（`name` 列 `unique=True`）

## 约束与备注

- `SysRole` 为物理删除（无软删除 `deleted_at`），重名查询无需排除已删除记录
- 本次仅覆盖新增；编辑改名导致冲突仍会由 DB `unique` 约束兜底（如需友好提示可后续补 `update_role` 校验）
- 未改前端代码，提示完全依赖全局响应拦截器

## 记录日期

2026-07-03
