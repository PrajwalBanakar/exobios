import contextvars
import logging

request_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get() or "-"
        return True


def setup_logging(level: int = logging.INFO) -> None:
    handler_file = logging.FileHandler("app.log", encoding="utf-8")
    handler_console = logging.StreamHandler()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(request_id)s | %(name)s | %(message)s"
    )
    for h in (handler_file, handler_console):
        h.setFormatter(formatter)
        h.addFilter(RequestIdFilter())

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers = [handler_file, handler_console]