from fastapi import Request
import ipaddress
from logging import getLogger

from core.config import settings

logger = getLogger(__name__)


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
    client_host = request.client.host if request.client else ""
    trusted_proxies = set(settings.SECURITY.TRUSTED_PROXIES)
    is_trusted = client_host in trusted_proxies
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    x_real_ip = request.headers.get("X-Real-IP")

    # 1. 先判断请求是否来自可信代理，再解析X-Forwarded-For（最常用）
    if x_forwarded_for and is_trusted:
        # X-Forwarded-For格式：client_ip, proxy1_ip, proxy2_ip...（取第一个有效IP）
        ips = [ip.strip() for ip in x_forwarded_for.split(",") if ip.strip()]
        if ips:
            normalized = _normalize_ip(ips[0])
            if normalized:
                logger.debug(
                    "get_real_client_ip resolve from X-Forwarded-For client_host=%s trusted=%s xff=%s -> %s",
                    client_host, is_trusted, x_forwarded_for, normalized,
                )
                return normalized

    # 2. 解析X-Real-IP（部分代理如Nginx常用）
    if x_real_ip and is_trusted:
        normalized = _normalize_ip(x_real_ip)
        if normalized:
            logger.debug(
                "get_real_client_ip resolve from X-Real-IP client_host=%s trusted=%s xri=%s -> %s",
                client_host, is_trusted, x_real_ip, normalized,
            )
            return normalized

    # 3. 无代理时，直接取request.client.host
    normalized = _normalize_ip(client_host)
    final = normalized or "unknown"

    if not is_trusted and (x_forwarded_for or x_real_ip):
        # 来自非可信代理但携带了转发头，提示运维 SECURITY.TRUSTED_PROXIES 可能遗漏
        logger.warning(
            "get_real_client_ip untrusted proxy with forward headers "
            "client_host=%s trusted_proxies=%s xff=%s xri=%s -> fallback=%s "
            "(check SECURITY.TRUSTED_PROXIES if this is unexpected)",
            client_host, trusted_proxies, x_forwarded_for, x_real_ip, final,
        )
    else:
        logger.debug(
            "get_real_client_ip fallback to client_host client_host=%s trusted=%s -> %s",
            client_host, is_trusted, final,
        )
    return final
