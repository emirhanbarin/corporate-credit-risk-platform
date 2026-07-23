"""Public SEC provider contracts."""

from credit_risk_platform.providers.sec.client import SecClient
from credit_risk_platform.providers.sec.errors import (
    SecNotFoundError,
    SecProviderError,
    SecRateLimitError,
    SecRequestError,
    SecResponseError,
    SecServerError,
    SecTimeoutError,
    SecTransportError,
)
from credit_risk_platform.providers.sec.models import SecRequest
from credit_risk_platform.providers.sec.request_builder import SecRequestBuilder
from credit_risk_platform.providers.sec.response_mapper import validate_sec_response
from credit_risk_platform.providers.sec.ticker_mapping import (
    SecCik,
    SecTickerCatalog,
    SecTickerMappingError,
    SecTickerNotFoundError,
    SecTickerRecord,
    parse_sec_ticker_mapping,
)
from credit_risk_platform.providers.sec.ticker_mapping_adapter import (
    SecTickerMappingAdapter,
)

__all__ = [
    "SecCik",
    "SecClient",
    "SecNotFoundError",
    "SecProviderError",
    "SecRateLimitError",
    "SecRequest",
    "SecRequestBuilder",
    "SecRequestError",
    "SecResponseError",
    "SecServerError",
    "SecTickerCatalog",
    "SecTickerMappingAdapter",
    "SecTickerMappingError",
    "SecTickerNotFoundError",
    "SecTickerRecord",
    "SecTimeoutError",
    "SecTransportError",
    "parse_sec_ticker_mapping",
    "validate_sec_response",
]
