from fastapi import Request
import ipaddress

from core.config import settings


def _normalize_ip(raw_ip: str) -> str:
    """标准化并校验 IP，非法时返回空字符串。"""
    try:
        return str(ipaddress.ip_address(raw_ip.strip()))
    except ValueError:
        return ""


def get_real_client_ip(request: Request) -> str:
    """
    安全获取客户端真实IP，处理反向代理场景，防止IP伪造
    """
    # 1. 先判断请求是否来自可信代理，再解析X-Forwarded-For（最常用）
    client_host = request.client.host if request.client else ""
    trusted_proxies = set(settings.SECURITY.TRUSTED_PROXIES)
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for and client_host in trusted_proxies:
        # X-Forwarded-For格式：client_ip, proxy1_ip, proxy2_ip...（取第一个有效IP）
        ips = [ip.strip() for ip in x_forwarded_for.split(",") if ip.strip()]
        if ips:
            normalized = _normalize_ip(ips[0])
            if normalized:
                return normalized

    # 2. 解析X-Real-IP（部分代理如Nginx常用）
    x_real_ip = request.headers.get("X-Real-IP")
    if x_real_ip and client_host in trusted_proxies:
        normalized = _normalize_ip(x_real_ip)
        if normalized:
            return normalized

    # 3. 无代理时，直接取request.client.host
    normalized = _normalize_ip(client_host)
    return normalized or "unknown"
