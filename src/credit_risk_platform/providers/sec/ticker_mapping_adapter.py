"""Retrieval adapter for the official SEC hosted ticker-mapping file."""

from __future__ import annotations

from dataclasses import dataclass, field

from credit_risk_platform.providers.sec.client import SecClient
from credit_risk_platform.providers.sec.models import SecRequest
from credit_risk_platform.providers.sec.ticker_mapping import (
    SecTickerCatalog,
    parse_sec_ticker_mapping,
)

_TICKER_MAPPING_PATH = "/files/company_tickers.json"


@dataclass(frozen=True, slots=True, init=False)
class SecTickerMappingAdapter:
    """Retrieve and parse the official SEC ticker mapping without retaining it.

    The injected client must use a builder configured with the SEC hosted-files
    authority. This adapter owns only the fixed relative endpoint, delegates all
    request orchestration to ``SecClient``, and delegates all document validation
    to ``parse_sec_ticker_mapping``. It performs no lookup, caching, or persistence.
    """

    _client: SecClient = field(repr=False)

    def __init__(self, client: SecClient) -> None:
        object.__setattr__(self, "_client", client)

    def fetch(self) -> SecTickerCatalog:
        """Retrieve and parse one fresh immutable SEC ticker catalog."""
        request = SecRequest(path=_TICKER_MAPPING_PATH, query={})
        response = self._client.send(request)
        return parse_sec_ticker_mapping(response.body)
