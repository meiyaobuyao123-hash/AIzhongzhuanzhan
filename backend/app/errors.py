"""OpenAI-style error responses + exception classes for upstream errors.

We always return JSON in OpenAI's error format:
    {"error": {"message": "...", "type": "...", "code": "...", "param": "..."}}

Even when the underlying request was Anthropic-flavored (/v1/messages), this format
is fine — Anthropic SDKs and Claude Code tolerate it (they just check HTTP status).
Standardizing on one format avoids Provider-specific error mapping in clients.
"""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from fastapi.responses import JSONResponse


# ---- Standard "type" values --------------------------------------------------

ERROR_TYPE_INVALID_REQUEST = "invalid_request_error"
ERROR_TYPE_AUTHENTICATION = "authentication_error"
ERROR_TYPE_PERMISSION = "permission_error"
ERROR_TYPE_RATE_LIMIT = "rate_limit_error"
ERROR_TYPE_INSUFFICIENT_QUOTA = "insufficient_quota"
ERROR_TYPE_API_ERROR = "api_error"


def error_response(
    status_code: int,
    message: str,
    type_: str,
    code: str | None = None,
    param: str | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {"error": {"message": message, "type": type_}}
    if code:
        body["error"]["code"] = code
    if param:
        body["error"]["param"] = param
    return JSONResponse(status_code=status_code, content=body)


# ---- Domain exceptions -------------------------------------------------------


class PrismException(Exception):
    """Base for all Prism domain exceptions."""

    status_code: int = 500
    error_type: str = ERROR_TYPE_API_ERROR
    code: str | None = None

    def __init__(self, message: str, *, param: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.param = param


class InvalidAPIKey(PrismException):
    status_code = 401
    error_type = ERROR_TYPE_AUTHENTICATION
    code = "invalid_api_key"


class UserDisabled(PrismException):
    status_code = 403
    error_type = ERROR_TYPE_PERMISSION
    code = "user_disabled"


class InsufficientBalance(PrismException):
    status_code = 402
    error_type = ERROR_TYPE_INSUFFICIENT_QUOTA
    code = "insufficient_balance"


class ModelNotFound(PrismException):
    status_code = 404
    error_type = ERROR_TYPE_INVALID_REQUEST
    code = "model_not_found"


class NoChannelAvailable(PrismException):
    status_code = 503
    error_type = ERROR_TYPE_API_ERROR
    code = "no_channel_available"


class UpstreamRateLimit(PrismException):
    status_code = 429
    error_type = ERROR_TYPE_RATE_LIMIT
    code = "upstream_rate_limit"


class UpstreamError(PrismException):
    """Generic upstream non-2xx that we couldn't otherwise classify."""

    status_code = 502
    error_type = ERROR_TYPE_API_ERROR
    code = "upstream_error"


# ---- HTTPException helper used by routes -------------------------------------


def to_http(exc: PrismException) -> HTTPException:
    """Used inside routes when we want FastAPI's default exception handling."""
    return HTTPException(
        status_code=exc.status_code,
        detail={"message": exc.message, "type": exc.error_type, "code": exc.code},
    )
