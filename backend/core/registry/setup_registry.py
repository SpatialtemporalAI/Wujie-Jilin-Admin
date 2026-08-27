from core.exception import setup_exception_handlers, setup_exception_global_handlers
from database.plugins import setup_soft_delete_plug
from fastapi import FastAPI
from core.log import setup_logging
from core.middleware.share_middleware import RequestContextMiddleware
from core.middleware.security_middleware import (
    RequestAuditMiddleware,
    RequestSizeLimitMiddleware,
    SecurityHeadersMiddleware,
)
from core.middleware.operation_log_middleware import OperationLogMiddleware
from core.middleware.merchant_call_log_middleware import MerchantCallLogMiddleware
from core.middleware.rate_limit_middleware import RateLimitMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from core.config import GlobalSetting


def setup_app(app: FastAPI, settings: GlobalSetting):
    """
    注册全局信息
    """

    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=settings.SECURITY.ALLOWED_HOSTS
    )

    app.add_middleware(RequestAuditMiddleware)
    app.add_middleware(RequestSizeLimitMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(MerchantCallLogMiddleware)
    app.add_middleware(OperationLogMiddleware)
    app.add_middleware(RequestContextMiddleware)

    # 配置跨域（允许其他服务访问）
    # 注意：Starlette 后注册的先执行，CORS 必须最后注册（最外层）。
    # 否则 RateLimit/RequestSizeLimit 等中间件短路返回的 429/413 响应
    # 不会携带 CORS 头，跨域场景下浏览器拦截响应，前端只能看到 Network Error
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.SECURITY.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册全局异常
    setup_exception_handlers(app)
    setup_exception_global_handlers(app)
    # 注册软删除插件
    setup_soft_delete_plug()
    # 注册日志
    setup_logging()
    # 加载插件
    if settings.PLUGINS.ENABLED:
        from plugins import load_plugins
        load_plugins(app, settings.PLUGINS.ENABLED)
