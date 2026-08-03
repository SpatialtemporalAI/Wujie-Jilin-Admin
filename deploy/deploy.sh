#!/usr/bin/env bash
# Wujie-Jilin-Admin Cloud Backend 部署脚本
# 用法: ./deploy.sh <command> [options]
#
# 命令:
#   setup              首次部署：安装依赖、初始化数据库、安装 systemd 服务
#   deploy             日常部署：拉取代码、更新依赖、迁移、重启
#   rollback [hash]    回滚到指定 commit（默认上一个 commit）
#   logs               查看服务日志 (journalctl -f)
#   status             查看服务状态

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ---- 配置（直接写在脚本里，按需修改；原 deploy.env 已不再读取） ----
# 应用
APP_NAME="smilex-cloud"
APP_USER="smilex"
APP_GROUP="smilex"

# 项目根目录（git 仓库根，含 backend/frontend/deploy；submodule: backend/database、backend/grpc）
PROJECT_DIR="/opt/smilex-cloud"
BACKEND_DIR="${PROJECT_DIR}/backend"
VENV_DIR="${BACKEND_DIR}/.venv"
DATABASE_DIR="${BACKEND_DIR}/database"   # alembic 子模块，alembic.ini 位于此目录

# Gunicorn
GUNICORN_WORKERS=4
GUNICORN_PORT=8000
GUNICORN_BIND="0.0.0.0:${GUNICORN_PORT}"
GUNICORN_TIMEOUT=120
GUNICORN_MAX_REQUESTS=5000
GUNICORN_MAX_REQUESTS_JITTER=500

# 日志（须与 backend/.env.prod 的 LOG__DIR 一致，否则 logrotate 滚动不到应用日志）
LOG_DIR="/var/log/smilex_cloud"
ACCESS_LOG="${LOG_DIR}/access.log"
ERROR_LOG="${LOG_DIR}/error.log"

# 应用环境配置（Python 应用读取）
ENV_FILE="${BACKEND_DIR}/.env.prod"

# Git
GIT_BRANCH="main"

# 健康检查
HEALTH_CHECK_URL="http://127.0.0.1:${GUNICORN_PORT}/openapi.json"
HEALTH_CHECK_TIMEOUT=10

# ---- 颜色输出 ----
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# ---- 前置检查 ----
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "此命令需要 root 权限，请使用 sudo 运行"
        exit 1
    fi
}

ensure_user() {
    if ! id -u "${APP_USER}" &>/dev/null; then
        info "创建用户: ${APP_USER}"
        useradd -r -s /bin/false -d "${PROJECT_DIR}" "${APP_USER}"
    fi
}

ensure_dirs() {
    info "创建目录结构"
    mkdir -p "${LOG_DIR}"
    mkdir -p "${BACKEND_DIR}/uploads"
    chown -R "${APP_USER}:${APP_GROUP}" "${LOG_DIR}"
    chown -R "${APP_USER}:${APP_GROUP}" "${BACKEND_DIR}/uploads"
}

check_prerequisites() {
    local missing=()

    if ! command -v python3 &>/dev/null; then
        missing+=("python3")
    else
        local py_ver
        py_ver=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        if [[ $(echo "$py_ver < 3.11" | bc -l 2>/dev/null || echo 1) -eq 1 ]]; then
            # fallback comparison
            local major minor
            IFS='.' read -r major minor <<< "$py_ver"
            if [[ "$major" -lt 3 ]] || [[ "$major" -eq 3 && "$minor" -lt 11 ]]; then
                error "Python 版本过低: ${py_ver}，需要 >= 3.11"
                missing+=("python3>=3.11")
            fi
        fi
    fi

    if ! command -v uv &>/dev/null; then
        missing+=("uv (pip install uv 或 curl -LsSf https://astral.sh/uv/install.sh | sh)")
    fi

    if ! command -v git &>/dev/null; then
        missing+=("git")
    fi

    if [[ ${#missing[@]} -gt 0 ]]; then
        error "缺少以下依赖:"
        for pkg in "${missing[@]}"; do
            echo "  - ${pkg}"
        done
        exit 1
    fi

    info "系统依赖检查通过"
}

# ---- 子命令实现 ----

cmd_setup() {
    info "========== Wujie-Jilin-Admin Cloud 首次部署 =========="
    check_root
    check_prerequisites
    ensure_user
    ensure_dirs

    # 初始化 submodule（backend/database 迁移、backend/grpc）
    info "初始化 submodule"
    cd "${PROJECT_DIR}"
    git submodule update --init --recursive

    # 安装 Python 依赖
    info "安装 Python 依赖"
    cd "${BACKEND_DIR}"
    uv sync --frozen

    # 检查 .env.prod
    if [[ ! -f "${ENV_FILE}" ]]; then
        warn ".env.prod 不存在，从模板创建"
        cp "${BACKEND_DIR}/.env.prod" "${ENV_FILE}" 2>/dev/null || true
        warn "请编辑 ${ENV_FILE} 配置数据库、Redis 等连接信息后再继续"
        warn "编辑完成后重新运行: sudo ./deploy.sh setup"
        exit 0
    fi
    info "环境配置: ${ENV_FILE}"

    # 数据库迁移（alembic.ini 位于 backend/database 子模块）
    info "运行数据库迁移"
    cd "${DATABASE_DIR}"
    source "${VENV_DIR}/bin/activate"
    alembic upgrade head
    info "数据库迁移完成"

    # 安装 systemd 服务
    info "安装 systemd 服务"
    sed \
        -e "s|/opt/smilex-cloud/backend|${BACKEND_DIR}|g" \
        -e "s|/opt/smilex-cloud/backend/.venv|${VENV_DIR}|g" \
        -e "s|/var/log/smilex_cloud|${LOG_DIR}|g" \
        -e "s|User=smilex|User=${APP_USER}|g" \
        -e "s|Group=smilex|Group=${APP_GROUP}|g" \
        -e "s|-w 4|-w ${GUNICORN_WORKERS}|g" \
        -e "s|-b 0.0.0.0:8000|-b ${GUNICORN_BIND}|g" \
        -e "s|--timeout 120|--timeout ${GUNICORN_TIMEOUT}|g" \
        -e "s|--max-requests 5000|--max-requests ${GUNICORN_MAX_REQUESTS}|g" \
        -e "s|--max-requests-jitter 500|--max-requests-jitter ${GUNICORN_MAX_REQUESTS_JITTER}|g" \
        -e "s|/var/log/smilex_cloud/access.log|${ACCESS_LOG}|g" \
        -e "s|/var/log/smilex_cloud/error.log|${ERROR_LOG}|g" \
        "${SCRIPT_DIR}/smilex-cloud.service" \
        > /etc/systemd/system/"${APP_NAME}.service"

    # 安装 logrotate 配置
    info "安装 logrotate 配置"
    mkdir -p /etc/logrotate.d
    sed \
        -e "s|/opt/smilex-cloud/backend|${BACKEND_DIR}|g" \
        -e "s|/var/log/smilex_cloud|${LOG_DIR}|g" \
        "${SCRIPT_DIR}/logrotate/smilex-cloud" \
        > /etc/logrotate.d/"${APP_NAME}"
    chmod 0644 /etc/logrotate.d/"${APP_NAME}"

    # 校验 Python 应用日志目录（.env.prod 的 LOG__DIR）与 logrotate 目标（LOG_DIR）一致，
    # 否则 logrotate 因 missingok 静默跳过，应用日志不会滚动。
    if [[ -f "${ENV_FILE}" ]]; then
        _py_log_dir=$(grep -iE '^[[:space:]]*LOG__DIR[[:space:]]*=' "${ENV_FILE}" | tail -1 \
            | sed -E 's/^[[:space:]]*LOG__DIR[[:space:]]*=//; s/^[[:space:]]*//; s/[[:space:]]*$//; s/^"//; s/"$//')
        if [[ -n "${_py_log_dir}" && "${_py_log_dir}" != "${LOG_DIR}" ]]; then
            warn "Python 日志目录 LOG__DIR=${_py_log_dir} 与部署 LOG_DIR=${LOG_DIR} 不一致"
            warn "logrotate 将无法滚动应用日志，请编辑 ${ENV_FILE} 将 LOG__DIR 设为 ${LOG_DIR}"
        fi
    fi

    if ! command -v logrotate &>/dev/null; then
        warn "未检测到 logrotate，请手动安装"
        warn "  Debian/Ubuntu: sudo apt-get install logrotate"
        warn "  RHEL/CentOS:   sudo yum install logrotate"
    fi

    systemctl daemon-reload
    systemctl enable "${APP_NAME}"

    info "========== 部署完成 =========="
    info ""
    info "下一步:"
    info "  1. 确认 ${ENV_FILE} 配置正确"
    info "  2. 启动服务: sudo systemctl start ${APP_NAME}"
    info "  3. 检查状态: ./deploy.sh status"
    info "  4. 可选: 配置 Nginx 反向代理 (参考 deploy/nginx.conf)"
}

cmd_deploy() {
    info "========== 开始部署 =========="
    check_prerequisites

    cd "${PROJECT_DIR}"

    # 记录当前 commit
    local before_commit
    before_commit=$(git rev-parse --short HEAD)
    info "当前版本: ${before_commit}"

    # 拉取最新代码（主仓库 + submodule：backend/database、backend/grpc）
    info "拉取最新代码 (分支: ${GIT_BRANCH})"
    git pull origin "${GIT_BRANCH}"
    git submodule update --init --recursive

    local after_commit
    after_commit=$(git rev-parse --short HEAD)

    if [[ "${before_commit}" == "${after_commit}" ]]; then
        info "代码无变化，跳过部署"
        exit 0
    fi

    info "更新版本: ${before_commit} -> ${after_commit}"

    # 更新依赖
    info "更新 Python 依赖"
    cd "${BACKEND_DIR}"
    uv sync --frozen

    # 数据库迁移（alembic.ini 位于 backend/database 子模块）
    info "运行数据库迁移"
    cd "${DATABASE_DIR}"
    source "${VENV_DIR}/bin/activate"
    alembic upgrade head
    info "数据库迁移完成"

    # 重启服务
    info "重启服务"
    sudo systemctl restart "${APP_NAME}"

    # 健康检查
    info "健康检查..."
    sleep 3
    if curl -sf -o /dev/null -m "${HEALTH_CHECK_TIMEOUT}" "${HEALTH_CHECK_URL}"; then
        info "========== 部署成功 =========="
        info "版本: ${after_commit}"
    else
        error "健康检查失败！服务可能未正常启动"
        error "查看日志: ./deploy.sh logs"
        error "回滚命令: ./deploy.sh rollback ${before_commit}"
        exit 1
    fi
}

cmd_rollback() {
    local target="${1:-HEAD~1}"
    info "========== 回滚部署 =========="
    cd "${PROJECT_DIR}"

    info "回滚到: ${target}"
    git log --oneline -1 "${target}"

    git reset --hard "${target}"
    git submodule update --init --recursive

    # 更新依赖
    info "更新 Python 依赖"
    cd "${BACKEND_DIR}"
    uv sync --frozen

    # 数据库迁移（回滚到匹配版本，alembic.ini 位于 backend/database 子模块）
    info "运行数据库迁移"
    cd "${DATABASE_DIR}"
    source "${VENV_DIR}/bin/activate"
    alembic upgrade head

    # 重启服务
    info "重启服务"
    sudo systemctl restart "${APP_NAME}"

    info "========== 回滚完成 =========="
    info "当前版本: $(git rev-parse --short HEAD)"
}

cmd_logs() {
    sudo journalctl -u "${APP_NAME}" -f --no-pager -n 100
}

cmd_status() {
    echo "========== 服务状态 =========="
    sudo systemctl status "${APP_NAME}" --no-pager || true
    echo ""
    echo "========== 最近日志 =========="
    sudo journalctl -u "${APP_NAME}" --no-pager -n 20
    echo ""
    echo "========== 版本信息 =========="
    cd "${PROJECT_DIR}"
    echo "分支: $(git branch --show-current)"
    echo "版本: $(git rev-parse --short HEAD) ($(git log -1 --format='%ci' HEAD))"
}

# ---- 入口 ----

usage() {
    echo "Wujie-Jilin-Admin Cloud Backend 部署脚本"
    echo ""
    echo "用法: $0 <command> [options]"
    echo ""
    echo "命令:"
    echo "  setup              首次部署：安装依赖、初始化数据库、安装 systemd 服务"
    echo "  deploy             日常部署：拉取代码、更新依赖、迁移、重启"
    echo "  rollback [hash]    回滚到指定 commit（默认上一个 commit）"
    echo "  logs               查看服务日志"
    echo "  status             查看服务状态"
}

case "${1:-}" in
    setup)    cmd_setup ;;
    deploy)   cmd_deploy ;;
    rollback) cmd_rollback "${2:-}" ;;
    logs)     cmd_logs ;;
    status)   cmd_status ;;
    -h|--help|help)
        usage
        ;;
    *)
        error "未知命令: ${1:-}"
        usage
        exit 1
        ;;
esac
