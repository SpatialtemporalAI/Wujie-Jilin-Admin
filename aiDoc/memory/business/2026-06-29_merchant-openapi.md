# 商户管理 + 商户开放 API

## 需求描述

新增"商户管理"后台模块与面向第三方商户的"开放 API"：
1. 后台可新增/编辑/删除商户，创建时自动生成 `api_key` + `api_secret`（secret 仅展示一次，可重置）。
2. 商户可绑定多台机器人；第三方用 api_key/api_secret 经 HMAC 签名调用开放 API 驱动机器人：
   单点导航 `goto_point`、多点导航 `navigate_route`、执行任务 `execute_task`、
   任务控制 `pause_task`/`resume_task`/`stop_task`、语音播报 `speak`。

## 状态

已完成。菜单与按钮权限种子已写入（迁移 `0034_seed_merchant_menu`，挂载在 manage 目录 2874692539129857 下）；开放 API 接入文档见仓库根目录 `商户开放API接入文档.md`。

## 涉及范围

### 后端

- 新模块 `backend/modules/merchant/`（endpoints/services/schemas/deps/router）
- 新表：`merchant`、`merchant_robot`（迁移 `0033_merchant_tables`）
- 新增 `core/security/crypto.py`（Fernet 可逆加密，HMAC 验签需 api_secret 明文）
- `core/config` 新增 `MERCHANT` 配置（ENCRYPT_KEY / SIGN_TTL_SECONDS / NONCE_TTL_SECONDS）
- 依赖新增 `cryptography`
- 复用：`TaskExecutionRecordService`（start/pause/resume/stop）、`TaskService.get`、
  `VoiceConfigClient.test_tts`；导航请求会落一条临时 Task(task_type=patrol, name 以 `API-` 开头)

### 前端

- `frontend/src/views/manage/merchant/`（index + search + operate-drawer + api-key-modal）
- `frontend/src/service/api/merchant.ts`、`frontend/src/typings/api/merchant.d.ts`
- i18n：`route.manage_merchant` + `page.manage.merchant.*`（zh-cn/en-us/app.d.ts）
- 路由 `manage_merchant`（`@elegant-router` 已生成）

## 约束与备注

- **鉴权**：HMAC-SHA256，头 `X-Api-Key/X-Timestamp/X-Nonce/X-Signature`；
  待签名串 = `{METHOD}\n{path}\n{timestamp}\n{nonce}\n{sha256(body)}`；
  时间戳容差 `MERCHANT__SIGN_TTL_SECONDS`；nonce 防重放走 Redis `set_nx_ex`。
- **api_secret 存储**：Fernet 可逆加密（passphrase 经 PBKDF2 派生密钥），非单向哈希——
  因验签需重算签名。创建/重置时明文仅返回一次。
- **机器人授权**：每个开放 API 请求体带 `robot_sn`，按 `Robot.serial_number` 解析，
  校验该 robot 在 `merchant_robot` 中属于当前商户；导航另校验"点位 map == 机器人 map"。
- **权限码**：`merchant:list/add/edit/delete`（非超管需 sys_menu 种子；超管直通）。
- 导航 = 复用任务管线（gRPC 仅下发 task_id+operation，agent 按 task_id 回查），无独立 goto 通道。

## 相关文件

- 后端：`backend/modules/merchant/`、`backend/core/security/crypto.py`、
  `backend/database/models/business/merchant.py`、`backend/database/models/business/merchant_robot.py`、
  `backend/database/alembic/versions/0033_merchant_tables.py`、
  `backend/database/alembic/versions/0034_seed_merchant_menu.py`、`backend/main.py`
- 文档：仓库根目录 `商户开放API接入文档.md`
- 前端：`frontend/src/views/manage/merchant/`、`frontend/src/service/api/merchant.ts`、
  `frontend/src/typings/api/merchant.d.ts`、`frontend/src/locales/langs/{zh-cn,en-us}.ts`、
  `frontend/src/typings/app.d.ts`
- 契约：`aiDoc/frontend-backend/boundary.md`（商户开放 API 契约段）

## 记录日期

2026-06-29
