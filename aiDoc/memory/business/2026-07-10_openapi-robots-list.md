---
date: 2026-07-10
type: business
---

# 商户开放 API 新增机器人列表查询接口

## 需求

在商户开放 API 中新增 `POST /openapi/v1/robots` 接口，返回当前商户已绑定的机器人列表，字段包括 `id`、`name`、`sn`。

## 实现

- `backend/modules/merchant/schemas/openapi.py`
  - 新增 `RobotsRequest(BaseEntity)`（当前无过滤参数，请求体可传 `{}`）
- `backend/modules/merchant/services/openapi_service.py`
  - 新增 `list_robots(db, merchant)` 方法：通过 `_merchant_robot_ids` 取关联机器人 ID，再查询 `Robot.id/name/serial_number`，按 `id` 倒序返回
- `backend/modules/merchant/endpoints/openapi.py`
  - 注册 `POST /openapi/v1/robots` 路由，HMAC 签名鉴权
- `backend/scripts/test_merchant_openapi.py`
  - 新增 `test_robots()` 和 `--test-robots` 参数
- 文档
  - `backend/docs/merchant-openapi.md`
  - `商户开放API接入文档.md`
  - `aiDoc/frontend-backend/boundary.md`
  - 全部补充 `/openapi/v1/robots` 接口说明

## 接口契约

| 方法 | 路径 | 请求体 | 响应 data |
|---|---|---|---|
| POST | `/openapi/v1/robots` | `{}` | `{ robots: [{ id, name, sn }] }` |

## 影响范围

- 纯新增接口，不影响现有接口行为。
- 第三方接入方可先调用 `/robots` 获取 `robot_sn`，再调用控制类接口。

## 相关文件

- `backend/modules/merchant/schemas/openapi.py`
- `backend/modules/merchant/services/openapi_service.py`
- `backend/modules/merchant/endpoints/openapi.py`
- `backend/scripts/test_merchant_openapi.py`
