# 日志管理三页面增加导出 Excel（复用异步导出任务体系 + 顶栏下载箱）

## 需求描述

「日志管理」下三个历史日志页面需要按当前筛选条件导出 Excel：

- 登录日志（login-log）
- 操作日志（operation-log）
- 机器人事件日志（robot-log）

下载入口为顶部栏通知图标旁新增的「下载箱」图标：点开弹出导出记录列表，任务完成后手动点击下载。不在页面内自动下载、不在页面内轮询。不含「在线用户」（实时会话状态，非历史日志）。

## 状态

已完成（前端 + 后端）。`pnpm typecheck` 本次改动文件无新增报错（既有 `locales/langs` 的 `map-editor` 路由 i18n 报错为 pre-existing，与本次无关，用户选择不修）。

## 涉及范围

### 后端

复用既有异步导出任务体系（`core/utils/excel_export.py` 构建器 + `modules/admin/exports/` 注册表 + `export_task_service.py` 后台任务 + `/admin/sys/export/task` 端点）。三个日志 service 的 `build_xxx_query` 与 QueryParams schema 均已存在，仅差 export 配置文件：

- 新建 `backend/modules/admin/exports/login_log_export.py`：列 id/username/ip/status(成功/失败)/detail/user_agent/login_time，复用 `LoginLogService.build_login_log_query` + `LoginLogQueryParams`，module_key=`login_log`。
- 新建 `backend/modules/admin/exports/robot_event_log_export.py`：跨模块导入 `RobotEventLogService` + `RobotEventLogQueryParams`，列 id/robot_id/event_type/event_status/event_content/created_at，module_key=`robot_event_log`。
- `backend/modules/admin/exports/__init__.py` 末尾 import 追加 `login_log_export, robot_event_log_export`。
- 操作日志（operation_log）后端导出早已注册，零改动。

约束：机器人事件日志导出列用 `robot_id`（非 robot_name）——`build_event_log_query` 只查单表不含 JOIN，普通导出路径（`result.unique().scalars().all()`）取不到 robot_name；为最小侵入未改通用导出服务。（注：该约束已于 2026-07-14 通过通用 `enrich_fn` 回调补齐 `robot_name` 列解除，见 [[2026-07-14_robot-event-log-search-export-fix]]）

### 前端

前端此前从未接入导出功能，本次首次接入：

- 新建 `frontend/src/service/api/export.ts`：4 个接口（submit/list/status/download），下载用原生 axios + `responseType:'blob'`（不经 request 封装，因 `request` transform 会取 `response.data.data`，不适用于 blob）。
- 新建 `frontend/src/typings/api/export.d.ts`：`Api.Export.ExportTask` 类型。
- 新建 `frontend/src/hooks/business/export-task.ts`：`useExportSubmit` hook，仅提交任务（剔除 page/page_size）+ 提示「请到顶部下载箱下载」+ dispatch `window` 自定义事件 `export:task-submitted`；不轮询、不下载。
- 新建 `frontend/src/layouts/modules/global-header/components/export-center.vue`：下载箱组件，仿 `notification-center.vue` 的 NPopover 模式；进行中任务每 3s 轮询、监听 `export:task-submitted` 立即刷新、completed 项手动下载（`URL.createObjectURL`+`<a>.click()`）、failed 显示错误、`onUnmounted` 清理。
- `global-header/index.vue` 在 `<NotificationCenter />` 后挂 `<ExportCenter />`。
- 三个日志页 `index.vue` 的 `TableHeaderOperation #prefix` 插槽加「导出」按钮，调 `submitExport(module_key, searchParams)`。
- i18n：`common` 加 export/exporting/exportTaskSubmitted/exportFailed；新增 `exportCenter` 块（title/download/noRecords/refresh/rows/statusPending/Processing/Completed/Failed），Schema（app.d.ts）+ zh-cn + en-us 三处同步。

## 约束与备注

- 复用项目既有异步导出任务体系，未新增同步导出接口，未改通用导出服务。
- 导出按钮不加权限码（后端 `/admin/sys/export/task` 端点本身无 `require_permission`，所有登录用户可调）；强行加前端权限会变成「看得见调不通」的半成品。
- 下载箱用 Popover（与通知中心对称），非独立路由页；如需「导出任务」菜单页可后续扩展。
- `request` 是 `createFlatRequest`，返回 `{ data, error }`（解构取值）；错误消息由 request 的 onError 统一展示。
- 后端 list 端点返回 `{ items, total, page, page_size }`（非统一分页的 `records`）。
- 后端改动需重启 FastAPI 服务才生效。

## 相关文件

后端：

- `backend/modules/admin/exports/login_log_export.py`（新建）
- `backend/modules/admin/exports/robot_event_log_export.py`（新建）
- `backend/modules/admin/exports/__init__.py`（改 1 行 import）
- 复用（未改）：`backend/core/utils/excel_export.py`、`backend/modules/admin/services/sys/export_task_service.py`、`backend/modules/admin/endpoints/sys/export_task.py`、各日志 `build_xxx_query` service 与 QueryParams schema

前端：

- `frontend/src/service/api/export.ts`（新建）、`frontend/src/service/api/index.ts`（加聚合）
- `frontend/src/typings/api/export.d.ts`（新建）、`frontend/src/typings/app.d.ts`（i18n Schema 加 key）
- `frontend/src/hooks/business/export-task.ts`（新建）
- `frontend/src/layouts/modules/global-header/components/export-center.vue`（新建）、`frontend/src/layouts/modules/global-header/index.vue`（挂载）
- `frontend/src/views/log/{login-log,operation-log,robot-log}/index.vue`（加导出按钮）
- `frontend/src/locales/langs/{zh-cn,en-us}.ts`（i18n 文案）

## 记录日期

2026-07-06
