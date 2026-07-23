"""Deterministic construction of SEC HTTP requests."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlencode, urlsplit, urlunsplit

from credit_risk_platform.config import AppSettings
from credit_risk_platform.providers.http import HttpRequest
from credit_risk_platform.providers.sec.models import SecRequest

_EMAIL_TOKEN_CHARACTER = r"A-Za-z0-9.!#$%&'*+/=?^_`{|}~-"


@dataclass(frozen=True, slots=True)
class SecRequestBuilder:
    """Build transport-neutral GET requests for the configured SEC origin."""

    settings: AppSettings

    def build(self, request: SecRequest) -> HttpRequest:
        """Convert a validated SEC request into an immutable HTTP request."""
        parsed_base = urlsplit(self.settings.sec_base_url)
        base_path = parsed_base.path.rstrip("/")
        final_path = f"{base_path}{request.path}"
        query = urlencode(sorted(request.query.items()))
        url = urlunsplit(
            (
                parsed_base.scheme,
                parsed_base.netloc,
                final_path,
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
