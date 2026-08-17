import contextvars
import json
import logging
import logging.handlers
import os

request_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)

_RESERVED_RECORD_ATTRS = frozenset(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {"message", "asctime"}


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get() or "-"
        return True


class JsonFormatter(logging.Formatter):
    """Structured logging so log lines are queryable in a production log
    aggregator (request_id, level, logger name, message, timestamp, plus any
    `extra=` fields callers attach) instead of grep-only plain text."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "request_id": getattr(record, "request_id", "-"),
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in _RESERVED_RECORD_ATTRS and key not in payload:
                try:
                    json.dumps(value)
                except TypeError:
                    value = repr(value)
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def setup_logging(level: int | None = None) -> None:
    log_level = level if level is not None else getattr(logging, os.environ.get("LOG_LEVEL", "INFO").upper(), logging.INFO)

    # Rotating, not a plain FileHandler — an unrotated app.log grows without
    # bound in a long-running production process.
    handler_file = logging.handlers.RotatingFileHandler(
        "app.log", maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    handler_console = logging.StreamHandler()

    formatter = JsonFormatter()
    for h in (handler_file, handler_console):
        h.setFormatter(formatter)
        h.addFilter(RequestIdFilter())

    root = logging.getLogger()
    root.setLevel(log_level)
    root.handlers = [handler_file, handler_console]
