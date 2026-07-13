#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import io
import logging
import logging.config
from pathlib import Path
from core.config import settings

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

_ENV_INI_MAP = {
    "dev": "logging_dev.ini",
    "test": "logging_dev.ini",
    "prod": "logging_prod.ini",
}


def setup_logging():
    # Windows 控制台默认编码非 UTF-8，重新配置以支持中文输出
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    env = settings.ENVIR.lower()
    ini_name = _ENV_INI_MAP.get(env, "logging_dev.ini")
    config_path = _PROJECT_ROOT / "config" / ini_name

    # 日志目录：优先使用 settings.LOG.DIR，相对路径基于项目根目录解析
    log_dir = Path(settings.LOG.DIR)
    if not log_dir.is_absolute():
        log_dir = _PROJECT_ROOT / log_dir
    log_dir.mkdir(parents=True, exist_ok=True)

    try:
        logging.config.fileConfig(
            str(config_path),
            disable_existing_loggers=False,
            encoding="utf8",
            defaults={
                "env": env,
                "log_dir": str(log_dir),
            },
        )
        # 启动时收集各文件 handler 的实际落盘路径（baseFilename），
        # 直接读 handler 而非硬编码文件名，ini 改了这里自动跟着对
        file_paths = []
        for handler in logging.getLogger().handlers:
            base = getattr(handler, "baseFilename", None)
            if base and base not in file_paths:
                file_paths.append(base)
        files_text = (
            "\n".join(f"  - {p}" for p in file_paths)
            if file_paths
            else "  (无文件 handler，仅控制台输出)"
        )
        # print 保证 dev/prod 控制台均可见（prod 控制台 handler 为 WARNING，INFO 不会显示）；
        # 同时 logging.info 写入文件留档
        print(
            f"[OK] 日志系统初始化完成 | 环境: {env} | 日志目录: {log_dir}\n"
            f"日志文件:\n{files_text}"
        )
        logging.info(f"日志系统初始化完成，当前环境: {env}, 日志目录: {log_dir}")
    except Exception as e:
        logging.basicConfig(level=logging.DEBUG if env == "dev" else logging.INFO)
        logging.error(f"日志配置加载失败: {str(e)}，已启用基础配置")
