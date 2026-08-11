from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppError(Exception):
    def __init__(
        self,
        *,
        code: str,
        message: str,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


async def app_error_handler(_request: Request, error: AppError) -> JSONResponse:
    payload: dict[str, Any] = {
        "error": {
            "code": error.code,
            "message": error.message,
        }
    }
    if error.details:
        payload["error"]["details"] = error.details
    return JSONResponse(status_code=error.status_code, content=payload)


async def validation_error_handler(_request: Request, error: RequestValidationError) -> JSONResponse:
    details = [
        {
            "field": ".".join(str(part) for part in item["loc"] if part not in {"body", "query"}),
            "message": item["msg"],
        }
        for item in error.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "validation_error",
                "message": "The request is invalid.",
                "details": {"fields": details},
            }
        },
    )


async def unhandled_error_handler(_request: Request, _error: Exception) -> JSONResponse:
    request_id = getattr(_request.state, "request_id", None)
    return JSONResponse(
        status_code=500,
        headers={"X-Request-Id": request_id} if request_id else None,
        content={
            "error": {
                "code": "internal_error",
                "message": "The server could not complete this request.",
            }
        },
    )
