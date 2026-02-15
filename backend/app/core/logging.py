import logging
import sys

from app.core.context import get_trace_id
from app.core.settings import get_settings


class TraceIdFilter(logging.Filter):
    """Injects trace_id into every log record from the request context.

    This filter reads the current trace_id from contextvars (set by
    TraceIdMiddleware) and attaches it to the log record. Outside of a
    request context, the trace_id defaults to "-".

    # Future: OpenTelemetry integration
    # When adopting OTel, replace get_trace_id() with:
    #
    #   from opentelemetry import trace
    #   span = trace.get_current_span()
    #   record.trace_id = format(span.get_span_context().trace_id, "032x")
    #   record.span_id = format(span.get_span_context().span_id, "016x")
    #
    # This lets log aggregators (CloudWatch, Datadog, etc.) correlate logs
    # with distributed traces automatically.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = get_trace_id()  # type: ignore[attr-defined]
        return True


def setup_logging() -> None:
    trace_filter = TraceIdFilter()

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(trace_filter)

    logging.basicConfig(
        level=get_settings().log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - [%(trace_id)s] %(message)s",
        handlers=[handler],
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
