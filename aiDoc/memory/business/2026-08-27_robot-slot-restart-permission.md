# 机器人「重启」按钮独立权限点 robot:manage:restart

## 需求描述

机器人卡片「服务器自启状态」行的「重启」按钮原复用 `robot:manage:edit` 权限，需要拆成独立的按钮权限点，方便在角色管理中单独分配。

## 状态

已完成

## 涉及范围

- `frontend/src/views/robots/index.vue`：重启按钮 `v-if="hasAuth('robot:manage:edit')"` → `hasAuth('robot:manage:restart')`（同页其它编辑类按钮仍用 `robot:manage:edit`，不动）
- `backend/modules/robot/endpoints/robot.py`：`POST /manage/{robot_id}/slot-restart` 的 `require_permission("robot:manage:edit")` → `require_permission("robot:manage:restart")`；`slot-status` 查询仍用 `robot:manage:list`，不动
- `backend/database/alembic/versions/0006_seed_robot_slot_restart_button.py`（新增）：BUTTON 种子 `robot_manage_restart`（id 3000000000000124，parent = robots 菜单 3000000000000003，permission `robot:manage:restart`，sort 6 接在 grpc_config 之后）；downgrade 按 id 删除
- `frontend/src/locales/langs/zh-cn.ts` / `en-us.ts`：补 `route.robot_manage_restart`（重启 / Restart），BUTTON 节点 i18nKey = `route.{name}` 的既定规则

## 关键决策

- **权限码命名**：沿用 `robot:manage:*` 段，取 `robot:manage:restart`
- **种子只写新迁移**：0004（voice-consultation）起新种子不再镜像回 `0002_seed_data.py`，本次同样只写 0006
- **不自动绑角色**：与既有种子一致，超管直通；非超管需在「角色管理」给角色勾上该按钮权限后前端按钮才显示

## 约束与备注

- 前端只做 typecheck（项目约定 [[feedback-typecheck-only]]），`npm run typecheck` 通过；后端迁移与 endpoint 做了 AST 语法校验
- 部署后需执行 `alembic upgrade head` 应用 0006，并在角色管理中为非超管角色分配 `robot:manage:restart`

## 记录日期

2026-08-27
