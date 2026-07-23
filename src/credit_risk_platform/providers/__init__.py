"""Transport-independent provider contracts."""

from credit_risk_platform.providers.http import (
    HttpRequest,
    HttpResponse,
    HttpTransport,
)
from credit_risk_platform.providers.urllib_transport import (
    HttpResponseTooLargeError,
    HttpTimeoutError,
    HttpTransportError,
    UrllibHttpTransport,
)

__all__ = [
    "HttpRequest",
    "HttpResponse",
    "HttpResponseTooLargeError",
    "HttpTimeoutError",
    "HttpTransport",
    "HttpTransportError",
    "UrllibHttpTransport",
]
