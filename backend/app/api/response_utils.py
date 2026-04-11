from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.app.core.config import get_settings
from backend.app.domain.exceptions import DomainError
from backend.app.schemas import ErrorDetailItem, ErrorDetailView, ErrorResponse, ResponseMeta


def build_response_meta(
    request: Request,
    *,
    generated_at: datetime | None = None,
) -> ResponseMeta:
    settings = get_settings()
    request_id = getattr(request.state, "request_id", None) or "unknown"
    return ResponseMeta(
        request_id=request_id,
        timestamp=generated_at or datetime.now(timezone.utc),
        contract_version=settings.api_contract_version,
    )


def append_meta(request: Request, payload: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(payload)
    enriched["meta"] = build_response_meta(request).model_dump(mode="json")
    return enriched


def _http_error_code(status_code: int, detail: str | None) -> str:
    normalized = (detail or "").strip().lower()
    detail_map = {
        "invalid credentials.": "INVALID_CREDENTIALS",
        "user account is locked.": "ACCOUNT_LOCKED",
        "captcha verification failed.": "CAPTCHA_FAILED",
        "reset token expired.": "RESET_TOKEN_EXPIRED",
        "email already registered.": "EMAIL_TAKEN",
        "username already registered.": "USERNAME_TAKEN",
        "user not found.": "USER_NOT_FOUND",
    }
    if normalized in detail_map:
        return detail_map[normalized]

    status_map = {
        status.HTTP_400_BAD_REQUEST: "BAD_REQUEST",
        status.HTTP_401_UNAUTHORIZED: "AUTH_REQUIRED",
        status.HTTP_403_FORBIDDEN: "FORBIDDEN",
        status.HTTP_404_NOT_FOUND: "NOT_FOUND",
        status.HTTP_409_CONFLICT: "CONFLICT",
        status.HTTP_422_UNPROCESSABLE_ENTITY: "VALIDATION_ERROR",
        status.HTTP_423_LOCKED: "ACCOUNT_LOCKED",
        status.HTTP_429_TOO_MANY_REQUESTS: "RATE_LIMITED",
    }
    return status_map.get(status_code, "REQUEST_FAILED")


def _domain_error_code(exc: DomainError) -> str:
    explicit = {
        "UnsupportedTrackTypeError": "UNSUPPORTED_TRACK_TYPE",
        "MissingFieldError": "MISSING_REQUIRED_FIELD",
        "InvalidScenarioInputError": "INVALID_SCENARIO_INPUT",
        "ScenarioGenerationLimitError": "SCENARIO_LIMIT_EXCEEDED",
        "MissingMarketInputError": "MISSING_MARKET_DATA",
        "MarketDataFetchError": "MARKET_DATA_FETCH_FAILED",
        "MarketDataParseError": "MARKET_DATA_PARSE_FAILED",
        "MarketDataValidationError": "INVALID_MARKET_DATA",
        "MarketDataStaleError": "STALE_MARKET_DATA",
        "MarketDataNotFoundError": "MISSING_MARKET_DATA",
        "MarketDataBucketLookupError": "AMBIGUOUS_MARKET_BUCKET",
    }
    return explicit.get(type(exc).__name__, "DOMAIN_ERROR")


def error_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    fields: list[ErrorDetailItem] | None = None,
) -> JSONResponse:
    payload = ErrorResponse(
        detail=message,
        error=ErrorDetailView(code=code, message=message, fields=fields or []),
        meta=build_response_meta(request),
    )
    response = JSONResponse(status_code=status_code, content=payload.model_dump(mode="json"))
    response.headers["X-Request-ID"] = payload.meta.request_id
    return response


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, str) else "Request failed."
    return error_response(
        request,
        status_code=exc.status_code,
        code=_http_error_code(exc.status_code, detail),
        message=detail,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    fields = [
        ErrorDetailItem(
            field=".".join(str(part) for part in error["loc"] if part != "body"),
            message=error["msg"],
            error_type=error["type"],
        )
        for error in exc.errors()
    ]
    return error_response(
        request,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        code="VALIDATION_ERROR",
        message="Validation error.",
        fields=fields,
    )


async def domain_exception_handler(request: Request, exc: DomainError) -> JSONResponse:
    return error_response(
        request,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        code=_domain_error_code(exc),
        message=str(exc),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    settings = get_settings()
    message = str(exc) if settings.debug else "Internal server error."
    return error_response(
        request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="INTERNAL_ERROR",
        message=message,
    )
