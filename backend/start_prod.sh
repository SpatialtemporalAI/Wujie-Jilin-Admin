#!/usr/bin/env bash
# 后端生产环境启动脚本（Linux + gunicorn + uvicorn worker）
#
# 用法：
#   ./start_prod.sh
#   # 或通过环境变量覆盖默认配置
#   HOST=0.0.0.0 PORT=8000 WORKERS=4 ./start_prod.sh
#
# 说明：
# - 自动设置 ENVIR=prod，加载 backend/.env.prod
# - 使用 gunicorn 多进程 + uvicorn 异步 worker
# - Windows 不支持 gunicorn，请在 Linux / WSL 运行
# - 生产环境长期运行推荐 systemd（参考 deploy/smilex-cloud.service）

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

export ENVIR=prod

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
WORKERS="${WORKERS:-4}"
TIMEOUT="${TIMEOUT:-120}"
MAX_REQUESTS="${MAX_REQUESTS:-5000}"
MAX_REQUESTS_JITTER="${MAX_REQUESTS_JITTER:-500}"
LOG_LEVEL="${LOG_LEVEL:-info}"

# 优先使用虚拟环境内的 gunicorn，其次用 PATH 中的
if [[ -x "${SCRIPT_DIR}/.venv/bin/gunicorn" ]]; then
    GUNICORN="${SCRIPT_DIR}/.venv/bin/gunicorn"
elif command -v gunicorn &>/dev/null; then
    GUNICORN="gunicorn"
else
    echo "[ERROR] 未找到 gunicorn，请先安装依赖：uv sync" >&2
    exit 1
fi

echo "[INFO] 启动生产环境 | ENVIR=${ENVIR} host=${HOST} port=${PORT} workers=${WORKERS}"

exec "${GUNICORN}" main:app \
    -w "${WORKERS}" \
    -k uvicorn.workers.UvicornWorker \
    -b "${HOST}:${PORT}" \
    --timeout "${TIMEOUT}" \
    --max-requests "${MAX_REQUESTS}" \
    --max-requests-jitter "${MAX_REQUESTS_JITTER}" \
    --access-logfile - \
    --error-logfile - \
    --log-level "${LOG_LEVEL}"
