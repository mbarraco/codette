"""ASGI middleware for request tracing.

Generates a unique trace_id per request, stores it in contextvars for the
duration of the request, and returns it in the X-Trace-ID response header.

If the client sends an X-Trace-ID header, that value is propagated instead of
generating a new one. This enables distributed tracing across services (e.g.,
when the worker calls back to the API, or when a gateway fronts the API).

# Future: OpenTelemetry migration
# When adopting OTel, replace this middleware with:
#
#   from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
#   FastAPIInstrumentor.instrument_app(app)
#
# OTel's instrumentation handles trace propagation (W3C Trace Context),
# span creation, and context management automatically. The X-Trace-ID
# header can still be set from the OTel span context if needed for
# client-facing debugging.
"""

import uuid

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.context import set_trace_id

_TRACE_HEADER = "x-trace-id"


class TraceIdMiddleware:
    """ASGI middleware that assigns a trace_id to every HTTP request."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        trace_id = _extract_trace_id(scope["headers"]) or uuid.uuid4().hex
        set_trace_id(trace_id)

        async def send_with_trace_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-trace-id", trace_id.encode()))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_trace_id)


def _extract_trace_id(raw_headers: list[tuple[bytes, bytes]]) -> str | None:
    """Extract X-Trace-ID from raw ASGI headers if present."""
    for name, value in raw_headers:
        if name.lower() == b"x-trace-id":
            decoded = value.decode("latin-1").strip()
            if decoded:
                return decoded
    return None
