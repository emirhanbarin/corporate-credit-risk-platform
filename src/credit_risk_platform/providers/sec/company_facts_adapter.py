"""Retrieval and raw provenance adapter for official SEC Company Facts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from credit_risk_platform.providers.sec.client import SecClient
from credit_risk_platform.providers.sec.models import SecRequest
from credit_risk_platform.providers.sec.raw_artifact import (
    SecRawArtifact,
    SecSource,
    preserve_sec_response,
)
from credit_risk_platform.providers.sec.ticker_mapping import SecCik

_COMPANY_FACTS_PATH_PREFIX = "/api/xbrl/companyfacts/CIK"
_COMPANY_FACTS_PATH_SUFFIX = ".json"


@dataclass(frozen=True, slots=True, init=False)
class SecCompanyFactsAdapter:
    """Retrieve Company Facts and immediately preserve exact response bytes.

    The injected ``SecClient`` must use the SEC data authority. The adapter builds
    only the fixed official relative endpoint from a canonical ``SecCik`` and
    passes the caller-supplied retrieval timestamp unchanged to the provenance
    boundary. It performs no JSON parsing, persistence, or fact selection.
    """

    _client: SecClient = field(repr=False)

    def __init__(self, client: SecClient) -> None:
        object.__setattr__(self, "_client", client)

    def fetch(
        self,
        cik: SecCik,
        *,
        retrieved_at: datetime,
    ) -> SecRawArtifact:
        """Retrieve one Company Facts response as an immutable raw artifact."""
        if not isinstance(cik, SecCik):
            raise ValueError("cik must be a SecCik.")

        request = SecRequest(
            path=(f"{_COMPANY_FACTS_PATH_PREFIX}{cik}{_COMPANY_FACTS_PATH_SUFFIX}"),
            query={},
        )
        response = self._client.send(request)
        return preserve_sec_response(
            response,
            source=SecSource.COMPANY_FACTS,
            retrieved_at=retrieved_at,
        )
