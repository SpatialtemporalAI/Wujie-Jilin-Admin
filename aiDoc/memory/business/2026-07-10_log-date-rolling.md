---
name: 2026-07-10_log-date-rolling
description: 本地 .log 日志按日期滚动需求，最终通过 logrotate + copytruncate 实现 Gunicorn 日志按天滚动
metadata:
  type: business
---

# 2026-07-10 本地 .log 日志按日期滚动

## 需求

用户要求本地 `.log` 日志实现按日期划分的滚动日志。后续用户反馈在服务器上没有看到滚动日志，要求排查。

## 排查结论

- Python 应用内部日志已经通过 `TimedRotatingFileHandler` 按天滚动（`backend/config/logging_prod.ini`）。
- 用户通过 `backend/start_prod.sh` 启动服务，该脚本把 Gunicorn 的 stdout/stderr 整体重定向到单个文件 `backend/logs/smilex-cloud.log`，**该文件没有滚动机制**。
- `deploy/smilex-cloud.service` 中 Gunicorn 直接写入的 `access.log` / `error.log` 同样不会自动滚动。

## 实施方案

采用 **logrotate + `copytruncate` + `dateext`** 方案：

- 保持 `start_prod.sh` 当前写入固定文件 `backend/logs/smilex-cloud.log` 的行为不变。
- 新增 `deploy/logrotate/smilex-cloud` 配置，由 `deploy/deploy.sh setup` 安装到 `/etc/logrotate.d/smilex-cloud`。
- logrotate 每天把当前日志复制为 `smilex-cloud-YYYY-MM-DD.log` 后清空原文件，服务不中断。
- 同时覆盖 systemd 方式下的 `/var/log/smilex_cloud/access.log` 和 `/var/log/smilex_cloud/error.log`。

## 修改文件

- [deploy/logrotate/smilex-cloud](../../../deploy/logrotate/smilex-cloud) — 新增 logrotate 配置模板
- [deploy/deploy.sh](../../../deploy/deploy.sh) — `cmd_setup()` 中增加 logrotate 配置安装
- [backend/start_prod.sh](../../../backend/start_prod.sh) — 增加注释和未配置 logrotate 时的启动警告

## 部署/验证

1. 确保服务器已安装 `logrotate`。
2. 已部署环境手动复制配置：
   ```bash
   sudo cp deploy/logrotate/smilex-cloud /etc/logrotate.d/smilex-cloud
   sudo chmod 0644 /etc/logrotate.d/smilex-cloud
   ```
3. 调试预览：
   ```bash
   sudo logrotate -d /etc/logrotate.d/smilex-cloud
   ```
4. 强制滚动验证：
   ```bash
   sudo bash -c 'echo "test" >> /opt/smilex-cloud/backend/logs/smilex-cloud.log'
   sudo logrotate -f /etc/logrotate.d/smilex-cloud
   ls -lh /opt/smilex-cloud/backend/logs/
   ```

## 注意事项

- `copytruncate` 在复制和清空之间有极小时间窗口，极端高并发下可能丢失少量日志。
- `dateyesterday` 需要 logrotate >= 3.10.0。
- 首次滚动时，原日志文件可能已包含多天历史内容，归档文件名不一定精确反映内容日期，第二次滚动后恢复正常。
- Python 应用内部 `info.log` / `error.log` 的滚动行为见下方 2026-07-30 修复（已由 `TimedRotatingFileHandler` 改为 `FileHandler` + logrotate）。

## 2026-07-30 修复：多 worker 下 info.log 不滚动

### 现象

`./start_prod.sh` 启动后，`/var/log/smilex_cloud/info.log` 持续增大、从不生成 `info.log.YYYY-MM-DD` 归档；目录有写权限，排除权限问题。

### 根因

`logging_prod.ini` 原用 `TimedRotatingFileHandler`，但 gunicorn `-w 4` 多 worker 各自持有 handler 实例，凌晨并发 `doRollover` 时互相 `os.rename` / 覆盖归档，滚动失效（Python `logging` 非多进程安全）。原 logrotate 配置只覆盖 `smilex-cloud.log` / `access.log` / `error.log`，**未覆盖 `info.log`**，无外部兜底。

### 修复（统一交给 logrotate，与 smilex-cloud.log 一致）

- [backend/config/logging_prod.ini](../../../backend/config/logging_prod.ini)：`infoFileHandler` / `errorFileHandler` 由 `TimedRotatingFileHandler` 改为普通 `FileHandler`（追加模式），不再自行滚动。
- [deploy/logrotate/smilex-cloud](../../../deploy/logrotate/smilex-cloud)：加入 `/var/log/smilex_cloud/info.log`，沿用 `copytruncate + dateext`。多 worker 的 fd 指向同一 inode，`copytruncate` 在 inode 层清空，全部 worker 继续追加写，多进程可靠。
- [backend/start_prod.sh](../../../backend/start_prod.sh)：新增 `APP_LOG_DIR`，从 `.env` / `.env.prod` 解析 `LOG__DIR`（后者覆盖），启动提示显示真实日志目录而非硬编码 `backend/logs`。
- [deploy/deploy.sh](../../../deploy/deploy.sh)：`cmd_setup` 安装 logrotate 后校验 `.env.prod` 的 `LOG__DIR` 与部署 `LOG_DIR` 一致，不一致则 warn（否则 logrotate 因 `missingok` 静默跳过）。

### 验证

```bash
sudo logrotate -f /etc/logrotate.d/smilex-cloud
ls -lh /var/log/smilex_cloud/   # 应出现 info.log-YYYY-MM-DD
```

### 注意

- `logging_dev.ini` 保留 `TimedRotatingFileHandler` 不变：dev 单进程直接运行，handler 工作正常，且 dev 无 logrotate 外部滚动。
- 遗留隐患（未本次处理）：systemd 方式下 gunicorn `--error-logfile /var/log/smilex_cloud/error.log` 与 Python `errorFileHandler` 同名共用，两类日志格式混写；如需分离可将 Python 端改名 `app-error.log` / `app-info.log`。
