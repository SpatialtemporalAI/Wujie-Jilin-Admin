import contextvars
import logging

_request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default="-"
)


class RequestIdFilter(logging.Filter):
    """将当前请求的 request_id 注入到每条日志记录中。"""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = _request_id_ctx.get("-")
        return True


def set_request_id(rid: str) -> None:
    _request_id_ctx.set(rid)
