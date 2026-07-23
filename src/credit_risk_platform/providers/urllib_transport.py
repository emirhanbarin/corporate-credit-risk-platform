"""Synchronous standard-library HTTP transport."""

from __future__ import annotations

import math
import socket
import ssl
import urllib.error
import urllib.request
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Protocol, cast

from credit_risk_platform.providers.http import HttpRequest, HttpResponse

_DEFAULT_MAX_RESPONSE_BYTES = 10_000_000


class HttpTransportError(Exception):
    """Base exception for safe HTTP transport execution failures."""

    _message = "HTTP transport failed."

    def __init__(self) -> None:
        super().__init__(self._message)


class HttpTimeoutError(HttpTransportError):
    """Raised when an HTTP request exceeds its timeout."""

    __slots__ = ("_timeout_seconds",)
    _message = "HTTP request timed out."

    def __init__(self, *, timeout_seconds: float) -> None:
        super().__init__()
        self._timeout_seconds = _validate_timeout(timeout_seconds)

    @property
    def timeout_seconds(self) -> float:
        """Return the request timeout."""
        return self._timeout_seconds


class HttpResponseTooLargeError(HttpTransportError):
    """Raised when an HTTP response exceeds the configured body limit."""

    __slots__ = ("_max_response_bytes",)
    _message = "HTTP response body exceeded the configured size limit."

    def __init__(self, *, max_response_bytes: int) -> None:
        super().__init__()
        self._max_response_bytes = _validate_max_response_bytes(max_response_bytes)

    @property
    def max_response_bytes(self) -> int:
        """Return the configured response-body limit."""
        return self._max_response_bytes


@dataclass(frozen=True, slots=True, init=False)
class UrllibHttpTransport:
    """Send immutable HTTP requests with Python's standard library."""

    _max_response_bytes: int = field(repr=False)
    _ssl_context: ssl.SSLContext = field(repr=False)

    def __init__(
        self,
        max_response_bytes: int = _DEFAULT_MAX_RESPONSE_BYTES,
        ssl_context: ssl.SSLContext | None = None,
    ) -> None:
        validated_limit = _validate_max_response_bytes(max_response_bytes)
        retained_context = (
            ssl.create_default_context() if ssl_context is None else ssl_context
        )
        object.__setattr__(self, "_max_response_bytes", validated_limit)
        object.__setattr__(self, "_ssl_context", retained_context)

    def send(self, request: HttpRequest) -> HttpResponse:
        """Send one request and return every valid HTTP response unchanged."""
        urllib_request = urllib.request.Request(
            request.url,
            headers=dict(request.headers),
            method=request.method,
        )

        try:
            try:
                response = cast(
                    _ReadableResponse,
                    urllib.request.urlopen(
                        urllib_request,
                        timeout=request.timeout_seconds,
                        context=self._ssl_context,
                    ),
                )
            except urllib.error.HTTPError as error:
                return self._consume_response(
                    cast(_ReadableResponse, error),
                    status_code=error.code,
                )

            try:
                status_code = response.status
            except AttributeError as error:
                response.close()
                raise HttpTransportError() from error
            return self._consume_response(response, status_code=status_code)
        except HttpTransportError:
            raise
        except (socket.timeout, TimeoutError) as error:
            raise HttpTimeoutError(timeout_seconds=request.timeout_seconds) from error
        except urllib.error.URLError as error:
            if isinstance(error.reason, (socket.timeout, TimeoutError)):
                raise HttpTimeoutError(
                    timeout_seconds=request.timeout_seconds
                ) from error
            raise HttpTransportError() from error
        except (ssl.SSLError, OSError) as error:
            raise HttpTransportError() from error

    def _consume_response(
        self,
        response: _ReadableResponse,
        *,
        status_code: int,
    ) -> HttpResponse:
        try:
            try:
                response_headers = response.headers
            except AttributeError as error:
                raise HttpTransportError() from error

            headers, content_length = _convert_response_headers(response_headers)
            if content_length is not None and content_length > self._max_response_bytes:
                raise HttpResponseTooLargeError(
                    max_response_bytes=self._max_response_bytes
                )

            body = _read_bounded(response, self._max_response_bytes)
            try:
                return HttpResponse(
                    status_code=status_code,
                    headers=headers,
                    body=body,
                )
            except ValueError as error:
                raise HttpTransportError() from error
        finally:
            response.close()


class _ResponseHeaders(Protocol):
    def raw_items(self) -> Iterable[tuple[str, str]]:
        """Return response header pairs without collapsing duplicates."""
        ...


class _ReadableResponse(Protocol):
    status: int
    headers: _ResponseHeaders

    def read(self, amount: int = -1) -> bytes:
        """Read up to the requested number of bytes."""
        ...

    def close(self) -> None:
        """Close the response."""
        ...


def _convert_response_headers(
    source: _ResponseHeaders,
) -> tuple[dict[str, str], int | None]:
    grouped: dict[str, tuple[str, list[str]]] = {}
    content_length_values: list[str] = []

    try:
        items = source.raw_items()
    except AttributeError as error:
        raise HttpTransportError() from error

    for name, value in items:
        if not isinstance(name, str) or not isinstance(value, str):
            raise HttpTransportError()

        casefolded_name = name.casefold()
        existing = grouped.get(casefolded_name)
        if existing is None:
            grouped[casefolded_name] = (name, [value])
        else:
            existing[1].append(value)

        if casefolded_name == "content-length":
            content_length_values.append(value)

    converted = {
        original_name: ", ".join(values) for original_name, values in grouped.values()
    }
    content_length = _trusted_content_length(content_length_values)
    return converted, content_length


def _trusted_content_length(values: list[str]) -> int | None:
    if len(values) != 1:
        return None

    stripped = values[0].strip()
    if not stripped or not all("0" <= character <= "9" for character in stripped):
        return None

    try:
        content_length = int(stripped)
    except ValueError:
        return None
    return content_length if content_length > 0 else None


def _read_bounded(response: _ReadableResponse, limit: int) -> bytes:
    chunks: list[bytes] = []
    bytes_read = 0
    maximum_read = limit + 1

    while bytes_read < maximum_read:
        chunk = response.read(maximum_read - bytes_read)
        if not chunk:
            break
        if not isinstance(chunk, bytes):
            raise HttpTransportError()
        chunks.append(chunk)
        bytes_read += len(chunk)

    if bytes_read > limit:
        raise HttpResponseTooLargeError(max_response_bytes=limit)
    return b"".join(chunks)


def _validate_max_response_bytes(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError("max_response_bytes must be a positive integer.")
    return value


def _validate_timeout(value: float) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value <= 0
    ):
        raise ValueError("timeout_seconds must be a positive finite number.")
    return float(value)
