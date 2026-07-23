"""Deterministic construction of SEC HTTP requests."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urlencode, urlsplit, urlunsplit

from credit_risk_platform.config import AppSettings
from credit_risk_platform.providers.http import HttpRequest
from credit_risk_platform.providers.sec.models import SecRequest

_EMAIL_TOKEN_CHARACTER = r"A-Za-z0-9.!#$%&'*+/=?^_`{|}~-"


_INVALID_AUTHORITY_MESSAGE = "base_url must be a valid root HTTPS authority."


@dataclass(frozen=True, slots=True, init=False)
class SecRequestBuilder:
    """Build requests for one immutable SEC authority selected at construction.

    Separate builders are required for separate SEC hosts. Relative request paths
    and query values cannot select or replace the builder's authority; endpoint
    paths remain outside settings and builder logic.
    """

    settings: AppSettings
    _base_url: str = field(repr=False)

    def __init__(self, settings: AppSettings, *, base_url: str) -> None:
        if not isinstance(settings, AppSettings):
            raise ValueError("settings must be an AppSettings.")
        authority = _validate_and_normalize_authority(base_url)
        object.__setattr__(self, "settings", settings)
        object.__setattr__(self, "_base_url", authority)

    def build(self, request: SecRequest) -> HttpRequest:
        """Convert a validated SEC request into an immutable HTTP request."""
        parsed_base = urlsplit(self._base_url)
        query = urlencode(sorted(request.query.items()))
        url = urlunsplit(
            (
                parsed_base.scheme,
                parsed_base.netloc,
                request.path,
                query,
                "",
            )
        )

        return HttpRequest(
            method="GET",
            url=url,
            headers={
                "User-Agent": _build_user_agent(self.settings),
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate",
            },
            timeout_seconds=self.settings.sec_request_timeout_seconds,
        )


def _validate_and_normalize_authority(value: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or any(
            character.isspace() or not character.isprintable() for character in value
        )
        or "\\" in value
        or "?" in value
        or "#" in value
    ):
        raise ValueError(_INVALID_AUTHORITY_MESSAGE)

    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        parsed = None
        hostname = None
        port = None

    if (
        parsed is None
        or parsed.scheme.casefold() != "https"
        or hostname is None
        or (port is not None and port <= 0)
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
    ):
        raise ValueError(_INVALID_AUTHORITY_MESSAGE)

    return urlunsplit(("https", parsed.netloc, "", "", ""))


def _build_user_agent(settings: AppSettings) -> str:
    pattern = re.compile(
        rf"(?<![{_EMAIL_TOKEN_CHARACTER}])"
        rf"{re.escape(settings.sec_contact_email)}"
        rf"(?![{_EMAIL_TOKEN_CHARACTER}])",
        re.IGNORECASE,
    )
    if pattern.search(settings.sec_user_agent):
        return settings.sec_user_agent
    return f"{settings.sec_user_agent} {settings.sec_contact_email}"
