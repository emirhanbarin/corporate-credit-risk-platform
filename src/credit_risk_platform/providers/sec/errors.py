"""Safe exception types for the SEC provider boundary."""

from __future__ import annotations

import math
import unicodedata
from urllib.parse import urlsplit, urlunsplit


class SecProviderError(Exception):
    """Base exception for safe SEC provider failures."""

    _message = "SEC provider operation failed."

    def __init__(self) -> None:
        super().__init__(self._message)


class SecRequestError(SecProviderError):
    """Raised when an SEC request cannot be constructed."""

    _message = "SEC request construction failed."


class SecTransportError(SecProviderError):
    """Raised when transport fails before a response is available."""

    __slots__ = ("_request_url",)
    _message = "SEC request transport failed."

    def __init__(self, *, request_url: str | None = None) -> None:
        super().__init__()
        self._request_url = _sanitize_request_url(request_url)

    @property
    def request_url(self) -> str | None:
        """Return the sanitized request URL, when available."""
        return self._request_url


class SecTimeoutError(SecTransportError):
    """Raised when an SEC request exceeds its timeout."""

    __slots__ = ("_timeout_seconds",)
    _message = "SEC request timed out."

    def __init__(
        self,
        *,
        request_url: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        super().__init__(request_url=request_url)
        self._timeout_seconds = _validate_optional_timeout(timeout_seconds)

    @property
    def timeout_seconds(self) -> float | None:
        """Return the configured timeout, when available."""
        return self._timeout_seconds


class SecResponseError(SecProviderError):
    """Raised for an unsuccessful SEC HTTP response."""

    __slots__ = ("_request_url", "_status_code")
    _message = "SEC returned an unexpected response."

    def __init__(
        self,
        *,
        status_code: int,
        request_url: str | None = None,
    ) -> None:
        super().__init__()
        self._status_code = _validate_error_status(status_code)
        self._request_url = _sanitize_request_url(request_url)

    @property
    def status_code(self) -> int:
        """Return the HTTP error status."""
        return self._status_code

    @property
    def request_url(self) -> str | None:
        """Return the sanitized request URL, when available."""
        return self._request_url


class SecRateLimitError(SecResponseError):
    """Raised when SEC access is rate limited."""

    _message = "SEC rate limit was reached."

    def __init__(
        self,
        *,
        status_code: int = 429,
        request_url: str | None = None,
    ) -> None:
        super().__init__(status_code=status_code, request_url=request_url)


class SecNotFoundError(SecResponseError):
    """Raised when the requested SEC resource does not exist."""

    _message = "SEC resource was not found."

    def __init__(
        self,
        *,
        status_code: int = 404,
        request_url: str | None = None,
    ) -> None:
        super().__init__(status_code=status_code, request_url=request_url)


class SecServerError(SecResponseError):
    """Raised when SEC returns a server error."""

    _message = "SEC returned a server error."

    def __init__(
        self,
        *,
        status_code: int,
        request_url: str | None = None,
    ) -> None:
        super().__init__(status_code=status_code, request_url=request_url)


def _validate_error_status(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 400 <= value <= 599:
        raise ValueError("status_code must be an HTTP error status from 400 to 599.")
    return value


def _validate_optional_timeout(value: float | None) -> float | None:
    if value is None:
        return None
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value <= 0
    ):
        raise ValueError("timeout_seconds must be a positive finite number.")
    return float(value)


def _sanitize_request_url(value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ValueError("request_url must be a valid absolute HTTPS URL.")
    if any(character.isspace() or _is_control(character) for character in value):
        raise ValueError("request_url must be a valid absolute HTTPS URL.")
    if "\\" in value:
        raise ValueError("request_url must be a valid absolute HTTPS URL.")

    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError as error:
        raise ValueError("request_url must be a valid absolute HTTPS URL.") from error

    if parsed.scheme.casefold() != "https" or hostname is None:
        raise ValueError("request_url must be a valid absolute HTTPS URL.")

    host = f"[{hostname}]" if ":" in hostname else hostname
    authority = f"{host}:{port}" if port is not None else host
    return urlunsplit(("https", authority, parsed.path, "", ""))


def _is_control(character: str) -> bool:
    return unicodedata.category(character) == "Cc"
