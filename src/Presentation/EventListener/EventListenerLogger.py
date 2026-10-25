import json
import logging
import traceback
from contextvars import ContextVar
from datetime import datetime
from typing import Any
from uuid import uuid4

EVENT_LISTENER_TRACE_ID_CONTEXT: ContextVar[str | None] = ContextVar("event_listener_trace_id", default=None)


class _EventListenerJsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        stacktrace = None
        if record.exc_info:
            stacktrace = "".join(traceback.format_exception(*record.exc_info))
        elif record.stack_info:
            stacktrace = record.stack_info

        payload: Any = getattr(record, "payload", None)
        trace_id: str | None = getattr(record, "trace_id", None) or EVENT_LISTENER_TRACE_ID_CONTEXT.get()

        log_data = {
            "timestamp": datetime.now().astimezone().isoformat(),
            "log_level": record.levelname,
            "file": f"{record.pathname} line: {record.lineno} function: {record.funcName}",
            "trace_id": trace_id or str(uuid4()),
            "message": record.getMessage(),
            "payload": payload,
            "stacktrace": stacktrace,
        }

        return json.dumps(log_data, ensure_ascii=False, default=str)


class EventListenerLogger:
    @staticmethod
    def set_trace_id(trace_id: str | None = None) -> str:
        current_trace_id = trace_id or str(uuid4())
        EVENT_LISTENER_TRACE_ID_CONTEXT.set(current_trace_id)
        return current_trace_id

    @staticmethod
    def set_logger() -> logging.Logger:
        event_listener_logger = logging.getLogger("presentation.eventlistener")
        event_listener_logger.setLevel(logging.INFO)
        event_listener_logger.propagate = False

        if not event_listener_logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(_EventListenerJsonFormatter())
            event_listener_logger.addHandler(console_handler)
        else:
            for handler in event_listener_logger.handlers:
                handler.setLevel(logging.INFO)
                handler.setFormatter(_EventListenerJsonFormatter())

        return event_listener_logger
