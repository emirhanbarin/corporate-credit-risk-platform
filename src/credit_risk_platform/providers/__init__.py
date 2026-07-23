"""Transport-independent provider contracts."""

from credit_risk_platform.providers.http import (
    HttpRequest,
    HttpResponse,
    HttpTransport,
)
from credit_risk_platform.providers.rate_limit import (
    RateLimitDecision,
    RateLimitPolicy,
    RateLimitState,
)
from credit_risk_platform.providers.retry import (
    RetryDecision,
    RetryDecisionReason,
    RetryOutcome,
    RetryPolicy,
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
    "RateLimitDecision",
    "RateLimitPolicy",
    "RateLimitState",
    "RetryDecision",
    "RetryDecisionReason",
    "RetryOutcome",
    "RetryPolicy",
    "UrllibHttpTransport",
]
