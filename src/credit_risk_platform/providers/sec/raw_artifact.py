"""Pure in-memory preservation of exact SEC response bytes and provenance."""

from __future__ import annotations

import hashlib
import string
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Self

from credit_risk_platform.providers.http import HttpResponse

_SHA256_HEX_LENGTH = 64
_LOWERCASE_HEX_DIGITS = frozenset(string.hexdigits.lower())


class SecRawArtifactError(ValueError):
    """Raised when SEC raw-artifact input fails safe validation."""

    __slots__ = ()
    _message = "SEC raw artifact input is invalid."

    def __init__(self) -> None:
        super().__init__(self._message)


class SecSource(str, Enum):
    """A finite logical SEC source identity without request-location metadata."""

    COMPANY_TICKERS = "company_tickers"
    COMPANY_FACTS = "company_facts"

    @classmethod
    def _missing_(cls, _value: object) -> None:
        raise SecRawArtifactError

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True, init=False)
class SecSha256:
    """A canonical lowercase SHA-256 hexadecimal digest."""

    value: str

    def __init__(self, value: str) -> None:
        if (
            not isinstance(value, str)
            or len(value) != _SHA256_HEX_LENGTH
            or value != value.lower()
            or any(character not in _LOWERCASE_HEX_DIGITS for character in value)
        ):
            raise SecRawArtifactError
        object.__setattr__(self, "value", value)

    @classmethod
    def from_bytes(cls, body: bytes) -> Self:
        """Calculate SHA-256 from the supplied byte-identical content."""
        if not isinstance(body, bytes):
            raise SecRawArtifactError
        return cls(hashlib.sha256(body).hexdigest())

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True, init=False)
class SecRawArtifact:
    """Exact SEC response bytes with deterministic in-memory provenance.

    Construction derives the digest and byte length from ``body`` and normalizes
    the caller-supplied aware retrieval timestamp to UTC. Empty bodies are valid
    evidence even when a later parser would reject them. This model performs no
    parsing, persistence, serialization, retrieval, or clock access.
    """

    source: SecSource
    retrieved_at: datetime
    body: bytes = field(repr=False)
    sha256: SecSha256
    byte_length: int

    def __init__(
        self,
        *,
        source: SecSource,
        retrieved_at: datetime,
        body: bytes,
    ) -> None:
        if not isinstance(source, SecSource) or not isinstance(body, bytes):
            raise SecRawArtifactError

        normalized_timestamp = _normalize_utc(retrieved_at)
        digest = SecSha256.from_bytes(body)

        object.__setattr__(self, "source", source)
        object.__setattr__(self, "retrieved_at", normalized_timestamp)
        object.__setattr__(self, "body", body)
        object.__setattr__(self, "sha256", digest)
        object.__setattr__(self, "byte_length", len(body))


def preserve_sec_response(
    response: HttpResponse,
    *,
    source: SecSource,
    retrieved_at: datetime,
) -> SecRawArtifact:
    """Preserve exact response bytes with explicit source and UTC retrieval time.

    The response must already have passed the caller's status interpretation.
    Only its immutable body is retained; no HTTP metadata is copied or inspected.
    """
    if not isinstance(response, HttpResponse):
        raise SecRawArtifactError
    return SecRawArtifact(
        source=source,
        retrieved_at=retrieved_at,
        body=response.body,
    )


def _normalize_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise SecRawArtifactError
    try:
        if value.utcoffset() is None:
            raise SecRawArtifactError
        return value.astimezone(timezone.utc)
    except SecRawArtifactError:
        raise
    except Exception:
        raise SecRawArtifactError from None
