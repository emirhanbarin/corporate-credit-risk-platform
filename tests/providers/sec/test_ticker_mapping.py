"""Tests for pure SEC ticker-mapping parsing and local resolution."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError

import pytest

import credit_risk_platform.providers as generic_providers
import credit_risk_platform.providers.sec as sec_providers
from credit_risk_platform.providers.sec import (
    SecCik,
    SecTickerCatalog,
    SecTickerMappingError,
    SecTickerNotFoundError,
    SecTickerRecord,
    parse_sec_ticker_mapping,
)


def _record(
    *,
    cik_str: object = 789019,
    ticker: object = "MSFT",
    title: object = "MICROSOFT CORP",
    **extra: object,
) -> dict[str, object]:
    return {
        "cik_str": cik_str,
        "ticker": ticker,
        "title": title,
        **extra,
    }


def _body(records: dict[str, object]) -> bytes:
    return json.dumps(records, separators=(",", ":")).encode()


@pytest.mark.parametrize(
    ("source_value", "canonical"),
    [
        (1, "0000000001"),
        (789019, "0000789019"),
        (9_999_999_999, "9999999999"),
    ],
)
def test_cik_canonicalizes_valid_integer_values(
    source_value: int,
    canonical: str,
) -> None:
    cik = SecCik(source_value)

    assert cik.value == canonical
    assert cik.integer == source_value
    assert str(cik) == canonical


@pytest.mark.parametrize(
    "source_value",
    [0, -1, 10_000_000_000, True, False, 789019.0, "789019", None],
)
def test_cik_rejects_invalid_or_coerced_values(source_value: object) -> None:
    with pytest.raises(
        ValueError,
        match="CIK must be a positive integer of at most ten digits",
    ):
        SecCik(source_value)  # type: ignore[arg-type]


def test_cik_is_frozen() -> None:
    cik = SecCik(789019)

    with pytest.raises(FrozenInstanceError):
        cik.value = "0000000001"  # type: ignore[misc]


def test_record_normalizes_ticker_and_preserves_title_punctuation() -> None:
    record = SecTickerRecord(
        ticker=" msft ",
        cik=SecCik(789019),
        title=" MICROSOFT CORP. (WASHINGTON) ",
    )

    assert record.ticker == "MSFT"
    assert record.cik == SecCik(789019)
    assert record.title == "MICROSOFT CORP. (WASHINGTON)"


@pytest.mark.parametrize("ticker", [None, 1, True])
def test_record_ticker_must_be_a_string(ticker: object) -> None:
    with pytest.raises(ValueError, match="ticker must be a string"):
        SecTickerRecord(
            ticker=ticker,  # type: ignore[arg-type]
            cik=SecCik(1),
            title="SYNTHETIC COMPANY",
        )


@pytest.mark.parametrize(
    "ticker",
    [
        "",
        "   ",
        "\tMSFT",
        "MS FT",
        "MS\nFT",
        "MS\x00FT",
        "MSFT,AAPL",
        "MSFT;AAPL",
        "A" * 33,
    ],
)
def test_record_rejects_unsafe_ticker_strings(ticker: str) -> None:
    with pytest.raises(ValueError, match="ticker"):
        SecTickerRecord(
            ticker=ticker,
            cik=SecCik(1),
            title="SYNTHETIC COMPANY",
        )


def test_record_requires_cik_value_object() -> None:
    with pytest.raises(ValueError, match="cik must be a SecCik"):
        SecTickerRecord(
            ticker="TEST",
            cik=1,  # type: ignore[arg-type]
            title="SYNTHETIC COMPANY",
        )


@pytest.mark.parametrize("title", [None, 1, True])
def test_record_title_must_be_a_string(title: object) -> None:
    with pytest.raises(ValueError, match="title must be a string"):
        SecTickerRecord(
            ticker="TEST",
            cik=SecCik(1),
            title=title,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "title",
    ["", "   ", "BAD\nTITLE", "BAD\rTITLE", "BAD\x00TITLE", "A" * 513],
)
def test_record_rejects_unsafe_title_strings(title: str) -> None:
    with pytest.raises(ValueError, match="title"):
        SecTickerRecord(ticker="TEST", cik=SecCik(1), title=title)


def test_record_is_frozen() -> None:
    record = SecTickerRecord("MSFT", SecCik(789019), "MICROSOFT CORP")

    with pytest.raises(FrozenInstanceError):
        record.title = "CHANGED"  # type: ignore[misc]


def test_parse_one_microsoft_record_and_resolve_canonical_cik() -> None:
    source = _body({"0": _record()})

    catalog = parse_sec_ticker_mapping(source)
    resolved = catalog.require("MSFT")

    assert resolved.ticker == "MSFT"
    assert resolved.cik.value == "0000789019"
    assert resolved.title == "MICROSOFT CORP"
    assert catalog.find("missing") is None


def test_parse_multiple_non_consecutive_records_in_deterministic_order() -> None:
    source = _body(
        {
            "91": _record(cik_str=320193, ticker="AAPL", title="APPLE INC."),
            "7": _record(),
            "2048": _record(cik_str=1652044, ticker="GOOG", title="ALPHABET INC."),
        }
    )

    catalog = parse_sec_ticker_mapping(source)

    assert tuple(record.ticker for record in catalog.records) == (
        "AAPL",
        "GOOG",
        "MSFT",
    )


def test_top_level_key_order_does_not_affect_catalog() -> None:
    first = parse_sec_ticker_mapping(
        _body(
            {
                "8": _record(),
                "2": _record(cik_str=320193, ticker="AAPL", title="APPLE INC."),
            }
        )
    )
    second = parse_sec_ticker_mapping(
        _body(
            {
                "2": _record(cik_str=320193, ticker="AAPL", title="APPLE INC."),
                "8": _record(),
            }
        )
    )

    assert first == second
    assert first.records == second.records


def test_unknown_record_fields_are_ignored_for_forward_compatibility() -> None:
    catalog = parse_sec_ticker_mapping(
        _body(
            {
                "0": _record(
                    exchange="SYNTHETIC",
                    nested={"ignored": ["value"]},
                )
            }
        )
    )

    assert catalog.records == (
        SecTickerRecord("MSFT", SecCik(789019), "MICROSOFT CORP"),
    )
    assert not hasattr(catalog.records[0], "exchange")


def test_parser_does_not_mutate_or_retain_raw_input() -> None:
    source = _body({"0": _record()})
    original = bytes(source)

    catalog = parse_sec_ticker_mapping(source)

    assert source == original
    assert not hasattr(catalog, "body")
    assert not hasattr(catalog, "raw_json")
    assert not hasattr(catalog.records[0], "source")


def test_mixed_case_source_ticker_normalizes_and_title_spelling_is_preserved() -> None:
    catalog = parse_sec_ticker_mapping(
        _body(
            {
                "0": _record(
                    ticker="mSfT",
                    title="Microsoft Corp., Class A",
                )
            }
        )
    )

    record = catalog.require("msft")
    assert record.ticker == "MSFT"
    assert record.title == "Microsoft Corp., Class A"


@pytest.mark.parametrize(
    "body",
    [
        b"",
        b"\xff\xfe",
        b"{malformed",
        b'{"0":null} trailing',
        b"null",
        b"[]",
        b'"string"',
        b"42",
        b"{}",
        b'{"0":{"cik_str":NaN,"ticker":"TEST","title":"TITLE"}}',
        b'{"0":{},"0":{}}',
    ],
)
def test_invalid_top_level_or_json_document_is_rejected(body: bytes) -> None:
    with pytest.raises(
        SecTickerMappingError,
        match="SEC ticker mapping document is invalid",
    ):
        parse_sec_ticker_mapping(body)


def test_excessive_json_nesting_is_rejected_safely() -> None:
    body = ("[" * 2_000 + "0" + "]" * 2_000).encode()

    with pytest.raises(SecTickerMappingError):
        parse_sec_ticker_mapping(body)


@pytest.mark.parametrize("body", [None, bytearray(b"{}"), memoryview(b"{}"), "{}"])
def test_parser_accepts_exactly_bytes(body: object) -> None:
    with pytest.raises(SecTickerMappingError):
        parse_sec_ticker_mapping(body)  # type: ignore[arg-type]


@pytest.mark.parametrize("record_value", [None, [], "record", 1, True])
def test_non_object_record_invalidates_document(record_value: object) -> None:
    with pytest.raises(SecTickerMappingError):
        parse_sec_ticker_mapping(_body({"0": record_value}))


@pytest.mark.parametrize("missing_field", ["cik_str", "ticker", "title"])
def test_missing_required_field_invalidates_document(missing_field: str) -> None:
    record = _record()
    del record[missing_field]

    with pytest.raises(SecTickerMappingError):
        parse_sec_ticker_mapping(_body({"0": record}))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("cik_str", None),
        ("cik_str", True),
        ("cik_str", 789019.0),
        ("cik_str", "789019"),
        ("ticker", None),
        ("ticker", 1),
        ("title", None),
        ("title", 1),
    ],
)
def test_null_or_wrong_required_field_type_invalidates_document(
    field: str,
    value: object,
) -> None:
    record = _record()
    record[field] = value

    with pytest.raises(SecTickerMappingError):
        parse_sec_ticker_mapping(_body({"0": record}))


@pytest.mark.parametrize("cik_value", [0, -1, 10_000_000_000])
def test_invalid_integer_cik_invalidates_document(cik_value: int) -> None:
    with pytest.raises(SecTickerMappingError):
        parse_sec_ticker_mapping(_body({"0": _record(cik_str=cik_value)}))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("ticker", ""),
        ("ticker", "   "),
        ("ticker", "BAD\rTICKER"),
        ("ticker", "BAD\nTICKER"),
        ("ticker", "BAD\x1fTICKER"),
        ("ticker", "T" * 33),
        ("title", ""),
        ("title", "   "),
        ("title", "BAD\rTITLE"),
        ("title", "BAD\nTITLE"),
        ("title", "BAD\x1fTITLE"),
        ("title", "T" * 513),
    ],
)
def test_invalid_required_string_invalidates_document(
    field: str,
    value: str,
) -> None:
    record = _record()
    record[field] = value

    with pytest.raises(SecTickerMappingError):
        parse_sec_ticker_mapping(_body({"0": record}))


def test_one_malformed_record_invalidates_otherwise_valid_document() -> None:
    body = _body(
        {
            "0": _record(),
            "1": _record(cik_str=320193, ticker="", title="APPLE INC."),
        }
    )

    with pytest.raises(SecTickerMappingError):
        parse_sec_ticker_mapping(body)


@pytest.mark.parametrize(
    "duplicate",
    [
        _record(),
        _record(ticker="msft"),
        _record(cik_str=320193),
        _record(title="DIFFERENT TITLE"),
    ],
)
def test_any_duplicate_normalized_ticker_invalidates_document(
    duplicate: dict[str, object],
) -> None:
    body = _body({"first": _record(), "second": duplicate})

    with pytest.raises(SecTickerMappingError):
        parse_sec_ticker_mapping(body)


def test_duplicate_error_is_independent_of_source_order() -> None:
    first = _record()
    conflict = _record(cik_str=320193, ticker="msft", title="DIFFERENT TITLE")

    errors: list[type[BaseException]] = []
    for records in (
        {"first": first, "second": conflict},
        {"second": conflict, "first": first},
    ):
        with pytest.raises(SecTickerMappingError) as exception_info:
            parse_sec_ticker_mapping(_body(records))
        errors.append(type(exception_info.value))

    assert errors == [SecTickerMappingError, SecTickerMappingError]


def test_catalog_defensively_copies_sorts_and_preserves_record_identity() -> None:
    microsoft = SecTickerRecord("MSFT", SecCik(789019), "MICROSOFT CORP")
    apple = SecTickerRecord("AAPL", SecCik(320193), "APPLE INC.")
    source = [microsoft, apple]

    catalog = SecTickerCatalog(source)
    source.clear()

    assert catalog.records == (apple, microsoft)
    assert catalog.find("AAPL") is apple
    assert catalog.find("MSFT") is microsoft


def test_catalog_and_public_records_are_immutable() -> None:
    catalog = SecTickerCatalog(
        [SecTickerRecord("MSFT", SecCik(789019), "MICROSOFT CORP")]
    )

    with pytest.raises(FrozenInstanceError):
        catalog.records = ()  # type: ignore[misc]
    with pytest.raises(TypeError):
        catalog._index["MSFT"] = SecTickerRecord(  # type: ignore[index]
            "OTHER",
            SecCik(1),
            "OTHER",
        )
    with pytest.raises(FrozenInstanceError):
        catalog.records[0].ticker = "OTHER"  # type: ignore[misc]


def test_empty_catalog_is_valid_for_explicit_local_absence() -> None:
    catalog = SecTickerCatalog([])

    assert catalog.records == ()
    assert catalog.find("MSFT") is None


@pytest.mark.parametrize("records", [None, 1, True])
def test_catalog_requires_an_iterable(records: object) -> None:
    with pytest.raises(ValueError, match="records must be an iterable"):
        SecTickerCatalog(records)  # type: ignore[arg-type]


def test_catalog_rejects_non_record_members() -> None:
    with pytest.raises(ValueError, match="only SecTickerRecord"):
        SecTickerCatalog([object()])  # type: ignore[list-item]


def test_catalog_rejects_duplicate_normalized_tickers_without_overwrite() -> None:
    first = SecTickerRecord("MSFT", SecCik(789019), "MICROSOFT CORP")
    second = SecTickerRecord("msft", SecCik(320193), "DIFFERENT")

    with pytest.raises(ValueError, match="unique normalized tickers"):
        SecTickerCatalog([first, second])


@pytest.mark.parametrize("lookup", ["MSFT", "msft", " MsFt "])
def test_lookup_normalizes_case_and_surrounding_ascii_spaces(lookup: str) -> None:
    record = SecTickerRecord("MSFT", SecCik(789019), "MICROSOFT CORP")
    catalog = SecTickerCatalog([record])

    assert catalog.find(lookup) is record
    assert catalog.require(lookup) is record


@pytest.mark.parametrize(
    "lookup",
    ["", "   ", "\t", "MS FT", "MS\nFT", "MSFT,AAPL", "MSFT;AAPL"],
)
def test_lookup_rejects_empty_or_unsafe_strings(lookup: str) -> None:
    catalog = SecTickerCatalog([])

    with pytest.raises(ValueError, match="ticker"):
        catalog.find(lookup)


@pytest.mark.parametrize("lookup", [None, 1, True, ["MSFT"]])
def test_lookup_rejects_non_strings(lookup: object) -> None:
    catalog = SecTickerCatalog([])

    with pytest.raises(ValueError, match="ticker must be a string"):
        catalog.find(lookup)  # type: ignore[arg-type]


def test_lookup_preserves_punctuation_without_aliasing() -> None:
    dot_record = SecTickerRecord("BRK.B", SecCik(1067983), "BERKSHIRE HATHAWAY")
    catalog = SecTickerCatalog([dot_record])

    assert catalog.find("brk.b") is dot_record
    assert catalog.find("BRK-B") is None
    assert catalog.find("BRK/B") is None


def test_require_raises_safe_local_absence_not_http_not_found() -> None:
    catalog = SecTickerCatalog([])
    requested_marker = "UNKNOWN_TICKER_MARKER_6A21"

    with pytest.raises(SecTickerNotFoundError) as exception_info:
        catalog.require(requested_marker)

    error = exception_info.value
    assert str(error) == "Ticker was not present in the SEC ticker mapping."
    assert requested_marker not in str(error)
    assert requested_marker not in repr(error)
    assert not isinstance(error, sec_providers.SecNotFoundError)


def test_mapping_error_exposes_no_malformed_source_content_or_context() -> None:
    source_marker = "MALFORMED_SOURCE_MARKER_7B32"
    body = f'{{"{source_marker}":'.encode()

    with pytest.raises(SecTickerMappingError) as exception_info:
        parse_sec_ticker_mapping(body)

    error = exception_info.value
    assert str(error) == "SEC ticker mapping document is invalid."
    assert source_marker not in str(error)
    assert source_marker not in repr(error)
    assert vars(error) == {}
    assert error.__cause__ is None
    assert error.__context__ is None


def test_catalog_representation_contains_only_validated_business_records() -> None:
    catalog = parse_sec_ticker_mapping(_body({"0": _record()}))

    representation = repr(catalog)
    assert "SecTickerRecord" in representation
    assert "_index" not in representation
    assert "raw_json" not in representation
    assert "HttpResponse" not in representation


def test_public_exports_are_sec_specific() -> None:
    expected = {
        "SecCik": SecCik,
        "SecTickerCatalog": SecTickerCatalog,
        "SecTickerMappingError": SecTickerMappingError,
        "SecTickerNotFoundError": SecTickerNotFoundError,
        "SecTickerRecord": SecTickerRecord,
        "parse_sec_ticker_mapping": parse_sec_ticker_mapping,
    }

    for name, value in expected.items():
        assert getattr(sec_providers, name) is value
        assert name in sec_providers.__all__
        assert name not in generic_providers.__all__
        assert not hasattr(generic_providers, name)
