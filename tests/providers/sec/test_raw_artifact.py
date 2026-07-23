"""Tests for pure in-memory SEC raw-response provenance."""

from __future__ import annotations

import hashlib
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone, tzinfo

import pytest

import credit_risk_platform.providers as generic_providers
import credit_risk_platform.providers.sec as sec_providers
import credit_risk_platform.providers.sec.raw_artifact as raw_artifact_module
from credit_risk_platform.providers import HttpResponse
from credit_risk_platform.providers.sec import (
    SecRawArtifact,
    SecRawArtifactError,
    SecSha256,
    SecSource,
    preserve_sec_response,
)

_UTC_TIMESTAMP = datetime(2026, 7, 23, 12, 34, 56, 789012, tzinfo=timezone.utc)


def _response(
    body: bytes,
    *,
    status_code: int = 200,
    headers: dict[str, str] | None = None,
) -> HttpResponse:
    return HttpResponse(
        status_code=status_code,
        headers={} if headers is None else headers,
        body=body,
    )


def _preserve(
    body: bytes,
    *,
    source: SecSource = SecSource.COMPANY_FACTS,
    retrieved_at: datetime = _UTC_TIMESTAMP,
) -> SecRawArtifact:
    return preserve_sec_response(
        _response(body),
        source=source,
        retrieved_at=retrieved_at,
    )


def test_source_identities_have_stable_distinct_canonical_values() -> None:
    assert tuple(SecSource) == (
        SecSource.COMPANY_TICKERS,
        SecSource.COMPANY_FACTS,
    )
    assert SecSource.COMPANY_TICKERS.value == "company_tickers"
    assert SecSource.COMPANY_FACTS.value == "company_facts"
    assert str(SecSource.COMPANY_TICKERS) == "company_tickers"
    assert str(SecSource.COMPANY_FACTS) == "company_facts"
    assert SecSource.COMPANY_TICKERS != SecSource.COMPANY_FACTS


def test_source_representation_contains_no_request_identity() -> None:
    representation = repr(SecSource.COMPANY_FACTS)

    assert "https://" not in representation
    assert "@" not in representation
    assert "?" not in representation


def test_source_rejects_unknown_direct_value_with_safe_error() -> None:
    marker = "ARBITRARY_SOURCE_ENUM_MARKER_1A2B"

    with pytest.raises(SecRawArtifactError) as exception_info:
        SecSource(marker)

    _assert_safe_error(exception_info.value, marker)


def test_preservation_rejects_arbitrary_source_string_with_safe_error() -> None:
    marker = "ARBITRARY_SOURCE_INPUT_MARKER_2B3C"

    with pytest.raises(SecRawArtifactError) as exception_info:
        preserve_sec_response(
            _response(b"body"),
            source=marker,  # type: ignore[arg-type]
            retrieved_at=_UTC_TIMESTAMP,
        )

    _assert_safe_error(exception_info.value, marker)


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        (
            b"",
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        ),
        (
            b"abc",
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
        ),
        (
            b"\x00\xffSEC\x80",
            "5d4db728b094def2fbce9322f73996a2482a9b429d1a1f3bd3801c1e36feb37c",
        ),
    ],
)
def test_sha256_known_vectors(body: bytes, expected: str) -> None:
    digest = SecSha256.from_bytes(body)

    assert digest.value == expected
    assert str(digest) == expected
    assert len(digest.value) == 64
    assert digest.value == digest.value.lower()
    assert digest == SecSha256(expected)
    assert not hasattr(digest, "body")


def test_different_bodies_produce_different_digests() -> None:
    assert SecSha256.from_bytes(b"first") != SecSha256.from_bytes(b"second")


@pytest.mark.parametrize(
    "value",
    [
        "",
        "0" * 63,
        "0" * 65,
        "A" * 64,
        "z" * 64,
        " " + ("0" * 63),
        ("0" * 63) + "\n",
        123,
        True,
        None,
    ],
)
def test_sha256_rejects_invalid_direct_values_with_safe_error(
    value: object,
) -> None:
    with pytest.raises(SecRawArtifactError) as exception_info:
        SecSha256(value)  # type: ignore[arg-type]

    assert str(exception_info.value) == "SEC raw artifact input is invalid."
    assert repr(value) not in str(exception_info.value)
    assert repr(value) not in repr(exception_info.value)


@pytest.mark.parametrize("body", [bytearray(b"body"), memoryview(b"body"), "body"])
def test_sha256_from_bytes_requires_immutable_bytes(body: object) -> None:
    with pytest.raises(SecRawArtifactError, match="SEC raw artifact input is invalid"):
        SecSha256.from_bytes(body)  # type: ignore[arg-type]


def test_sha256_is_frozen_and_slotted() -> None:
    digest = SecSha256.from_bytes(b"body")

    assert not hasattr(digest, "__dict__")
    with pytest.raises(FrozenInstanceError):
        digest.value = "0" * 64  # type: ignore[misc]


@pytest.mark.parametrize(
    "body",
    [
        b'{"companyfacts":[]}',
        b"",
        b"\x00\xff\x80binary",
        "Zażółć gęślą jaźń".encode(),
        b"line-one\r\nline-two\r\n",
        b'\xef\xbb\xbf{"bom":true}',
        b' \t\n{"space":true}\r\n ',
    ],
)
def test_preservation_keeps_exact_raw_bytes_and_derives_integrity(
    body: bytes,
) -> None:
    response = _response(
        body,
        headers={"X-Synthetic": "RESPONSE_HEADER_MARKER"},
    )

    artifact = preserve_sec_response(
        response,
        source=SecSource.COMPANY_FACTS,
        retrieved_at=_UTC_TIMESTAMP,
    )

    assert artifact.body is response.body
    assert artifact.body == body
    assert artifact.byte_length == len(body)
    assert artifact.sha256.value == hashlib.sha256(body).hexdigest()
    assert response.body == body
    assert response.headers == {"X-Synthetic": "RESPONSE_HEADER_MARKER"}


def test_empty_body_is_valid_preserved_evidence() -> None:
    artifact = _preserve(b"")

    assert artifact.body == b""
    assert artifact.byte_length == 0
    assert artifact.sha256 == SecSha256.from_bytes(b"")


def test_preservation_does_not_retain_http_metadata() -> None:
    artifact = preserve_sec_response(
        _response(
            b"body",
            status_code=599,
            headers={"X-Synthetic": "HEADER_VALUE_MARKER"},
        ),
        source=SecSource.COMPANY_TICKERS,
        retrieved_at=_UTC_TIMESTAMP,
    )

    assert not hasattr(artifact, "response")
    assert not hasattr(artifact, "status_code")
    assert not hasattr(artifact, "headers")
    assert not hasattr(artifact, "url")
    assert not hasattr(artifact, "query")
    assert not hasattr(artifact, "method")
    assert not hasattr(artifact, "timeout_seconds")
    assert not hasattr(artifact, "metadata")


def test_utc_timestamp_is_accepted_and_microseconds_are_preserved() -> None:
    artifact = _preserve(b"body")

    assert artifact.retrieved_at == _UTC_TIMESTAMP
    assert artifact.retrieved_at.tzinfo is timezone.utc
    assert artifact.retrieved_at.microsecond == 789012


@pytest.mark.parametrize(
    ("supplied", "expected"),
    [
        (
            datetime(
                2026,
                7,
                23,
                14,
                34,
                56,
                789012,
                tzinfo=timezone(timedelta(hours=2)),
            ),
            _UTC_TIMESTAMP,
        ),
        (
            datetime(
                2026,
                7,
                23,
                7,
                34,
                56,
                789012,
                tzinfo=timezone(timedelta(hours=-5)),
            ),
            _UTC_TIMESTAMP,
        ),
    ],
)
def test_offset_timestamp_is_normalized_to_canonical_utc(
    supplied: datetime,
    expected: datetime,
) -> None:
    artifact = _preserve(b"body", retrieved_at=supplied)

    assert artifact.retrieved_at == expected
    assert artifact.retrieved_at.tzinfo is timezone.utc
    assert artifact.retrieved_at.microsecond == supplied.microsecond


def test_equivalent_offset_instants_produce_equal_artifacts() -> None:
    utc = _preserve(b"body")
    offset = _preserve(
        b"body",
        retrieved_at=datetime(
            2026,
            7,
            23,
            14,
            34,
            56,
            789012,
            tzinfo=timezone(timedelta(hours=2)),
        ),
    )

    assert utc == offset


@pytest.mark.parametrize(
    "retrieved_at",
    [
        datetime(2026, 7, 23, 12, 34, 56),
        "2026-07-23T12:34:56Z",
        True,
        None,
    ],
)
def test_invalid_timestamp_values_are_rejected_safely(
    retrieved_at: object,
) -> None:
    marker = "TIMESTAMP_INPUT_MARKER"

    with pytest.raises(SecRawArtifactError) as exception_info:
        preserve_sec_response(
            _response(b"body"),
            source=SecSource.COMPANY_FACTS,
            retrieved_at=retrieved_at,  # type: ignore[arg-type]
        )

    _assert_safe_error(exception_info.value, marker)


class _MissingOffset(tzinfo):
    def utcoffset(self, _value: datetime | None) -> None:
        return None

    def dst(self, _value: datetime | None) -> None:
        return None

    def tzname(self, _value: datetime | None) -> str:
        return "MISSING_OFFSET_MARKER"


class _InvalidOffset(tzinfo):
    def utcoffset(self, _value: datetime | None) -> timedelta:
        return timedelta(days=1)

    def dst(self, _value: datetime | None) -> timedelta:
        return timedelta(0)

    def tzname(self, _value: datetime | None) -> str:
        return "INVALID_OFFSET_MARKER"


class _RaisingOffset(tzinfo):
    def utcoffset(self, _value: datetime | None) -> timedelta:
        raise RuntimeError("PATHOLOGICAL_TIMEZONE_MARKER")

    def dst(self, _value: datetime | None) -> timedelta:
        return timedelta(0)

    def tzname(self, _value: datetime | None) -> str:
        return "RAISING_OFFSET_MARKER"


@pytest.mark.parametrize(
    ("timezone_value", "marker"),
    [
        (_MissingOffset(), "MISSING_OFFSET_MARKER"),
        (_InvalidOffset(), "INVALID_OFFSET_MARKER"),
        (_RaisingOffset(), "PATHOLOGICAL_TIMEZONE_MARKER"),
    ],
)
def test_pathological_timezone_behavior_fails_safely(
    timezone_value: tzinfo,
    marker: str,
) -> None:
    supplied = datetime(2026, 7, 23, tzinfo=timezone_value)

    with pytest.raises(SecRawArtifactError) as exception_info:
        _preserve(b"body", retrieved_at=supplied)

    _assert_safe_error(exception_info.value, marker)
    assert exception_info.value.__cause__ is None


def test_artifact_is_frozen_slotted_and_has_only_contract_fields() -> None:
    artifact = _preserve(b"body")

    assert not hasattr(artifact, "__dict__")
    assert tuple(artifact.__slots__) == (
        "source",
        "retrieved_at",
        "body",
        "sha256",
        "byte_length",
    )
    with pytest.raises(FrozenInstanceError):
        artifact.source = SecSource.COMPANY_TICKERS  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        artifact.retrieved_at = _UTC_TIMESTAMP  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        artifact.body = b"changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        artifact.sha256 = SecSha256.from_bytes(b"changed")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        artifact.byte_length = 100  # type: ignore[misc]


def test_public_construction_cannot_supply_derived_integrity_values() -> None:
    with pytest.raises(TypeError):
        SecRawArtifact(
            source=SecSource.COMPANY_FACTS,
            retrieved_at=_UTC_TIMESTAMP,
            body=b"body",
            sha256=SecSha256.from_bytes(b"different"),  # type: ignore[call-arg]
            byte_length=999,  # type: ignore[call-arg]
        )


@pytest.mark.parametrize(
    ("source", "body"),
    [
        ("company_facts", b"body"),
        (SecSource.COMPANY_FACTS, bytearray(b"body")),
        (SecSource.COMPANY_FACTS, memoryview(b"body")),
    ],
)
def test_direct_artifact_construction_rejects_invalid_types_safely(
    source: object,
    body: object,
) -> None:
    with pytest.raises(SecRawArtifactError, match="SEC raw artifact input is invalid"):
        SecRawArtifact(
            source=source,  # type: ignore[arg-type]
            retrieved_at=_UTC_TIMESTAMP,
            body=body,  # type: ignore[arg-type]
        )


def test_artifact_value_equality_tracks_body_and_provenance() -> None:
    first = _preserve(b"same")
    repeated = _preserve(b"same")
    different_source = _preserve(b"same", source=SecSource.COMPANY_TICKERS)
    different_time = _preserve(
        b"same",
        retrieved_at=_UTC_TIMESTAMP + timedelta(microseconds=1),
    )
    different_body = _preserve(b"Same")

    assert first == repeated
    assert first.sha256 == repeated.sha256
    assert different_source != first
    assert different_source.sha256 == first.sha256
    assert different_time != first
    assert different_time.sha256 == first.sha256
    assert different_body != first
    assert different_body.sha256 != first.sha256


def test_semantically_equivalent_but_byte_different_json_has_distinct_digest() -> None:
    compact = _preserve(b'{"a":1,"b":2}')
    reordered = _preserve(b'{"b":2,"a":1}')
    spaced = _preserve(b'{ "a": 1, "b": 2 }')

    assert compact.sha256 != reordered.sha256
    assert compact.sha256 != spaced.sha256
    assert reordered.sha256 != spaced.sha256


def test_artifact_representation_excludes_raw_body_and_http_markers() -> None:
    body_marker = "RAW_BODY_MARKER_7B91"
    header_marker = "RESPONSE_HEADER_MARKER_8CA2"
    artifact = preserve_sec_response(
        _response(
            f'{{"value":"{body_marker}"}}'.encode(),
            headers={"X-Synthetic": header_marker},
        ),
        source=SecSource.COMPANY_FACTS,
        retrieved_at=_UTC_TIMESTAMP,
    )

    representation = repr(artifact)
    assert body_marker not in representation
    assert header_marker not in representation
    assert "https://" not in representation
    assert artifact.body == f'{{"value":"{body_marker}"}}'.encode()
    assert artifact.sha256.value in representation
    assert str(artifact.byte_length) in representation


def test_preservation_rejects_non_response_without_exposing_object_repr() -> None:
    marker = "RESPONSE_OBJECT_MARKER_9DB3"

    class _NotAResponse:
        def __repr__(self) -> str:
            return marker

    with pytest.raises(SecRawArtifactError) as exception_info:
        preserve_sec_response(
            _NotAResponse(),  # type: ignore[arg-type]
            source=SecSource.COMPANY_FACTS,
            retrieved_at=_UTC_TIMESTAMP,
        )

    _assert_safe_error(exception_info.value, marker)


def test_public_exports_are_sec_specific_and_helpers_remain_private() -> None:
    assert sec_providers.SecSource is SecSource
    assert sec_providers.SecSha256 is SecSha256
    assert sec_providers.SecRawArtifact is SecRawArtifact
    assert sec_providers.SecRawArtifactError is SecRawArtifactError
    assert sec_providers.preserve_sec_response is preserve_sec_response
    assert {
        "SecSource",
        "SecSha256",
        "SecRawArtifact",
        "SecRawArtifactError",
        "preserve_sec_response",
    }.issubset(sec_providers.__all__)

    for name in (
        "SecSource",
        "SecSha256",
        "SecRawArtifact",
        "SecRawArtifactError",
        "preserve_sec_response",
    ):
        assert name not in generic_providers.__all__
        assert not hasattr(generic_providers, name)

    assert "_normalize_utc" not in sec_providers.__all__
    assert not hasattr(sec_providers, "_normalize_utc")
    assert hasattr(raw_artifact_module, "_normalize_utc")


def _assert_safe_error(error: SecRawArtifactError, marker: str) -> None:
    assert str(error) == "SEC raw artifact input is invalid."
    assert marker not in str(error)
    assert marker not in repr(error)
    assert error.args == ("SEC raw artifact input is invalid.",)
