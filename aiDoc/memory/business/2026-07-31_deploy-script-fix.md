---
name: 2026-07-31_deploy-script-fix
description: deploy.sh 部署流程修复：配置内联、submodule 同步、alembic 在 backend/database 执行
metadata:
  type: business
---

# 2026-07-31 deploy.sh 部署流程修复

## 背景

用户反馈 deploy.sh 目录引用有问题。审查发现：配置通过 `source deploy.env` 间接加载（路径不直观）；git 操作在 `BACKEND_DIR` 而非仓库根 `PROJECT_DIR`，且未同步 submodule；alembic 实际应在 `backend/database` 执行却在 `BACKEND_DIR`。

## 关键事实

- `backend/database`、`backend/grpc` 是 git submodule（见 `.gitmodules`）。
- `alembic.ini` 位于 `backend/database/alembic.ini`，alembic 必须在 `backend/database` 目录执行。
- `backend/.env.prod` 是 git 追踪的（入库）。

## 修改文件

- [deploy/deploy.sh](../../../deploy/deploy.sh)
  - **配置内联**：删除 `source deploy.env`，所有配置变量（`APP_NAME`/`PROJECT_DIR`/`BACKEND_DIR`/`VENV_DIR`/`DATABASE_DIR`/`GUNICORN_*`/`LOG_DIR`/`ENV_FILE` 等）直接写在脚本顶部；新增 `DATABASE_DIR="${BACKEND_DIR}/database"`。
  - **git 目录**：`cmd_deploy`/`cmd_rollback`/`cmd_status` 的 git 操作统一 `cd "${PROJECT_DIR}"`（仓库根）。
  - **submodule 同步**：`cmd_setup` 加 `git submodule update --init --recursive`；`cmd_deploy` 的 `git pull` 后、`cmd_rollback` 的 `git reset --hard` 后均补 `git submodule update --init --recursive`。
  - **alembic 目录**：setup/deploy/rollback 的 `alembic upgrade head` 改为 `cd "${DATABASE_DIR}"` 后执行。
  - `uv sync` 始终在 `BACKEND_DIR`（pyproject.toml 所在）执行。
  - 顺带：`cmd_setup` 加 `LOG__DIR` 与 `LOG_DIR` 一致性校验（见 [[2026-07-10_log-date-rolling]]）。

## 注意

- 原 `deploy/deploy.env` 不再被读取，已成孤儿文件，建议删除或改名 `.example`。
- 遗留（未处理）：`cmd_setup` 里 `.env.prod` 不存在时的 `cp` 自己死代码（因 `.env.prod` 入库不触发）；systemd 方式下 gunicorn `--error-logfile` 与 Python `errorFileHandler` 同名共用 `error.log`（见 [[2026-07-10_log-date-rolling]]）。
