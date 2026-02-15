from fastapi import FastAPI, Request
import contextvars
import uvicorn

request_ctx = contextvars.ContextVar("request", default=None)


# 2. 定义自定义中间件类（适配add_middleware的写法）
class RequestContextMiddleware:
    """
    自定义请求上下文中间件：将request绑定到contextvars，实现全局共享
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # 仅处理HTTP请求（排除WebSocket等）
        if scope["type"] == "http":
            # 构建Request对象（Starlette的Request初始化方式）
            request = Request(scope, receive)
            # 将request存入上下文变量，记录token用于后续清理
            token = request_ctx.set(request)
            try:
                # 执行后续中间件/路由处理
                await self.app(scope, receive, send)
            finally:
                # 无论是否异常，都清理上下文（避免协程泄漏）
                request_ctx.reset(token)
        else:
            # 非HTTP请求直接放行
            await self.app(scope, receive, send)
