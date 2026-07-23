"""Minimal transport-independent HTTP contracts."""

from __future__ import annotations

import math
import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Protocol
from urllib.parse import urlsplit

_HEADER_NAME = re.compile(r"[!#$%&'*+\-.^_`|~0-9A-Za-z]+")


@dataclass(frozen=True, slots=True)
class HttpRequest:
    """An immutable request passed to an HTTP transport."""

    method: str
    url: str
    headers: Mapping[str, str]
    timeout_seconds: float

    def __post_init__(self) -> None:
        method = _validate_method(self.method)
        _validate_https_url(self.url)
        headers = _copy_and_validate_headers(self.headers)
        _validate_positive_finite_number(self.timeout_seconds, "timeout_seconds")

        object.__setattr__(self, "method", method)
        object.__setattr__(self, "headers", headers)


@dataclass(frozen=True, slots=True)
class HttpResponse:
    """An immutable response returned by an HTTP transport."""

    status_code: int
    headers: Mapping[str, str]
    body: bytes

    def __post_init__(self) -> None:
        if (
            isinstance(self.status_code, bool)
            or not isinstance(self.status_code, int)
            or not 100 <= self.status_code <= 599
        ):
            raise ValueError("status_code must be an integer from 100 through 599.")

        headers = _copy_and_validate_headers(self.headers)
        try:
            body = bytes(self.body)
        except (TypeError, ValueError) as error:
            raise ValueError("body must be bytes-like.") from error

        object.__setattr__(self, "headers", headers)
        object.__setattr__(self, "body", body)


class HttpTransport(Protocol):
    """The minimal interface implemented by a future HTTP transport."""

    def send(self, request: HttpRequest) -> HttpResponse:
        """Send one request and return its unprocessed response."""
        ...


def _validate_method(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("method must be a non-blank string.")
    if any(character.isspace() or _is_control(character) for character in value):
        raise ValueError("method must not contain whitespace or control characters.")
    return value.upper()


def _validate_https_url(value: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError("url must be an absolute HTTPS URL.")
    if any(character.isspace() or _is_control(character) for character in value):
        raise ValueError("url must not contain whitespace or control characters.")
    if "\\" in value:
        raise ValueError("url must not contain backslashes.")

    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        _port = parsed.port
    except ValueError as error:
        raise ValueError("url must be a valid absolute HTTPS URL.") from error

    if parsed.scheme.casefold() != "https" or hostname is None:
        raise ValueError("url must be an absolute HTTPS URL with a hostname.")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("url must not contain credentials.")
    if parsed.fragment:
        raise ValueError("url must not contain a fragment.")


def _copy_and_validate_headers(
    headers: Mapping[str, str],
) -> Mapping[str, str]:
    copied: dict[str, str] = {}
    casefolded_names: set[str] = set()

    try:
        header_items = headers.items()
    except AttributeError as error:
        raise ValueError("headers must be a string mapping.") from error

    for name, value in header_items:
        if not isinstance(name, str) or _HEADER_NAME.fullmatch(name) is None:
            raise ValueError("header names must use valid HTTP field-name characters.")
        if not isinstance(value, str):
            raise ValueError("header values must be strings.")
        if any(_is_control(character) for character in value):
            raise ValueError("header values must not contain control characters.")

        casefolded_name = name.casefold()
        if casefolded_name in casefolded_names:
            raise ValueError("header names must be unique case-insensitively.")
        casefolded_names.add(casefolded_name)
        copied[name] = value

    return MappingProxyType(copied)


def _validate_positive_finite_number(value: float, field: str) -> None:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value <= 0
    ):
        raise ValueError(f"{field} must be a positive finite number.")


def _is_control(character: str) -> bool:
    return unicodedata.category(character) == "Cc"
