from fastapi import Request

TRUSTED_PROXIES = ["127.0.0.1", "::1"]  # 本地开发环境常用IP


def get_real_client_ip(request: Request) -> str:
    """
    安全获取客户端真实IP，处理反向代理场景，防止IP伪造
    """
    # 1. 先判断请求是否来自可信代理，再解析X-Forwarded-For（最常用）
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for and request.client.host in TRUSTED_PROXIES:
        # X-Forwarded-For格式：client_ip, proxy1_ip, proxy2_ip...（取第一个有效IP）
        ips = [ip.strip() for ip in x_forwarded_for.split(",") if ip.strip()]
        if ips:
            return ips[0]

    # 2. 解析X-Real-IP（部分代理如Nginx常用）
    x_real_ip = request.headers.get("X-Real-IP")
    if x_real_ip and request.client.host in TRUSTED_PROXIES:
        return x_real_ip.strip()

    # 3. 无代理时，直接取request.client.host
    return request.client.host if request.client else "unknown"
