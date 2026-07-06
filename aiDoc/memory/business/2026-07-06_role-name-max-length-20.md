---
name: role-name-max-length-20
description: 角色新增/编辑时名称最大长度限制为 20 字符
metadata:
  type: business
---

# 2026-07-06 角色名称最大长度 20 字符

## 需求

角色管理新增/编辑角色时，角色名称长度最大为 20 字符。

## 背景

`SysRoleCreate.name` / `SysRoleUpdate.name` 原先 `max_length=100`，前端 `role-operate-drawer.vue` 的名称输入框 `NInput` 未设置 `maxlength`，用户可输入超长名称，仅在超 100 字符时才被后端 Pydantic 拦截。业务上希望统一收紧到 20 字符并在前端即时限制输入。

## 实现

- 后端：`backend/modules/admin/schemas/sys/role.py` 中 `SysRoleCreate.name`、`SysRoleUpdate.name` 的 `max_length` 由 `100` 改为 `20`，超长时 Pydantic 返回 422。
- 前端：`frontend/src/views/manage/role/modules/role-operate-drawer.vue` 名称 `NInput` 增加 `:maxlength="20"` + `show-count`，沿用项目其它表单（如 `task-operate-drawer` 任务名称 2-20 字）的既有写法，浏览器原生限制输入并显示字数计数。

## 涉及文件

- 后端 schema：`backend/modules/admin/schemas/sys/role.py`（`SysRoleCreate.name`、`SysRoleUpdate.name`）
- 前端表单：`frontend/src/views/manage/role/modules/role-operate-drawer.vue`（名称 `NInput`）
- 参考写法：`frontend/src/views/task/modules/task-operate-drawer.vue`（`:maxlength="20" show-count`）

## 约束与备注

- 仅改请求侧校验长度，未动数据库 `SysRole.name` 列定义（保持现有列宽，存量数据不受影响）。
- 新增/编辑共用同一抽屉组件，前后端一次改动同时覆盖两个入口。
- `desc` 描述字段未要求限制，保持原状。

## 记录日期

2026-07-06
