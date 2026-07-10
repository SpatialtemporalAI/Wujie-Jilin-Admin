---
date: 2026-07-10
type: business
---

# 商户开放 API 路径取消 /admin 前缀

## 需求

将商户开放 API 从 `/admin/openapi/v1` 迁移到 `/openapi/v1`，不再经过 `/admin` 前缀。

## 背景

原实现将 `openapi_router` 挂载在 `modules.admin.router`（prefix=/admin）下，导致完整路径为 `/admin/openapi/v1`。用户要求开放 API 直接挂在根路径，与第三方接入方的常见约定一致。

## 实现

- 后端路由 `backend/main.py`
  - 新增 `from modules.merchant.endpoints import openapi_router`
  - 新增 `app.include_router(openapi_router)`，直接挂载到 `/openapi/v1`
- 商户模块路由 `backend/modules/merchant/router.py`
  - 移除 `router.include_router(openapi_router)`
  - 更新注释，说明开放 API 改由主应用直接挂载
- 测试脚本 `backend/scripts/test_merchant_openapi.py`
  - 默认 `base_url` 改回 `http://127.0.0.1:8000`
  - docstring 路径说明改回 `/openapi/v1`
- 文档
  - `backend/docs/merchant-openapi.md`
  - `商户开放API接入文档.md`
  - `aiDoc/frontend-backend/boundary.md`
  - `aiDoc/memory/business/2026-07-01_merchant-openapi-list-endpoints.md`
  - `aiDoc/memory/business/2026-07-06_openapi-param-validation.md`
  - 全部路径示例从 `/admin/openapi/v1` 改回 `/openapi/v1`

## 影响范围

- 鉴权逻辑不变：仍由 `get_current_merchant` 通过 HMAC 签名校验商户。
- 旧路径 `/admin/openapi/v1/*` 404 失效，第三方接入方需改用 `/openapi/v1/*`。
- 后台商户管理接口 `/merchant/*` 和调用日志接口 `/merchant/call-log/*` 不受影响。
