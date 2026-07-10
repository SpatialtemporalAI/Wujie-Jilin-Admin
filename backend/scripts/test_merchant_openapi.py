#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
商户开放 API (OpenAPI v1) 测试脚本

用途：
- 作为第三方商户接入方，测试 /openapi/v1 下全部接口的连通性与签名正确性。
- 演示 HMAC-SHA256 签名生成逻辑，与 backend/docs/merchant-openapi.md 一致。

运行方式：
    cd backend
    python scripts/test_merchant_openapi.py

环境变量（也可使用命令行参数覆盖）：
    MERCHANT_OPENAPI_BASE_URL  服务前缀，默认 http://127.0.0.1:8000
    MERCHANT_API_KEY           商户 api_key
    MERCHANT_API_SECRET        商户 api_secret
    MERCHANT_ROBOT_SN          用于测试的机器人序列号

接口独立控制：
- 未指定任何 --test-* 参数时，默认运行全部接口。
- 指定任意 --test-* 参数后，仅运行被指定的接口。
- 动作类接口（导航/任务控制/语音）默认 dry-run，加 --send-actions 才会真实发送。

示例：
    # 只测试场景、点位、任务三个查询接口
    python scripts/test_merchant_openapi.py --api-key xxx --api-secret xxx --test-scenes --test-points --test-tasks

    # 只测试单点导航，并真实发送
    python scripts/test_merchant_openapi.py --api-key xxx --api-secret xxx --robot-sn R001 --test-goto-point --send-actions

说明：
- 本脚本仅依赖 Python 标准库，无需额外安装 requests/httpx。
- 查询类接口永远真实发送；动作类接口由 --send-actions 统一控制是否真实下发。
- 首次运行建议先确认 scenes/points/tasks 能返回数据，再视情况开启动作类测试。
"""

import argparse
import hashlib
import hmac
import json
import os
import time
import uuid
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


# ---------------------------------------------------------------------------
# 签名与请求
# ---------------------------------------------------------------------------


def sign_request(
    api_secret: str,
    method: str,
    path: str,
    timestamp: str,
    nonce: str,
    body_bytes: bytes,
) -> str:
    """
    计算 HMAC-SHA256 签名。

    待签名串格式：
        METHOD\nPATH\nTIMESTAMP\nNONCE\nBODY_SHA256_HEX
    """
    body_hash = hashlib.sha256(body_bytes).hexdigest()
    string_to_sign = f"{method.upper()}\n{path}\n{timestamp}\n{nonce}\n{body_hash}"
    return hmac.new(
        api_secret.encode("utf-8"),
        string_to_sign.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def openapi_call(
    base_url: str,
    api_key: str,
    api_secret: str,
    path: str,
    payload: Optional[dict[str, Any]] = None,
    timeout: int = 10,
) -> dict[str, Any]:
    """
    调用商户开放 API，自动完成 HMAC 签名并返回解析后的 JSON。

    Args:
        base_url: 平台地址，如 http://127.0.0.1:8000
        api_key: 商户 api_key
        api_secret: 商户 api_secret
        path: 接口路径，如 /openapi/v1/scenes
        payload: 请求体字典，None 时发送 {}
        timeout: 请求超时秒数

    Returns:
        服务端返回的 JSON 反序列化结果
    """
    payload = payload or {}
    body_bytes = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    url = base_url.rstrip("/") + path
    signing_path = urlparse(url).path

    timestamp = str(int(time.time()))
    nonce = uuid.uuid4().hex
    signature = sign_request(api_secret, "POST", signing_path, timestamp, nonce, body_bytes)

    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": api_key,
        "X-Timestamp": timestamp,
        "X-Nonce": nonce,
        "X-Signature": signature,
    }

    req = Request(url, data=body_bytes, headers=headers, method="POST")

    try:
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {"error": True, "status": exc.code, "body": body}
    except URLError as exc:
        return {"error": True, "status": None, "msg": f"网络错误: {exc.reason}"}
    except TimeoutError:
        return {"error": True, "status": None, "msg": "请求超时"}


# ---------------------------------------------------------------------------
# 测试用例
# ---------------------------------------------------------------------------


class MerchantOpenApiTester:
    def __init__(self, base_url: str, api_key: str, api_secret: str, robot_sn: str):
        self.base_url = base_url
        self.api_key = api_key
        self.api_secret = api_secret
        self.robot_sn = robot_sn
        self._last_scene_id: Optional[int] = None
        self._last_point_id: Optional[int] = None
        self._last_task_id: Optional[int] = None

    def _call(self, path: str, payload: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        url = self.base_url.rstrip("/") + path
        print(f"\n[REQUEST] POST {url}")
        print(f"[PAYLOAD] {json.dumps(payload or {}, ensure_ascii=False)}")
        resp = openapi_call(
            self.base_url,
            self.api_key,
            self.api_secret,
            path,
            payload,
        )
        print(f"[RESPONSE] {json.dumps(resp, ensure_ascii=False, indent=2)}")
        return resp

    def _ok(self, resp: dict[str, Any]) -> bool:
        return resp.get("code") == 200 and resp.get("data", {}).get("success") is True

    def test_scenes(self) -> None:
        """测试 /openapi/v1/scenes，获取商户可访问场景。"""
        resp = self._call("/openapi/v1/scenes", {})
        if self._ok(resp):
            scenes = resp.get("data", {}).get("data", {}).get("scenes", [])
            if scenes:
                self._last_scene_id = scenes[0]["id"]
                print(f"[OK] 选中测试场景 map_id={self._last_scene_id}")
            else:
                print("[WARN] 场景列表为空，后续 points 测试将跳过")
        else:
            print("[FAIL] 场景列表获取失败")

    def test_points(self) -> None:
        """测试 /openapi/v1/points，获取首个场景下的点位。"""
        if self._last_scene_id is None:
            print("[SKIP] 无可用场景，跳过点位列表测试")
            return

        resp = self._call("/openapi/v1/points", {"map_id": self._last_scene_id})
        if self._ok(resp):
            points = resp.get("data", {}).get("data", {}).get("points", [])
            if points:
                self._last_point_id = points[0]["id"]
                print(f"[OK] 选中测试点位 point_id={self._last_point_id}")
            else:
                print("[WARN] 点位列表为空，后续 goto_point/navigate_route 将跳过")
        else:
            print("[FAIL] 点位列表获取失败")

    def test_tasks(self) -> None:
        """测试 /openapi/v1/tasks，获取关联到商户机器人的任务。"""
        payload = {"robot_sn": self.robot_sn} if self.robot_sn else {}
        resp = self._call("/openapi/v1/tasks", payload)
        if self._ok(resp):
            tasks = resp.get("data", {}).get("data", {}).get("tasks", [])
            if tasks:
                self._last_task_id = tasks[0]["id"]
                print(f"[OK] 选中测试任务 task_id={self._last_task_id}")
            else:
                print("[WARN] 任务列表为空，后续 execute_task 将跳过")
        else:
            print("[FAIL] 任务列表获取失败")

    def test_goto_point(self, dry_run: bool = True) -> None:
        """测试 /openapi/v1/goto_point。dry_run=True 时仅打印不发送。"""
        if not self.robot_sn or self._last_point_id is None:
            print("[SKIP] 缺少 robot_sn 或可用点位，跳过单点导航测试")
            return
        payload = {"robot_sn": self.robot_sn, "point_id": self._last_point_id}
        if dry_run:
            print(f"\n[DRY-RUN] POST /openapi/v1/goto_point 将发送: {json.dumps(payload, ensure_ascii=False)}")
            return
        self._call("/openapi/v1/goto_point", payload)

    def test_navigate_route(self, dry_run: bool = True) -> None:
        """测试 /openapi/v1/navigate_route。dry_run=True 时仅打印不发送。"""
        if not self.robot_sn or self._last_point_id is None:
            print("[SKIP] 缺少 robot_sn 或可用点位，跳过多点导航测试")
            return
        payload = {"robot_sn": self.robot_sn, "point_ids": [self._last_point_id]}
        if dry_run:
            print(f"\n[DRY-RUN] POST /openapi/v1/navigate_route 将发送: {json.dumps(payload, ensure_ascii=False)}")
            return
        self._call("/openapi/v1/navigate_route", payload)

    def test_execute_task(self, dry_run: bool = True) -> None:
        """测试 /openapi/v1/execute_task。dry_run=True 时仅打印不发送。"""
        if not self.robot_sn or self._last_task_id is None:
            print("[SKIP] 缺少 robot_sn 或可用任务，跳过执行任务测试")
            return
        payload = {"robot_sn": self.robot_sn, "task_id": self._last_task_id}
        if dry_run:
            print(f"\n[DRY-RUN] POST /openapi/v1/execute_task 将发送: {json.dumps(payload, ensure_ascii=False)}")
            return
        self._call("/openapi/v1/execute_task", payload)

    def test_pause_task(self, dry_run: bool = True) -> None:
        """测试 /openapi/v1/pause_task。dry_run=True 时仅打印不发送。"""
        if not self.robot_sn:
            print("[SKIP] 缺少 robot_sn，跳过暂停任务测试")
            return
        payload = {"robot_sn": self.robot_sn}
        if dry_run:
            print(f"\n[DRY-RUN] POST /openapi/v1/pause_task 将发送: {json.dumps(payload, ensure_ascii=False)}")
            return
        self._call("/openapi/v1/pause_task", payload)

    def test_resume_task(self, dry_run: bool = True) -> None:
        """测试 /openapi/v1/resume_task。dry_run=True 时仅打印不发送。"""
        if not self.robot_sn:
            print("[SKIP] 缺少 robot_sn，跳过恢复任务测试")
            return
        payload = {"robot_sn": self.robot_sn}
        if dry_run:
            print(f"\n[DRY-RUN] POST /openapi/v1/resume_task 将发送: {json.dumps(payload, ensure_ascii=False)}")
            return
        self._call("/openapi/v1/resume_task", payload)

    def test_stop_task(self, dry_run: bool = True) -> None:
        """测试 /openapi/v1/stop_task。dry_run=True 时仅打印不发送。"""
        if not self.robot_sn:
            print("[SKIP] 缺少 robot_sn，跳过停止任务测试")
            return
        payload = {"robot_sn": self.robot_sn}
        if dry_run:
            print(f"\n[DRY-RUN] POST /openapi/v1/stop_task 将发送: {json.dumps(payload, ensure_ascii=False)}")
            return
        self._call("/openapi/v1/stop_task", payload)

    def test_speak(self, dry_run: bool = True) -> None:
        """测试 /openapi/v1/speak。dry_run=True 时仅打印不发送。"""
        if not self.robot_sn:
            print("[SKIP] 缺少 robot_sn，跳过语音播报测试")
            return
        payload = {
            "robot_sn": self.robot_sn,
            "text": "商户开放 API 测试播报",
            "tts_params": {"voice": "female", "speed": 1.0, "volume": 80},
        }
        if dry_run:
            print(f"\n[DRY-RUN] POST /openapi/v1/speak 将发送: {json.dumps(payload, ensure_ascii=False)}")
            return
        self._call("/openapi/v1/speak", payload)

    def test_robots(self) -> None:
        """测试 /openapi/v1/robots，获取当前商户关联的机器人列表。"""
        self._call("/openapi/v1/robots", {})

    # 接口名 -> 测试方法（顺序即执行顺序）
    TEST_CASES: dict[str, tuple[str, callable]] = {
        "robots": ("获取机器人列表", lambda self, dry: self.test_robots()),
        "scenes": ("获取场景列表", lambda self, dry: self.test_scenes()),
        "points": ("获取点位列表", lambda self, dry: self.test_points()),
        "tasks": ("获取任务列表", lambda self, dry: self.test_tasks()),
        "goto_point": ("单点导航", lambda self, dry: self.test_goto_point(dry_run=dry)),
        "navigate_route": ("多点导航", lambda self, dry: self.test_navigate_route(dry_run=dry)),
        "execute_task": ("执行任务", lambda self, dry: self.test_execute_task(dry_run=dry)),
        "pause_task": ("暂停任务", lambda self, dry: self.test_pause_task(dry_run=dry)),
        "resume_task": ("恢复任务", lambda self, dry: self.test_resume_task(dry_run=dry)),
        "stop_task": ("停止任务", lambda self, dry: self.test_stop_task(dry_run=dry)),
        "speak": ("语音播报", lambda self, dry: self.test_speak(dry_run=dry)),
    }

    def run(
        self,
        enabled_tests: Optional[set[str]] = None,
        send_actions: bool = False,
    ) -> None:
        """执行指定测试用例。

        Args:
            enabled_tests: 需要运行的接口名集合；None 表示运行全部。
            send_actions: 是否真实发送动作类接口（导航/任务控制/语音）。
        """
        enabled_tests = enabled_tests or set(self.TEST_CASES.keys())

        print("=" * 60)
        print("商户开放 API 测试开始")
        print(f"Base URL: {self.base_url}")
        print(f"API Key: {self.api_key[:8]}{'*' * 8 if self.api_key else '(未配置)'}")
        print(f"Robot SN: {self.robot_sn or '(未配置)'}")
        print(f"本次测试接口: {', '.join(enabled_tests)}")
        print("=" * 60)

        for name, (label, method) in self.TEST_CASES.items():
            if name not in enabled_tests:
                continue
            print(f"\n[TEST] {label} ({name})")
            # 查询类接口永远真实发送；动作类接口由 send_actions 控制
            is_action = name in {"goto_point", "navigate_route", "execute_task", "pause_task", "resume_task", "stop_task", "speak"}
            dry_run = is_action and not send_actions
            method(self, dry_run)

        print("\n" + "=" * 60)
        print("测试结束")
        print("=" * 60)


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="商户开放 API 测试脚本")
    parser.add_argument(
        "--send-actions",
        action="store_true",
        help="默认动作类接口（导航/任务控制/语音）仅 dry-run，加此参数才会真实发送",
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("MERCHANT_OPENAPI_BASE_URL", "http://127.0.0.1:8000"),
        help="服务前缀，默认 http://127.0.0.1:8000",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("MERCHANT_API_KEY", ""),
        help="商户 API Key",
    )
    parser.add_argument(
        "--api-secret",
        default=os.environ.get("MERCHANT_API_SECRET", ""),
        help="商户 API Secret",
    )
    parser.add_argument(
        "--robot-sn",
        default=os.environ.get("MERCHANT_ROBOT_SN", ""),
        help="用于测试的机器人序列号",
    )

    # 每个接口独立开关；未指定任何开关时默认运行全部
    test_group = parser.add_argument_group("接口独立控制（未指定则运行全部）")
    test_group.add_argument("--test-robots", action="store_true", help="测试 /openapi/v1/robots")
    test_group.add_argument("--test-scenes", action="store_true", help="测试 /openapi/v1/scenes")
    test_group.add_argument("--test-points", action="store_true", help="测试 /openapi/v1/points")
    test_group.add_argument("--test-tasks", action="store_true", help="测试 /openapi/v1/tasks")
    test_group.add_argument("--test-goto-point", action="store_true", help="测试 /openapi/v1/goto_point")
    test_group.add_argument("--test-navigate-route", action="store_true", help="测试 /openapi/v1/navigate_route")
    test_group.add_argument("--test-execute-task", action="store_true", help="测试 /openapi/v1/execute_task")
    test_group.add_argument("--test-pause-task", action="store_true", help="测试 /openapi/v1/pause_task")
    test_group.add_argument("--test-resume-task", action="store_true", help="测试 /openapi/v1/resume_task")
    test_group.add_argument("--test-stop-task", action="store_true", help="测试 /openapi/v1/stop_task")
    test_group.add_argument("--test-speak", action="store_true", help="测试 /openapi/v1/speak")

    args = parser.parse_args()

    if not args.api_key or not args.api_secret:
        print(
            "[ERROR] 请配置 MERCHANT_API_KEY 和 MERCHANT_API_SECRET 环境变量，"
            "或使用 --api-key / --api-secret 参数。"
        )
        raise SystemExit(1)

    # 收集用户显式指定的接口
    explicit_tests = {
        name
        for name in MerchantOpenApiTester.TEST_CASES.keys()
        if getattr(args, f"test_{name.replace('-', '_')}", False)
    }
    enabled_tests = explicit_tests if explicit_tests else None

    tester = MerchantOpenApiTester(
        base_url=args.base_url,
        api_key=args.api_key,
        api_secret=args.api_secret,
        robot_sn=args.robot_sn,
    )
    tester.run(enabled_tests=enabled_tests, send_actions=args.send_actions)


if __name__ == "__main__":
    main()
