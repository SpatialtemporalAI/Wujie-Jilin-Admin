# 开放商户目录 + 商户 OpenAPI 调用日志

## 需求描述

1. 新建一级菜单目录「**开放商户**」，把原挂在「系统管理 (manage)」下的「商户管理」移到该目录下。
2. 在「开放商户」目录下新增「**调用日志**」菜单，记录第三方商户对开放 API（`/openapi/v1/*`）的调用结果，**全程脱敏**。

## 状态

已完成（前后端 + 迁移 + typecheck 通过；alembic upgrade 待用户在有 DB 的环境执行）

## 涉及范围

### 后端

- **脱敏工具**：`core/security/mask.py`（`mask_api_key` 首尾留 6/4 位、`mask_secret_fields` 递归把 secret/sign/password/token/api_key 等键值替换 `***` 并截断）。与现有 `core/security/sanitize.py`（bleach 防 XSS）分工。
- **Model**：`database/models/business/merchant_call_log.py` → `MerchantCallLog`（merchant_id/name/code 快照、api_key_masked、method/path/action、ip、request_params、response_code/result、success、elapsed_ms、error_msg）。
- **中间件**：`core/middleware/merchant_call_log_middleware.py`，仿 `OperationLogMiddleware` 的 `BaseHTTPMiddleware + BackgroundTask`：仅捕获 `/openapi/v1/*`，掩码 api_key、丢弃 X-Signature/X-Timestamp/X-Nonce、脱敏请求/响应体后落库；用 `MerchantService.get_by_api_key` 解析商户（失败则 merchant 字段为空仍记录）。注册于 `core/registry/setup_registry.py`（RateLimit 之后、OperationLog 之前）。
- **Schema/Service/Endpoint**（merchant 模块，仿 operation_log）：`schemas/call_log.py`、`services/call_log_service.py`、`endpoints/call_log.py`。管理端路由前缀 `/merchant/call-log`（list/detail/export/batch-delete/clear/delete），权限 `merchant:call-log:list` / `merchant:call-log:delete`。挂在 `modules/merchant/router.py`。
- **导出**：`modules/admin/exports/merchant_call_log_export.py` 注册 `merchant_call_log` 导出配置（module_key），前端复用异步导出任务体系 `submitExport('merchant_call_log', ...)`。

### 前端

- 视图目录重构：`views/merchant/` → `views/open-merchant/merchant/`（git 历史经 cp+rm 保留）；新增 `views/open-merchant/call-log/`（index + search + detail-drawer，仿 `views/log/operation-log/`）。
- `pnpm gen-route`（实际由 vite 插件在 dev/build 期重生成）后 `router/elegant/{imports,routes,transform}.ts` + `typings/elegant-router.d.ts` 产出 `open-merchant` 父路由 + `open-merchant_merchant` / `open-merchant_call-log` 子路由。
- i18n：`locales/langs/{zh-cn,en-us}.ts` 新增 `route.open-merchant*` 与 `page.manage.callLog.*`；`typings/app.d.ts` Schema 补 `callLog` 类型块（i18n key 类型由该 Schema 派生，需手改）。
- API/类型：`service/api/call-log.ts` + `service/api/index.ts` barrel + `typings/api/merchant.d.ts` 的 `Api.Merchant.CallLog*`。

### DB 迁移

- `0040_merchant_call_log_table.py`：建 `merchant_call_log` 表（+ merchant_id/created_at 索引）。
- `0041_seed_open_merchant_menu.py`：新增 CATALOG `open-merchant`（id 3000000000000110）；UPDATE 商户菜单（id 3000000000000080）从 `manage_merchant`(/manage/merchant) 改为 `open-merchant_merchant`(/open-merchant/merchant) 挂到新目录下；新增 `open-merchant_call-log` 菜单 + list/delete 按钮。downgrade 还原。

## 约束与备注

- **动态路由模式**（`VITE_AUTH_ROUTE_MODE=dynamic`）：侧边栏由 `sys_menu` 驱动（`route_service._menu_to_route` 产 `i18nKey=route.{name}`、`icon=meta_icon`、`component` 字符串经前端 `imports.ts` 解析）。故菜单重构必须 DB 迁移 + 前端 i18n + 视图目录三处同步，component 字符串（`view.open-merchant_merchant` 等）必须与 `imports.ts` 的键一致。
- **脱敏边界**：api_key 掩码；签名/时间戳/nonce 绝不入库；保留 robot_sn/point_ids/task_id/map_id/text 等业务字段（排查必需、非凭证）；响应体截断 2000 字符。如需进一步掩码 robot_sn，调 `mask_secret_fields` 规则。
- **权限**：超管自动可见；非超管需在「角色管理」分配 `merchant:call-log:list/delete`（与 0034/0039 种子一致，迁移不自动绑角色）。
- **i18n 类型**：`$t` 的合法 key 由 `typings/app.d.ts` 的 `Schema` 类型派生（非自动推断），新增 page 级 key 必须同时改该文件，否则 typecheck 报 I18nKey 错误。
- 复用范式：中间件仿 `operation_log_middleware.py`；日志 service/schema/endpoint 仿 operation_log；菜单种子仿 0039/0034 + 0002 catalog。

## 相关文件

后端：
- `backend/core/security/mask.py`
- `backend/core/middleware/merchant_call_log_middleware.py`
- `backend/core/registry/setup_registry.py`
- `backend/database/models/business/merchant_call_log.py`
- `backend/database/alembic/versions/0040_merchant_call_log_table.py`
- `backend/database/alembic/versions/0041_seed_open_merchant_menu.py`
- `backend/modules/merchant/{schemas/services/endpoints}/call_log*.py`
- `backend/modules/merchant/endpoints/__init__.py`、`router.py`
- `backend/modules/admin/exports/{merchant_call_log_export.py,__init__.py}`

前端：
- `frontend/src/views/open-merchant/{merchant,call-log}/`
- `frontend/src/router/elegant/{imports,routes,transform}.ts`、`frontend/src/typings/elegant-router.d.ts`
- `frontend/src/locales/langs/{zh-cn,en-us}.ts`、`frontend/src/typings/app.d.ts`
- `frontend/src/service/api/call-log.ts`、`index.ts`、`frontend/src/typings/api/merchant.d.ts`

## 记录日期

2026-07-08
