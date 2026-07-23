"""Pure parsing and lookup for the SEC ``company_tickers.json`` document.

This module validates raw UTF-8 JSON bytes into immutable ticker records. It does
not retrieve or preserve the upstream document. Tickers are normalized by trimming
surrounding ASCII spaces and applying ``str.upper``; internal punctuation is never
rewritten. Duplicate normalized tickers invalidate the complete document.
"""

from __future__ import annotations

import json
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import NoReturn

_MAX_CIK_INTEGER = 9_999_999_999
_MAX_TICKER_LENGTH = 32
_MAX_TITLE_LENGTH = 512
_REQUIRED_RECORD_FIELDS = frozenset({"cik_str", "ticker", "title"})
_DECODE_FAILURE = object()


class SecTickerMappingError(ValueError):
    """Raised when an SEC ticker-mapping document fails validation."""

    __slots__ = ()
    _message = "SEC ticker mapping document is invalid."

    def __init__(self) -> None:
        super().__init__(self._message)


class SecTickerNotFoundError(LookupError):
    """Raised when a ticker is absent from a valid local catalog."""

    __slots__ = ()
    _message = "Ticker was not present in the SEC ticker mapping."

    def __init__(self) -> None:
        super().__init__(self._message)


@dataclass(frozen=True, slots=True, init=False)
class SecCik:
    """An SEC Central Index Key stored as exactly ten decimal digits."""

    value: str

    def __init__(self, source_value: int) -> None:
        if (
            isinstance(source_value, bool)
            or not isinstance(source_value, int)
            or not 1 <= source_value <= _MAX_CIK_INTEGER
        ):
            raise ValueError("CIK must be a positive integer of at most ten digits.")
        object.__setattr__(self, "value", f"{source_value:010d}")

    @property
    def integer(self) -> int:
        """Return the unambiguous integer form of the CIK."""
        return int(self.value)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class SecTickerRecord:
    """One validated SEC ticker, canonical CIK, and conformed company title.

    Tickers are limited to 32 characters and titles to 512 characters. These
    conservative safety bounds remain broad enough to avoid prescribing an
    exchange-specific ticker grammar.
    """

    ticker: str
    cik: SecCik
    title: str

    def __post_init__(self) -> None:
        ticker = _normalize_ticker(self.ticker)
        if not isinstance(self.cik, SecCik):
            raise ValueError("cik must be a SecCik.")
        title = _normalize_title(self.title)

        object.__setattr__(self, "ticker", ticker)
        object.__setattr__(self, "title", title)


@dataclass(frozen=True, slots=True, init=False)
class SecTickerCatalog:
    """An immutable, deterministically ordered local SEC ticker index.

    ``find`` returns ``None`` for ordinary local absence. ``require`` raises
    ``SecTickerNotFoundError`` without implying that an HTTP 404 occurred.
    """

    records: tuple[SecTickerRecord, ...]
    _index: MappingProxyType[str, SecTickerRecord] = field(repr=False)

    def __init__(self, records: Iterable[SecTickerRecord]) -> None:
        try:
            copied = tuple(records)
        except TypeError:
            raise ValueError(
                "records must be an iterable of SecTickerRecord."
            ) from None

        index: dict[str, SecTickerRecord] = {}
        for record in copied:
            if not isinstance(record, SecTickerRecord):
                raise ValueError("records must contain only SecTickerRecord values.")
            if record.ticker in index:
                raise ValueError("records must have unique normalized tickers.")
            index[record.ticker] = record

        ordered = tuple(sorted(copied, key=lambda record: record.ticker))
        ordered_index = {record.ticker: record for record in ordered}
        object.__setattr__(self, "records", ordered)
        object.__setattr__(self, "_index", MappingProxyType(ordered_index))

    def find(self, ticker: str) -> SecTickerRecord | None:
        """Return the stored record for a normalized ticker, or ``None``."""
        normalized = _normalize_ticker(ticker)
        return self._index.get(normalized)

    def require(self, ticker: str) -> SecTickerRecord:
        """Return a stored record or raise a safe local-absence error."""
        record = self.find(ticker)
        if record is None:
            raise SecTickerNotFoundError
        return record


def parse_sec_ticker_mapping(body: bytes) -> SecTickerCatalog:
    """Parse raw SEC ticker-mapping bytes without retrieval or persistence.

    Input must be non-empty strict UTF-8 JSON. The top level must be a non-empty
    object whose values contain integer ``cik_str``, string ``ticker``, and string
    ``title`` fields. Unknown record fields are ignored. One malformed record or
    duplicate normalized ticker invalidates the entire document.
    """
    if not isinstance(body, bytes) or not body:
        raise SecTickerMappingError

    decoded = _decode_json(body)
    if decoded is _DECODE_FAILURE or not isinstance(decoded, dict) or not decoded:
        raise SecTickerMappingError

    records: list[SecTickerRecord] = []
    normalized_tickers: set[str] = set()
    for source_record in decoded.values():
        record = _parse_record(source_record)
        if record is None or record.ticker in normalized_tickers:
            raise SecTickerMappingError
        normalized_tickers.add(record.ticker)
        records.append(record)

    return SecTickerCatalog(records)


def _decode_json(body: bytes) -> object:
    try:
        text = body.decode("utf-8")
        return json.loads(
            text,
            object_pairs_hook=_object_from_pairs,
            parse_constant=_reject_json_constant,
        )
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        _InvalidJsonStructureError,
        RecursionError,
    ):
        return _DECODE_FAILURE


def _object_from_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _InvalidJsonStructureError
        result[key] = value
    return result


def _reject_json_constant(_value: str) -> NoReturn:
    raise _InvalidJsonStructureError


def _parse_record(source_record: object) -> SecTickerRecord | None:
    if not isinstance(source_record, dict):
        return None
    if not _REQUIRED_RECORD_FIELDS.issubset(source_record):
        return None

    cik_value = source_record["cik_str"]
    ticker = source_record["ticker"]
    title = source_record["title"]
    if (
        isinstance(cik_value, bool)
        or not isinstance(cik_value, int)
        or not isinstance(ticker, str)
        or not isinstance(title, str)
    ):
        return None

    try:
        return SecTickerRecord(
            ticker=ticker,
            cik=SecCik(cik_value),
            title=title,
        )
    except ValueError:
        return None


def _normalize_ticker(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("ticker must be a string.")
    normalized = value.strip(" ").upper()
    if not normalized or len(normalized) > _MAX_TICKER_LENGTH:
        raise ValueError("ticker must have a valid length.")
    if any(character.isspace() or _is_control(character) for character in normalized):
        raise ValueError("ticker must not contain whitespace or control characters.")
    if "," in normalized or ";" in normalized:
        raise ValueError("ticker must identify exactly one symbol.")
    return normalized


def _normalize_title(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("title must be a string.")
    normalized = value.strip(" ")
    if not normalized or len(normalized) > _MAX_TITLE_LENGTH:
        raise ValueError("title must have a valid length.")
    if any(_is_control(character) for character in normalized):
        raise ValueError("title must not contain control characters.")
    return normalized


def _is_control(character: str) -> bool:
    return unicodedata.category(character) == "Cc"


class _InvalidJsonStructureError(ValueError):
    __slots__ = ()
