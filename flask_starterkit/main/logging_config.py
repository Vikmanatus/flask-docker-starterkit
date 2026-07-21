"""Logging setup: one handler, on stdout, so the container runtime owns the logs.

Anything that writes log files inside a container is a mistake waiting for a
disk-full page, so both formatters here go to stdout and nowhere else.
"""

import json
import logging
import sys

# Attributes present on every LogRecord. Anything outside this set was attached
# by the caller via `extra=` and belongs in the structured output.
_RESERVED = set(logging.LogRecord("", 0, "", 0, "", None, None).__dict__) | {
    "asctime",
    "message",
    "taskName",
}


class JsonFormatter(logging.Formatter):
    """Render records as single-line JSON for log aggregators."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        for key, value in record.__dict__.items():
            if key not in _RESERVED and not key.startswith("_"):
                payload[key] = value

        return json.dumps(payload, default=str)


def configure_logging(app) -> None:
    """Point the app logger at stdout using the configured level and format."""
    level = getattr(logging, app.config.get("LOG_LEVEL", "INFO"), logging.INFO)

    if app.config.get("LOG_FORMAT") == "json":
        formatter: logging.Formatter = JsonFormatter()
    else:
        formatter = logging.Formatter("[%(asctime)s] %(levelname)-8s %(name)s: %(message)s")

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Replace rather than append, so reloads in dev don't stack up duplicate
    # handlers and print every line twice.
    app.logger.handlers = [handler]
    app.logger.setLevel(level)
    app.logger.propagate = False

    for name in ("werkzeug", "gunicorn.error", "gunicorn.access"):
        external = logging.getLogger(name)
        external.handlers = [handler]
        external.setLevel(level)
        external.propagate = False
