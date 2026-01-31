#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from pathlib import Path
from core.config import settings
def setup_logging():
    # 读取环境变量，默认开发环境
    env = settings.ENVIR.lower()
    config_path = settings.LOG.INI
    log_dir = Path(settings.LOG.DIR)
    log_dir.mkdir(parents=True, exist_ok=True)  # 自动创建目录（开发环境友好）
    # 加载对应环境的配置
    try:
        logging.config.fileConfig(
            config_path,
            disable_existing_loggers=False,  # 兼容已存在的日志器
            encoding="utf8",
            defaults={
                "env": env,
                "log_dir": str(log_dir),
            },  # 可在配置文件中通过 %(env)s 引用环境变量
        )
        logging.info(f"日志系统初始化完成，当前环境: {env}")
    except Exception as e:
        # 配置加载失败时降级为基础日志
        logging.basicConfig(level=logging.DEBUG if env == "dev" else logging.INFO)
        logging.error(f"日志配置加载失败: {str(e)}，已启用基础配置")