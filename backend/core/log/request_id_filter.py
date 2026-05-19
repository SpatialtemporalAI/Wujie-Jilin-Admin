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


class RequestIdFormatter(logging.Formatter):
    """自动注入 request_id 的格式化器，防止 filter 未生效时崩溃。"""

    def formatMessage(self, record: logging.LogRecord) -> str:
        if not hasattr(record, "request_id"):
            record.request_id = _request_id_ctx.get("-")
        return super().formatMessage(record)


def set_request_id(rid: str) -> None:
    _request_id_ctx.set(rid)
