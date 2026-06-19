# NotifyMapSaved image_url 改为 HMAC 签名 URL（带时效）

## 需求描述

导览服务通过 gRPC `NotifyMapSaved` 收到的 `MapInfo.map.image_url` 此前是相对路径（`/st/admin/sys/file/{id}/preview`），无法直接拉图；preview 端点原本强制 JWT token 鉴权，导览服务侧处理不便。

迭代历程：
1. v1：URL 自带固定 `internal_token`（query 形式）—— 可直接 GET，但密钥永久暴露在 URL/log 里
2. **v2（当前实现）**：HMAC 签名 URL（?expires=&sig=）—— URL 不暴露密钥，有时效，可直接 GET

## 状态

已完成

## 涉及范围

### 后端

- 配置：`backend/core/config/settings_model.py` `ServiceModel` 新增
  - `BASE_URL`：对外可访问基础 URL（协议+host+port），用于拼接完整 URL
  - `INTERNAL_TOKEN`：HMAC 密钥；非空即启用签名 URL 模式
  - `FILE_PREVIEW_TTL_SECONDS`：签名 URL 默认有效期，默认 600 秒
- 环境变量：`.env.dev/.env.test/.env.prod` 配置 `SERVICE__BASE_URL` / `SERVICE__INTERNAL_TOKEN`
- 新建：`backend/core/security/file_signature.py`
  - `compute_sig(file_id, expires)` → HMAC-SHA256 hex
  - `verify(file_id, expires, sig)` → bool（含过期校验、防时序攻击的 compare_digest）
  - `build_signed_url(file_id, ttl)` → 完整签名 URL
  - `is_enabled()` → 是否启用签名模式（INTERNAL_TOKEN 非空）
- 端点：`backend/modules/admin/endpoints/sys/file.py`
  - `preview_router` 不再使用 router-level 鉴权依赖
  - `preview_file` 函数体统一处理三种鉴权（任一通过即可）：
    1. 签名 URL：`?expires=&sig=`（验签 + 过期校验）
    2. 内部 header：`X-Internal-Token: <INTERNAL_TOKEN>`（仍保留以备无 URL 改造能力的客户端）
    3. JWT：`?token=<JWT>`（浏览器/前端原行为）
- 服务：`backend/modules/admin/services/sys/file_service.py` `get_file_url`
  - 启用签名模式：返回 `build_signed_url(file_id)`
  - 未启用：回退为相对路径（向后兼容）
- gRPC 转换器：`backend/modules/grpc/converter.py` docstring 更新为签名 URL 形态，转换逻辑不变
- 脚本：`backend/scripts/dump_notify_map_saved.py` `build_image_url` 复用 `build_signed_url`

### 前端

无（浏览器/前端仍走 `?token=<JWT>`，行为不变）

## 约束与备注

- HMAC 密钥 = `SERVICE.INTERNAL_TOKEN`，该字段非空时：
  - 启用签名 URL（推荐）
  - 同时保留 header 旁路（应急/调试）
- 签名 URL 有效期默认 600 秒，可通过 `FILE_PREVIEW_TTL_SECONDS` 调整
- 导览服务侧需在 TTL 窗口内拉图，过期需后端重新推送
- HMAC 校验使用 `hmac.compare_digest` 防时序攻击
- `INTERNAL_TOKEN` 不入 git，三个环境使用不同值；轮换只需修改 `.env` 并重启
- converter 不读 settings，URL 生成责任在 `FileService.get_file_url`
- 路由实际路径不包含 `SERVICE.PREFIX`（该字段在项目代码中未实际使用）

## URL 形态

```
http://<host>:<port>/admin/sys/file/{file_id}/preview?expires=<unix_ts>&sig=<hmac_sha256_hex>
```

## 相关文件

- backend/core/config/settings_model.py
- backend/core/security/file_signature.py（新建）
- backend/.env.dev / .env.test / .env.prod
- backend/modules/admin/endpoints/sys/file.py
- backend/modules/admin/services/sys/file_service.py
- backend/modules/grpc/converter.py
- backend/modules/scene/services/scene_map_nav_image_service.py（调用方，未改逻辑）
- backend/scripts/dump_notify_map_saved.py

## 记录日期

2026-06-18
