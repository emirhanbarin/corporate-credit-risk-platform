"""Pure SEC HTTP status interpretation without body inspection or retry execution."""

from __future__ import annotations

from credit_risk_platform.providers.http import HttpResponse
from credit_risk_platform.providers.sec.errors import (
    SecNotFoundError,
    SecRateLimitError,
    SecResponseError,
    SecServerError,
    _sanitize_request_url,
)


def validate_sec_response(
    response: HttpResponse,
    *,
    request_url: str | None = None,
) -> HttpResponse:
    """Return 2xx responses unchanged or raise a safe typed SEC response error.

    Mapping precedence is 2xx success, 429 rate limit, 404 not found, 5xx server
    error, then generic response error. The mapper does not inspect bodies or
    headers, parse Retry-After, or make retry decisions.
    """
    if not isinstance(response, HttpResponse):
        raise ValueError("response must be an HttpResponse.")

    sanitized_request_url = _sanitize_request_url(request_url)
    status_code = response.status_code
    if 200 <= status_code <= 299:
        return response
    if status_code == 429:
        raise SecRateLimitError(
            status_code=status_code,
            request_url=sanitized_request_url,
        )
    if status_code == 404:
        raise SecNotFoundError(
            status_code=status_code,
            request_url=sanitized_request_url,
        )
    if 500 <= status_code <= 599:
        raise SecServerError(
            status_code=status_code,
            request_url=sanitized_request_url,
        )
    raise SecResponseError(
        status_code=status_code,
        request_url=sanitized_request_url,
    )
