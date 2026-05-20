#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP 上游 HTTP 客户端
用于 MCP 工具回调主应用 API
"""
import logging

import httpx

from mcp_server.config import settings
from mcp_server.context import mcp_request_ctx

logger = logging.getLogger(__name__)


class McpHttpClient:
    def __init__(self):
        self._base_url = settings.UPSTREAM_BASE_URL
        self._timeout = settings.REQUEST_TIMEOUT

    def _build_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        ctx = mcp_request_ctx.get()
        if ctx and ctx.token:
            headers[settings.AUTH_HEADER] = f"Bearer {ctx.token}"
        return headers

    async def get(self, path: str, params: dict | None = None) -> dict:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(
                f"{self._base_url}{path}",
                params=params,
                headers=self._build_headers(),
            )
            resp.raise_for_status()
            return resp.json()

    async def post(self, path: str, json_data: dict | None = None) -> dict:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(
                f"{self._base_url}{path}",
                json=json_data,
                headers=self._build_headers(),
            )
            resp.raise_for_status()
            return resp.json()

    async def put(self, path: str, json_data: dict | None = None) -> dict:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.put(
                f"{self._base_url}{path}",
                json=json_data,
                headers=self._build_headers(),
            )
            resp.raise_for_status()
            return resp.json()

    async def delete(self, path: str, params: dict | None = None) -> dict:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.delete(
                f"{self._base_url}{path}",
                params=params,
                headers=self._build_headers(),
            )
            resp.raise_for_status()
            return resp.json()
