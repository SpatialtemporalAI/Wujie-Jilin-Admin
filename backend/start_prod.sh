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
TAIL_LINES="${TAIL_LINES:-100}"

PID_DIR="${SCRIPT_DIR}/run"
# 日志目录/文件保持固定名称，由 logrotate（deploy/logrotate/smilex-cloud）按天滚动。
# 归档文件名为：smilex-cloud-YYYY-MM-DD.log
LOG_DIR="${SCRIPT_DIR}/logs"

PID_FILE="${PID_DIR}/${APP_NAME}.pid"
LOG_FILE="${LOG_DIR}/${APP_NAME}.log"

# Python 应用日志目录由 settings.LOG.DIR 决定（.env / .env.prod 的 LOG__DIR，后者覆盖前者）。
# prod 默认指向 /var/log/smilex_cloud，与脚本内 LOG_DIR(=backend/logs) 不同，解析真实路径用于启动提示。
APP_LOG_DIR="${LOG_DIR}"
for _env in "${SCRIPT_DIR}/.env" "${SCRIPT_DIR}/.env.prod"; do
    if [[ -f "${_env}" ]]; then
        _parsed=$(grep -iE '^[[:space:]]*LOG__DIR[[:space:]]*=' "${_env}" | tail -1 \
            | sed -E 's/^[[:space:]]*LOG__DIR[[:space:]]*=//; s/^[[:space:]]*//; s/[[:space:]]*$//; s/^"//; s/"$//')
        [[ -n "${_parsed}" ]] && APP_LOG_DIR="${_parsed}"
    fi
done
# 相对路径基于项目根（与 app_logging.py 解析规则一致）
if [[ "${APP_LOG_DIR}" != /* ]]; then
    APP_LOG_DIR="${SCRIPT_DIR}/${APP_LOG_DIR}"
fi

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

# 进程存活校验：除 kill -0 外，Linux 下再比对 /proc cmdline，防止 PID 复用误判
is_running() {
    local pid="${1:-}"
    [[ "${pid}" =~ ^[0-9]+$ ]] || return 1
    kill -0 "${pid}" 2>/dev/null || return 1
    if [[ -r "/proc/${pid}/cmdline" ]]; then
        tr '\0' ' ' < "/proc/${pid}/cmdline" | grep -q "main:app" || return 1
    fi
    return 0
}

# 输出运行中的 PID；未运行则输出空（并清理残留 PID 文件）
current_pid() {
    local pid=""
    if [[ -f "${PID_FILE}" ]]; then
        pid="$(tr -d '[:space:]' < "${PID_FILE}")"
    fi
    if is_running "${pid}"; then
        echo "${pid}"
    else
        rm -f "${PID_FILE}"
    fi
}

start() {
    local pid
    pid="$(current_pid)"
    if [[ -n "${pid}" ]]; then
        echo "[INFO] 服务已运行 PID=${pid}"
        return 0
    fi

    echo "[INFO] 启动 ${APP_NAME} (${HOST}:${PORT}, workers=${WORKERS})"

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

    pid=$!
    echo "${pid}" > "${PID_FILE}"

    # 健康检查：进程秒挂立即失败；最多等待 10s 端口就绪
    local probe_host="${HOST}" i
    [[ "${probe_host}" == "0.0.0.0" || "${probe_host}" == "::" ]] && probe_host="127.0.0.1"
    for i in {1..10}; do
        if ! kill -0 "${pid}" 2>/dev/null; then
            echo "[ERROR] 启动失败，进程已退出，最近日志："
            tail -n 20 "${LOG_FILE}" 2>/dev/null || true
            rm -f "${PID_FILE}"
            exit 1
        fi
        if (exec 3<>"/dev/tcp/${probe_host}/${PORT}") 2>/dev/null; then
            echo "[SUCCESS] 启动成功 PID=${pid}"
            echo "[INFO] 日志文件(gunicorn): ${LOG_FILE}"
            # info.log / error.log 由 logging_prod.ini 的 FileHandler 写入，实际目录见 APP_LOG_DIR（解析自 .env/.env.prod 的 LOG__DIR）
            echo "[INFO] 日志文件(logging): ${APP_LOG_DIR}/info.log, ${APP_LOG_DIR}/error.log"
            return 0
        fi
        sleep 1
    done

    echo "[WARN] 进程存活但 10s 内端口未就绪，请检查日志: ${LOG_FILE}"
    echo "[INFO] PID=${pid}"
}

stop() {
    local pid
    pid="$(current_pid)"
    if [[ -z "${pid}" ]]; then
        echo "[INFO] 服务未运行"
        return 0
    fi

    echo "[INFO] 停止服务 PID=${pid}"

    kill -TERM "${pid}" 2>/dev/null || true

    local i
    for i in {1..30}; do
        if ! kill -0 "${pid}" 2>/dev/null; then
            rm -f "${PID_FILE}"
            echo "[SUCCESS] 已停止"
            return 0
        fi
        sleep 1
    done

    echo "[WARN] 30s 内未退出，强制停止"

    kill -9 "${pid}" 2>/dev/null || true

    rm -f "${PID_FILE}"
}

status() {
    local pid
    pid="$(current_pid)"
    if [[ -n "${pid}" ]]; then
        echo "[RUNNING] PID=${pid}"
        ps -fp "${pid}" || true
        return 0
    fi
    echo "[STOPPED]"
    return 3
}

logs() {
    tail -n "${TAIL_LINES}" -f "${LOG_FILE}"
}

restart() {
    stop
    sleep 2
    start
}

usage() {
    echo "用法:"
    echo "  $0 start      启动服务"
    echo "  $0 stop       停止服务"
    echo "  $0 restart    重启服务（未运行时等同 start）"
    echo "  $0 status     查看状态（运行中退出码 0，未运行 3）"
    echo "  $0 logs       跟踪日志（TAIL_LINES 控制初始行数，默认 100）"
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
    -h|--help|help)
        usage
        ;;
    *)
        usage
        exit 1
        ;;
esac
