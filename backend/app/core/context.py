"""Request-scoped context using contextvars.

Provides a trace_id that is automatically set per request by the TraceIdMiddleware
and automatically injected into every log record by the TraceIdFilter.

Usage in application code:

    from app.core.context import get_trace_id

    trace_id = get_trace_id()  # returns current request's trace_id or "-"

No application code needs to call set_trace_id — the middleware handles that.

# Future: OpenTelemetry integration
# When adopting OTel, replace the ContextVar with OTel's trace context:
#
#   from opentelemetry import trace
#
#   def get_trace_id() -> str:
#       span = trace.get_current_span()
#       ctx = span.get_span_context()
#       if ctx.trace_id:
#           return format(ctx.trace_id, "032x")
#       return "-"
#
# The middleware would then become an OTel instrumentation layer,
# and the logging filter would read from OTel context instead.
"""

from contextvars import ContextVar

_trace_id_ctx: ContextVar[str] = ContextVar("trace_id", default="-")


def get_trace_id() -> str:
    return _trace_id_ctx.get()


def set_trace_id(trace_id: str) -> None:
    _trace_id_ctx.set(trace_id)
