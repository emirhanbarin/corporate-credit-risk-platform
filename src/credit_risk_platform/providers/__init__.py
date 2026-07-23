"""Transport-independent provider contracts."""

from credit_risk_platform.providers.http import (
    HttpRequest,
    HttpResponse,
    HttpTransport,
)

__all__ = ["HttpRequest", "HttpResponse", "HttpTransport"]
