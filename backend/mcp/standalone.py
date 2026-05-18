#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP 独立进程管理
支持将 MCP 服务器作为独立子进程启动/停止/查询状态
"""
import json
import logging
import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx

from core.config import settings

logger = logging.getLogger(__name__)


def _meta_file_path() -> Path:
    return Path(settings.MCP.PROCESS_META_FILE)


def _read_meta() -> dict | None:
    p = _meta_file_path()
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def _write_meta(data: dict) -> None:
    p = _meta_file_path()
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _remove_meta() -> None:
    p = _meta_file_path()
    if p.exists():
        p.unlink()


class StandaloneMCPManager:
    @staticmethod
    def start() -> dict:
        meta = _read_meta()
        if meta and StandaloneMCPManager._is_process_alive(meta.get("pid")):
            return {"status": "already_running", "pid": meta["pid"]}

        host = settings.MCP.HOST
        port = settings.MCP.PORT

        # 使用 uvicorn 启动独立 MCP 服务器入口
        cmd = [
            sys.executable, "-m", "uvicorn",
            "mcp.server_entry:app",
            "--host", host,
            "--port", str(port),
        ]

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(Path(__file__).resolve().parent.parent),
        )

        meta = {
            "pid": proc.pid,
            "host": host,
            "port": port,
            "started_at": datetime.now().isoformat(),
            "command": " ".join(cmd),
        }
        _write_meta(meta)

        # 等待健康检查
        for _ in range(10):
            time.sleep(0.5)
            if StandaloneMCPManager.health_check():
                logger.info(f"MCP 独立服务已启动，PID={proc.pid}, {host}:{port}")
                return {"status": "started", "pid": proc.pid, "host": host, "port": port}

        logger.warning(f"MCP 独立服务启动超时，PID={proc.pid}")
        return {"status": "starting", "pid": proc.pid, "host": host, "port": port}

    @staticmethod
    def stop() -> dict:
        meta = _read_meta()
        if not meta:
            return {"status": "not_running"}

        pid = meta.get("pid")
        if not pid or not StandaloneMCPManager._is_process_alive(pid):
            _remove_meta()
            return {"status": "not_running"}

        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass

        # 等待进程退出
        for _ in range(10):
            time.sleep(0.3)
            if not StandaloneMCPManager._is_process_alive(pid):
                break

        if StandaloneMCPManager._is_process_alive(pid):
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

        _remove_meta()
        logger.info(f"MCP 独立服务已停止，PID={pid}")
        return {"status": "stopped", "pid": pid}

    @staticmethod
    def status() -> dict:
        meta = _read_meta()
        if not meta:
            return {
                "running": False,
                "status": "stopped",
                "pid": None,
                "host": settings.MCP.HOST,
                "port": settings.MCP.PORT,
                "started_at": None,
            }

        pid = meta.get("pid")
        alive = StandaloneMCPManager._is_process_alive(pid)
        healthy = StandaloneMCPManager.health_check() if alive else False

        return {
            "running": alive and healthy,
            "status": "running" if alive and healthy else ("starting" if alive else "stopped"),
            "pid": pid if alive else None,
            "host": meta.get("host", settings.MCP.HOST),
            "port": meta.get("port", settings.MCP.PORT),
            "started_at": meta.get("started_at"),
        }

    @staticmethod
    def health_check() -> bool:
        try:
            resp = httpx.get(
                f"http://{settings.MCP.HOST}:{settings.MCP.PORT}/health",
                timeout=3,
            )
            return resp.status_code == 200
        except Exception:
            return False

    @staticmethod
    def _is_process_alive(pid: int | None) -> bool:
        if not pid:
            return False
        try:
            os.kill(pid, 0)
            return True
        except (ProcessLookupError, PermissionError, OSError):
            return False
