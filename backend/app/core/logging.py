import json
import logging
import re
from datetime import datetime, timezone
from time import monotonic
from uuid import uuid4

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class JsonFormatter(logging.Formatter):
    """Keep stdout machine-readable so Cloud Logging can index fields."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "severity": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in (
            "request_id",
            "lesson_id",
            "owner_id_hash",
            "stage",
            "duration_ms",
            "provider",
            "model",
            "input_tokens",
            "output_tokens",
            "output_bytes",
            "http_method",
            "http_path",
            "http_status",
        ):
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)


class RequestLoggingMiddleware:
    """Log after the final response body so SSE durations include generation work."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self.logger = logging.getLogger("chalksmith.access")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        supplied_request_id = headers.get(b"x-request-id", b"").decode("ascii", errors="ignore")[:128]
        request_id = (
            supplied_request_id
            if re.fullmatch(r"[A-Za-z0-9._:-]+", supplied_request_id)
            else str(uuid4())
        )
        scope.setdefault("state", {})["request_id"] = request_id
        started = monotonic()
        status_code = 500
        completed = False
        response_started = False

        async def send_with_logging(message: Message) -> None:
            nonlocal completed, response_started, status_code
            if message["type"] == "http.response.start":
                response_started = True
                status_code = message["status"]
                response_headers = list(message.get("headers", []))
                response_headers.append((b"x-request-id", request_id.encode("utf-8")))
                message["headers"] = response_headers
            await send(message)
            if message["type"] == "http.response.body" and not message.get("more_body", False):
                completed = True
                self._log(scope, request_id, status_code, started)

        try:
            await self.app(scope, receive, send_with_logging)
        except Exception:
            logging.getLogger("backend.app.core.errors").exception(
                "unhandled_request_error",
                extra={"request_id": request_id},
            )
            if response_started:
                if not completed:
                    self._log(scope, request_id, status_code, started)
                raise
            response = JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "internal_error",
                        "message": "The server could not complete this request.",
                    }
                },
            )
            await response(scope, receive, send_with_logging)

    def _log(self, scope: Scope, request_id: str, status_code: int, started: float) -> None:
        self.logger.info(
            "request_completed",
            extra={
                "request_id": request_id,
                "http_method": scope.get("method"),
                "http_path": scope.get("path"),
                "http_status": status_code,
                "duration_ms": round((monotonic() - started) * 1000),
            },
        )
