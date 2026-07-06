---
name: role-name-max-length-20
description: 角色新增/编辑时名称最大 20 字符、描述最大 200 字符
metadata:
  type: business
---

# 2026-07-06 角色名称与描述长度限制

## 需求

角色管理新增/编辑角色时：
- 角色名称 `name` 长度最大为 20 字符；
- 角色描述 `desc` 长度最大为 200 字符。

## 背景

`SysRoleCreate` / `SysRoleUpdate` 原先 `name` 为 `max_length=100`、`desc` 未限制长度，前端 `role-operate-drawer.vue` 的名称/描述 `NInput` 均未设置 `maxlength`，用户可输入超长内容，仅在超 100 字符（名称）时被后端 Pydantic 拦截，描述则无任何上限。业务希望统一收紧并在前端即时限制输入、显示字数。

## 实现

- 后端：`backend/modules/admin/schemas/sys/role.py`
  - `SysRoleCreate.name` / `SysRoleUpdate.name` 的 `max_length` 由 `100` 改为 `20`
  - `SysRoleCreate.desc` / `SysRoleUpdate.desc` 增加 `max_length=200`
  - 超长时由 Pydantic 返回 422
- 前端：`frontend/src/views/manage/role/modules/role-operate-drawer.vue`
  - 名称 `NInput` 增加 `:maxlength="20"` + `show-count`
  - 描述 `NInput` 增加 `:maxlength="200"` + `show-count`
  - 沿用项目其它表单（如 `task-operate-drawer` 任务名称 2-20 字）的既有写法，浏览器原生限制输入并显示字数计数

## 涉及文件

- 后端 schema：`backend/modules/admin/schemas/sys/role.py`（`SysRoleCreate`、`SysRoleUpdate` 的 `name`、`desc`）
- 前端表单：`frontend/src/views/manage/role/modules/role-operate-drawer.vue`（名称、描述 `NInput`）
- 参考写法：`frontend/src/views/task/modules/task-operate-drawer.vue`（`:maxlength="20" show-count`）

## 约束与备注

- 仅改请求侧校验长度，未动数据库 `SysRole.name` / `SysRole.desc` 列定义（保持现有列宽，存量数据不受影响）。
- 新增/编辑共用同一抽屉组件，前后端一次改动同时覆盖两个入口。
- 描述 `NInput` 维持单行输入未改 `type="textarea"`，仅加长度限制。

## 记录日期

2026-07-06
