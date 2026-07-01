# 前后端生产环境启动脚本

## 需求描述

为前端和后端分别提供一条"生产环境启动"命令，避免每次手动拼接 build / preview 或 gunicorn 参数。

- 前端：一条命令完成生产构建 + 预览（基于 vite preview）
- 后端：一条命令以生产模式启动 gunicorn + uvicorn worker（仅 Linux）

## 状态

已完成

## 涉及范围

### 后端

- 新增 `backend/start_prod.sh`：
  - `set -euo pipefail` + `exec` 启动 gunicorn，信号直通主进程
  - `export ENVIR=prod` 触发 `core/config` 加载 `backend/.env.prod`
  - 默认 `WORKERS=4 / TIMEOUT=120 / MAX_REQUESTS=5000 / MAX_REQUESTS_JITTER=500`，与 `deploy/smilex-cloud.service` 保持一致
  - `HOST/PORT/WORKERS/TIMEOUT/MAX_REQUESTS/MAX_REQUESTS_JITTER/LOG_LEVEL` 可通过环境变量覆盖
  - 优先使用 `backend/.venv/bin/gunicorn`，缺失时回退到 PATH 中的 gunicorn；都找不到时报错退出
  - `--access-logfile -` / `--error-logfile -` 日志直接打到 stdout/stderr，方便容器或 systemd 收集
  - 文件已在 git index 中标记为可执行（`100755`）

### 前端

- `frontend/package.json` `scripts` 新增 `"start:prod": "vite build --mode prod && vite preview"`：
  - 先用 prod 模式构建产物到 `dist/`
  - 再用 `vite preview` 启动本地静态服务器预览
  - 与既有 `dev` / `dev:prod` / `build` / `preview` 命名风格一致

## 约束与备注

- 后端脚本仅支持 Linux/WSL（gunicorn 不支持 Windows）。Windows 本地开发继续用 `python main.py` 或 `uvicorn main:app --reload`。
- 后端脚本面向"手动 / 临时启动"场景；正式生产部署仍推荐 systemd（参考 `deploy/smilex-cloud.service`）+ `deploy/deploy.sh`，可享受自动重启、日志轮转、健康检查。
- 后端脚本运行前需保证 `backend/.env.prod` 已正确配置（DB / Redis / JWT / gRPC 等）。
- 配置加载一致性（2026-07-01 修复）：`backend/database/config.py` 的 `settings` 现已按 `ENVIR` 选择 `.env.{env}`（与 `core/config` 对齐）。此前该处写死 `env_file=".env"`、无视 `ENVIR=prod`，导致 prod 启动时数据库连接池退回 `DatabaseModel` 默认值（`mysql/root/localhost`），报 `(pymysql.err.OperationalError) (1698, "Access denied for user 'root'@'localhost'")`。注意项目存在两套并行配置体系（`core/config/` 与 `database/config.py`），后者供数据库连接池使用。
- 前端 `vite preview` 仅用于本地预览生产产物，**不是**生产级静态服务器；正式部署应使用 nginx（参考 `deploy/nginx.conf`）。
- 前端 `.env.prod` 中 `VITE_SERVICE_BASE_URL` 当前指向 mock，正式部署前需替换为真实后端地址。

## 相关文件

- `backend/start_prod.sh`
- `frontend/package.json`
- `deploy/smilex-cloud.service`（参考的 gunicorn 参数来源）
- `deploy/deploy.env`（参考的默认值来源）

## 记录日期

2026-06-18
