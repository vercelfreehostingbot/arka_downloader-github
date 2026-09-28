"""Structured logging setup."""
from __future__ import annotations
import logging
import os
import sys

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        import json
        return json.dumps({"level": record.levelname, "logger": record.name, "message": record.getMessage(), "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z")}, ensure_ascii=False)

def configure() -> None:
    root = logging.getLogger()
    root.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.handlers[:] = [handler]
