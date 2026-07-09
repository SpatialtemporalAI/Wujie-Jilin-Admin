# 导出任务弹窗样式优化 + 新增导出任务列表页

## 需求描述

1. 优化顶栏导出任务弹窗样式：可下载状态（状态 Tag）放在任务名旁边；下载入口用图标替代文字按钮，放整行右侧，仅 `completed` 时出现。
2. 弹窗增加「查看全部」，点击跳转到独立的导出任务列表页。
3. （问答）说明弹窗当前显示逻辑。

## 状态

已完成（前端 + 后端）。`pnpm typecheck` 通过。

## 2026-07-09 修正：「查看全部」不跳转

- **现象**：点击导出中心弹窗的「查看全部」没有跳转页面。
- **根因**：项目使用动态路由模式（`VITE_AUTH_ROUTE_MODE=dynamic`），运行时路由由后端 `getPermissions` 返回。由于 `log_export-task` 未建 `sys_menu` 记录，该路由未被注册到运行时路由表，`router.push({ name: 'log_export-task' })` 找不到目标。
- **修复**：前端自治 —— 在 `frontend/src/store/modules/route/index.ts` 的 `initDynamicAuthRoute` 中，将 `log_export-task` 注入到 `log` 菜单的 children 里（`hideInMenu: true`）。这样无需后端建表即可跳转，同时保持页面只在用户有 `log` 菜单权限时才可达。
- **验证**：`pnpm typecheck` 通过。

## 决策（已与用户确认）

- **下载入口**：任务名旁放状态 Tag，整行右侧放下载图标（仅 `completed`），移除原底部独立文字下载按钮。
- **列表页**：新建 `views/log/export-task/`，**不进菜单**，仅靠弹窗「查看全部」入口进入。
  - 2026-07-09 更新：不进菜单的方式从「后端不建 `sys_menu`」改为「前端在动态路由返回后注入该路由并标记 `hideInMenu: true`」，避免路由未注册导致无法跳转。
- **列表页状态筛选**：后端 list 接口加 `status` 可选筛选（endpoint + service），前端 api 适配。
- **pre-existing typecheck 报错**：本次建 view 触发 elegant-router 重生成 d.ts 后，暴露 route 段 `map-editor` / 按钮权限 key（`monitor_view`/`manage_menu_list`/`operation_monitor_list` 等 ~40 个）不在 `I18nRouteKey`。**用户本次选择保留修复**（推翻 [2026-07-07 导出任务卡死修复](./2026-07-07_export-task-stuck-recover-and-timeout.md) 中「不修 map-editor」的决定）：
  - `route.map-editor` → `route.scene_map-editor`（死 key，无 `$t` 使用，对齐路由名）。
  - `I18nRouteKey` 放宽为 `Exclude<RouteKey,'root'|'not-found'> | ${string}_${string}`，让按钮权限文案合法。
  - **副作用**：route 段按钮文案的类型校验被放宽（纯路由 key 仍校验）；长期建议把按钮权限文案迁出 route 段以收紧类型。

## 涉及范围

### 前端

- `frontend/src/layouts/modules/global-header/components/export-center.vue`：样式（状态 Tag 移标题旁 / 下载图标放右侧 / 移除底部按钮行）+「查看全部」入口 `router.push({ name: 'log_export-task' })`。
- `frontend/src/views/log/export-task/index.vue`（新建）：分页表格（`useNaivePaginatedTable` + 自定义 transform 适配 `items→records`）+ 状态筛选（NSelect）+ 下载图标（复用 `fetchDownloadExportFile`）。参考 `views/log/online-user` 模式。
- `frontend/src/service/api/export.ts`：`fetchGetExportTaskList` 加 `status?: string | null`。
- `frontend/src/store/modules/route/index.ts`：在 `initDynamicAuthRoute` 中注入 `log_export-task` 路由（`hideInMenu: true`），修复「查看全部」不跳转。
- `frontend/src/typings/app.d.ts`：手写 Schema `page.log` 加 `exportTask`、`exportCenter` 加 `viewAll`；`I18nRouteKey` 放宽（本项目 I18nKey 基于显式 Schema，新增 key 必须同步，否则 vue-tsc 报 I18nKey 不可赋值）。
- `frontend/src/locales/langs/{zh-cn,en-us}.ts`：`route.log_export-task`、`page.log.exportTask.*`、`exportCenter.viewAll`；`route.map-editor` → `route.scene_map-editor`。
- `frontend/src/router/elegant/{routes,imports,transform}.ts` + `typings/elegant-router.d.ts`：elegant-router 插件自动生成（含 `log_export-task`），无需手改。

### 后端

- `backend/modules/admin/endpoints/sys/export_task.py`：`get_export_task_list` 加 `status: str | None = Query(None)` 透传。
- `backend/modules/admin/services/sys/export_task_service.py`：`get_task_list` 加 `status: str | None = None` 可选筛选。

## 约束与备注

- 列表页不进菜单；若后续要菜单入口，在后端 `sys_menu` 建记录即可（前端路由已就绪）。
- `I18nRouteKey` 放宽是 pragmatic 妥协；长期建议把按钮权限文案迁出 route 段（独立段或 dropdown）以收紧类型。
- 列表页复用现有 `fetchGetExportTaskList`（返回 `items` 非项目通用的 `records`），用自定义 transform 适配，**未改后端响应结构**。
- 弹窗显示逻辑（第 3 点问答）：顶栏云下载图标 NPopover，最近 20 条；展开/挂载/`export:task-submitted` 事件拉取，存在 pending/processing 时每 3s 轮询，全终态停止；每条展示任务名+状态Tag+行数+时间，completed 可下载。

## 相关文件

前端：

- `frontend/src/layouts/modules/global-header/components/export-center.vue`
- `frontend/src/views/log/export-task/index.vue`（新建）
- `frontend/src/service/api/export.ts`
- `frontend/src/typings/app.d.ts`
- `frontend/src/locales/langs/zh-cn.ts`、`frontend/src/locales/langs/en-us.ts`
- 自动生成：`frontend/src/router/elegant/{routes,imports,transform}.ts`、`frontend/src/typings/elegant-router.d.ts`

后端：

- `backend/modules/admin/endpoints/sys/export_task.py`
- `backend/modules/admin/services/sys/export_task_service.py`

## 记录日期

2026-07-07
