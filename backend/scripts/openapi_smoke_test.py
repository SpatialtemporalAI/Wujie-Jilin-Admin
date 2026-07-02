#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OpenAPI 全端点自动巡检脚本

用途：
    连接到正在运行的后端服务，拉取 /openapi.json，登录拿到 token，
    然后对规范里所有「只读 GET」端点逐一发起请求，输出 通过/失败/状态码 报告。

设计原则：
    - 纯标准库实现（urllib + json），无需安装任何依赖
    - 只发 GET 请求，绝不触发写操作，可安全对生产环境做冒烟测试
    - 端点、参数、登录账号全部可通过命令行参数 / 环境变量覆盖

典型用法：
    # 连本地（默认 http://127.0.0.1:8000，admin/admin123）
    python scripts/openapi_smoke_test.py

    # 连指定服务器并自定义账号
    python scripts/openapi_smoke_test.py \
        --base-url http://192.168.5.183:8000 \
        --username admin --password admin123

    # 同时测试带路径/查询参数的端点（用样例值填充）
    python scripts/openapi_smoke_test.py --include-params

    # 只巡检某个 tag（正则匹配，如 admin接口/认证）
    python scripts/openapi_smoke_test.py --tag '认证'

环境变量（命令行参数优先级更高）：
    OPENAPI_BASE_URL     服务地址
    OPENAPI_USERNAME     登录用户名
    OPENAPI_PASSWORD     登录密码
    OPENAPI_LOGIN_PATH   登录端点路径，默认 /admin/auth/login
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------

DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin123"
DEFAULT_LOGIN_PATH = "/admin/auth/login"
DEFAULT_TIMEOUT = 15

# 统一响应结构里的成功业务码（ResponseModel.code）
SUCCESS_BIZ_CODE = 200


# ---------------------------------------------------------------------------
# HTTP 小工具
# ---------------------------------------------------------------------------


def http_request(
    method: str,
    url: str,
    *,
    token: str | None = None,
    json_body: Any = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> tuple[int, dict | list | str, dict]:
    """发起一次 HTTP 请求，返回 (status, parsed_body, headers)。

    body 解析失败时退化为原始文本。urllib 抛出的网络异常会向上冒泡。
    """
    headers: dict[str, str] = {"Accept": "application/json"}
    data: bytes | None = None
    if json_body is not None:
        data = json.dumps(json_body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            status = resp.getcode()
            resp_headers = dict(resp.headers.items())
    except urllib.error.HTTPError as exc:
        # HTTPError 仍然有响应体，按正常流程解析状态码与 body
        raw = exc.read().decode("utf-8", errors="replace")
        status = exc.code
        resp_headers = dict(exc.headers.items()) if exc.headers else {}

    try:
        parsed = json.loads(raw) if raw else None
    except (ValueError, json.JSONDecodeError):
        parsed = raw
    return status, parsed, resp_headers


# ---------------------------------------------------------------------------
# 登录
# ---------------------------------------------------------------------------


def login(base_url: str, login_path: str, username: str, password: str, timeout: int) -> str:
    """登录并返回 access_token。"""
    url = base_url.rstrip("/") + login_path
    status, body, _ = http_request(
        "POST",
        url,
        json_body={"username": username, "password": password},
        timeout=timeout,
    )

    def _fail(reason: str) -> str:
        preview = json.dumps(body, ensure_ascii=False)[:300] if isinstance(body, (dict, list)) else str(body)[:300]
        raise SystemExit(f"[登录失败] {reason}\n  POST {url} -> HTTP {status}\n  body: {preview}")

    if not isinstance(body, dict):
        _fail("响应不是 JSON 对象")
        return ""  # 仅为类型检查，不会执行

    # 统一响应：{ code, msg, data, request_id, err_code }
    biz_code = body.get("code")
    if biz_code != SUCCESS_BIZ_CODE:
        # 滑块验证码、限流等情况
        msg = body.get("msg") or body.get("message") or ""
        _fail(f"业务码 code={biz_code} msg={msg}（若提示需要验证码，请先在 Web 端登录一次清除失败计数）")

    data = body.get("data") or {}
    token = data.get("access_token")
    if not token:
        _fail("响应缺少 data.access_token")
    return token


# ---------------------------------------------------------------------------
# OpenAPI 解析与样例参数
# ---------------------------------------------------------------------------


# 用参数名/位置推断一个尽量「不报 422」的样例值
def sample_value(name: str, schema: dict | None) -> str:
    schema = schema or {}
    low = name.lower()
    py_type = schema.get("type")
    # 枚举优先
    enum = schema.get("enum")
    if enum:
        return str(enum[0])
    if py_type == "boolean":
        return "false"
    if py_type == "integer" or py_type == "number":
        if "page" in low:
            return "1"
        if "size" in low or "limit" in low:
            return "20"
        return "1"
    # 名字启发式
    if low.endswith("id") or low.endswith("_id") or low == "id":
        return "1"
    if "page" in low:
        return "1"
    if "size" in low or "limit" in low:
        return "20"
    if "code" in low or "name" in low:
        return "test"
    return "test"


def collect_get_endpoints(spec: dict, include_params: bool, tag_filter: str | None):
    """从 openapi spec 中收集要测试的 GET 端点。

    返回列表，每项：{path, method, operation, full_path(填充样例后的路径),
    query(样例查询参数 dict), skipped(跳过原因或 None), sampled(是否使用了样例参数)}
    """
    paths = spec.get("paths") or {}
    tag_re = re.compile(tag_filter) if tag_filter else None
    results = []

    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method.lower() != "get":
                continue
            if not isinstance(operation, dict):
                continue

            # tag 过滤
            tags = operation.get("tags") or []
            if tag_re and not any(tag_re.search(t) for t in tags):
                continue

            params = operation.get("parameters") or []
            required_path = []
            optional_path_sample = {}
            required_query = []
            query_sample: dict[str, str] = {}

            for p in params:
                if not isinstance(p, dict):
                    continue
                loc = p.get("in")
                pname = p.get("name", "")
                required = bool(p.get("required"))
                schema = p.get("schema") if isinstance(p.get("schema"), dict) else None
                if loc == "path":
                    optional_path_sample[pname] = sample_value(pname, schema)
                    if required:
                        required_path.append(pname)
                elif loc == "query":
                    if required:
                        required_query.append(pname)
                        query_sample[pname] = sample_value(pname, schema)
                    elif include_params:
                        # 可选参数仅在 --include-params 时填充，避免噪音
                        query_sample[pname] = sample_value(pname, schema)

            has_body = "requestBody" in operation  # GET 一般没有，留作判定

            skipped = None
            sampled = False

            if has_body:
                skipped = "GET 带 requestBody，跳过"
            elif not include_params and (required_path or required_query):
                skipped = (
                    f"需要必填参数 path={required_path} query={required_query}"
                    "（加 --include-params 可用样例值试探）"
                )

            # 填充路径参数
            full_path = path
            if include_params or not required_path:
                for pname, val in optional_path_sample.items():
                    full_path = full_path.replace("{" + pname + "}", urllib.parse.quote(val, safe=""))
                    sampled = True

            results.append(
                {
                    "path": path,
                    "method": method.upper(),
                    "operation": operation,
                    "full_path": full_path,
                    "query": query_sample if (include_params or not required_query) else {},
                    "skipped": skipped,
                    "sampled": sampled,
                    "tags": tags,
                }
            )

    return results


# ---------------------------------------------------------------------------
# 结果分类
# ---------------------------------------------------------------------------

# 分类标签
OK = "OK"
AUTH = "AUTH"
CLIENT = "CLIENT"
SERVER = "SERVER"
NET = "NET_ERR"
SKIP = "SKIP"


def classify(status: int | None, body: Any, exc: Exception | None) -> tuple[str, str]:
    """根据状态码/异常分类，返回 (类别, 简要说明)。"""
    if exc is not None:
        return NET, f"{type(exc).__name__}: {exc}"
    if status is None:
        return NET, "无响应"
    if 200 <= status < 300:
        # 进一步看业务码（统一响应 { code, msg, data }）
        if isinstance(body, dict):
            biz = body.get("code")
            if biz is not None and biz != SUCCESS_BIZ_CODE:
                return CLIENT, f"HTTP {status} 但业务 code={biz} msg={body.get('msg')}"
        return OK, f"HTTP {status}"
    if status in (401, 403):
        return AUTH, f"HTTP {status}"
    if 400 <= status < 500:
        return CLIENT, f"HTTP {status}"
    if status >= 500:
        return SERVER, f"HTTP {status}"
    return CLIENT, f"HTTP {status}"


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="OpenAPI 全端点自动巡检（只读 GET 冒烟测试）",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--base-url", default=os.getenv("OPENAPI_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--username", default=os.getenv("OPENAPI_USERNAME", DEFAULT_USERNAME))
    parser.add_argument("--password", default=os.getenv("OPENAPI_PASSWORD", DEFAULT_PASSWORD))
    parser.add_argument("--login-path", default=os.getenv("OPENAPI_LOGIN_PATH", DEFAULT_LOGIN_PATH))
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="单次请求超时(秒)")
    parser.add_argument(
        "--include-params",
        action="store_true",
        help="对带路径/查询参数的端点用样例值填充后也测试（404/422 属正常）",
    )
    parser.add_argument("--tag", default=None, help="只测 tags 正则匹配的端点")
    parser.add_argument("--no-login", action="store_true", help="跳过登录，以匿名身份巡检公开端点")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    print(f"目标服务: {base_url}")

    # 1. 拉取 openapi.json
    try:
        _, spec_body, _ = http_request("GET", base_url + "/openapi.json", timeout=args.timeout)
    except Exception as exc:
        print(f"[错误] 拉取 /openapi.json 失败: {type(exc).__name__}: {exc}")
        print("       请确认服务已启动且未在生产环境关闭 openapi（SERVICE.OPENAPI_ENABLE_IN_PROD）")
        return 2
    if not isinstance(spec_body, dict) or "paths" not in spec_body:
        print("[错误] /openapi.json 返回内容不是合法的 OpenAPI 文档")
        return 2
    total_paths = len(spec_body.get("paths") or {})
    print(f"已加载 OpenAPI 规范：{spec_body.get('info', {}).get('title', '?')} "
          f"version={spec_body.get('info', {}).get('version', '?')}，共 {total_paths} 个路径")

    # 2. 登录
    token = ""
    if not args.no_login:
        print(f"登录中... ({args.login_path} 用户={args.username})")
        token = login(base_url, args.login_path, args.username, args.password, args.timeout)
        print("登录成功，已获取 access_token")
    else:
        print("已跳过登录（--no-login），仅巡检公开端点")

    # 3. 收集端点
    endpoints = collect_get_endpoints(spec_body, args.include_params, args.tag)
    print(f"发现 GET 端点 {len(endpoints)} 个（tag 过滤={args.tag or '无'}，含参试探={args.include_params}）\n")

    # 4. 逐个请求
    rows = []
    counters = {OK: 0, AUTH: 0, CLIENT: 0, SERVER: 0, NET: 0, SKIP: 0}
    for ep in endpoints:
        if ep["skipped"]:
            counters[SKIP] += 1
            rows.append((ep, SKIP, "-", ep["skipped"]))
            continue

        url = base_url + ep["full_path"]
        if ep["query"]:
            url += "?" + urllib.parse.urlencode(ep["query"])
        try:
            status, body, _ = http_request(
                "GET", url, token=token or None, timeout=args.timeout
            )
            category, note = classify(status, body, None)
        except Exception as exc:  # 网络层异常
            category, note = classify(None, None, exc)

        counters[category] += 1
        tag_str = "/".join(ep["tags"]) if ep["tags"] else "-"
        rows.append((ep, category, tag_str, note))

    # 5. 报告
    print("=" * 100)
    print(f"{'类别':<8} {'TAG':<28} {'方法':<6} {'路径':<48} 说明")
    print("-" * 100)
    for ep, category, tag_str, note in rows:
        flag = " *" if ep["sampled"] else ""
        path_col = ep["full_path"] + flag
        print(f"{category:<8} {tag_str:<28} {ep['method']:<6} {path_col:<48} {note}")
    print("=" * 100)

    # 6. 汇总
    total = len(rows)
    print(
        "汇总: "
        f"共 {total}，OK={counters[OK]}，AUTH={counters[AUTH]}，"
        f"CLIENT={counters[CLIENT]}，SERVER={counters[SERVER]}，"
        f"NET_ERR={counters[NET]}，SKIP={counters[SKIP]}"
    )
    print("说明: OK=2xx成功；AUTH=401/403需鉴权；CLIENT=4xx(带参试探时多为404/422，属正常)；"
          "SERVER=5xx需排查；NET_ERR=网络异常；SKIP=未测试；路径后的 * 表示使用了样例参数")

    # 退出码：出现 SERVER 或 NET 视为失败
    if counters[SERVER] or counters[NET]:
        print("\n结果: 存在服务端错误/网络异常 ❌")
        return 1
    print("\n结果: 无服务端错误 ✅")
    return 0


if __name__ == "__main__":
    start = time.time()
    try:
        code = main()
    except KeyboardInterrupt:
        print("\n已中断")
        code = 130
    print(f"耗时 {time.time() - start:.2f}s")
    sys.exit(code)
