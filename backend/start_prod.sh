#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

export ENVIR=prod

APP_NAME="smilex-cloud"

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8901}"
WORKERS="${WORKERS:-4}"
TIMEOUT="${TIMEOUT:-120}"
MAX_REQUESTS="${MAX_REQUESTS:-5000}"
MAX_REQUESTS_JITTER="${MAX_REQUESTS_JITTER:-500}"
LOG_LEVEL="${LOG_LEVEL:-info}"

PID_DIR="${SCRIPT_DIR}/run"
# 日志目录/文件保持固定名称，由 logrotate（deploy/logrotate/smilex-cloud）按天滚动。
# 归档文件名为：smilex-cloud-YYYY-MM-DD.log
LOG_DIR="${SCRIPT_DIR}/logs"

PID_FILE="${PID_DIR}/${APP_NAME}.pid"
LOG_FILE="${LOG_DIR}/${APP_NAME}.log"

mkdir -p "${PID_DIR}"
mkdir -p "${LOG_DIR}"

# gunicorn路径
if [[ -x "${SCRIPT_DIR}/.venv/bin/gunicorn" ]]; then
    GUNICORN="${SCRIPT_DIR}/.venv/bin/gunicorn"
elif command -v gunicorn &>/dev/null; then
    GUNICORN="$(command -v gunicorn)"
else
    echo "[ERROR] 未找到 gunicorn"
    exit 1
fi

start() {

    if [[ -f "${PID_FILE}" ]]; then
        PID=$(cat "${PID_FILE}")

        if kill -0 "${PID}" 2>/dev/null; then
            echo "[INFO] 服务已运行 PID=${PID}"
            exit 0
        fi

        rm -f "${PID_FILE}"
    fi

    echo "[INFO] 启动 ${APP_NAME}"

    if [[ ! -f "/etc/logrotate.d/${APP_NAME}" ]]; then
        echo "[WARN] 未检测到 logrotate 配置 /etc/logrotate.d/${APP_NAME}，日志不会自动按天滚动"
    fi

    nohup "${GUNICORN}" main:app \
        -w "${WORKERS}" \
        -k uvicorn.workers.UvicornWorker \
        -b "${HOST}:${PORT}" \
        --timeout "${TIMEOUT}" \
        --max-requests "${MAX_REQUESTS}" \
        --max-requests-jitter "${MAX_REQUESTS_JITTER}" \
        --access-logfile - \
        --error-logfile - \
        --log-level "${LOG_LEVEL}" \
        >> "${LOG_FILE}" 2>&1 &

    PID=$!

    echo "${PID}" > "${PID_FILE}"

    sleep 2

    if kill -0 "${PID}" 2>/dev/null; then
        echo "[SUCCESS] 启动成功 PID=${PID}"
        echo "[INFO] 日志文件(gunicorn): ${LOG_FILE}"
        # info.log / error.log 由 logging_prod.ini 的 file handler 写入（同名约定，改 ini 需同步此行）
        echo "[INFO] 日志文件(logging): ${LOG_DIR}/info.log, ${LOG_DIR}/error.log"
    else
        echo "[ERROR] 启动失败"
        exit 1
    fi
}

stop() {

    if [[ ! -f "${PID_FILE}" ]]; then
        echo "[INFO] 服务未运行"
        exit 0
    fi

    PID=$(cat "${PID_FILE}")

    if ! kill -0 "${PID}" 2>/dev/null; then
        rm -f "${PID_FILE}"
        echo "[INFO] 服务已停止"
        exit 0
    fi

    echo "[INFO] 停止服务 PID=${PID}"

    kill -TERM "${PID}"

    for i in {1..30}; do
        if ! kill -0 "${PID}" 2>/dev/null; then
            rm -f "${PID_FILE}"
            echo "[SUCCESS] 已停止"
            return
        fi

        sleep 1
    done

    echo "[WARN] 强制停止"

    kill -9 "${PID}" || true

    rm -f "${PID_FILE}"
}

status() {

    if [[ ! -f "${PID_FILE}" ]]; then
        echo "[INFO] 未运行"
        return
    fi

    PID=$(cat "${PID_FILE}")

    if kill -0 "${PID}" 2>/dev/null; then
        echo "[RUNNING] PID=${PID}"
        ps -fp "${PID}"
    else
        echo "[STOPPED]"
        rm -f "${PID_FILE}"
    fi
}

logs() {
    tail -f "${LOG_FILE}"
}

restart() {
    stop
    sleep 2
    start
}

case "${1:-}" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    logs)
        logs
        ;;
    *)
        echo "用法:"
        echo "  $0 start"
        echo "  $0 stop"
        echo "  $0 restart"
        echo "  $0 status"
        echo "  $0 logs"
        exit 1
        ;;
esac