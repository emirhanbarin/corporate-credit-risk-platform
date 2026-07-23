"""Tests for the SEC Company Facts retrieval and provenance adapter."""

from __future__ import annotations

import hashlib
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone, tzinfo
from inspect import signature

import pytest

import credit_risk_platform.providers as generic_providers
import credit_risk_platform.providers.sec as sec_providers
import credit_risk_platform.providers.sec.company_facts_adapter as adapter_module
from credit_risk_platform.config import AppSettings
from credit_risk_platform.providers import (
    HttpRequest,
    HttpResponse,
    RateLimitPolicy,
    RetryPolicy,
)
from credit_risk_platform.providers.sec import (
    SecCik,
    SecClient,
    SecCompanyFactsAdapter,
    SecNotFoundError,
    SecRateLimitError,
    SecRawArtifact,
    SecRawArtifactError,
    SecRequest,
    SecRequestBuilder,
    SecResponseError,
    SecServerError,
    SecSource,
    SecTimeoutError,
    SecTransportError,
)

_RETRIEVED_AT = datetime(2026, 7, 24, 9, 10, 11, 654321, tzinfo=timezone.utc)


def _response(
    body: bytes,
    *,
    headers: dict[str, str] | None = None,
) -> HttpResponse:
    return HttpResponse(
        status_code=200,
        headers={} if headers is None else headers,
        body=body,
    )


class _FakeClient:
    def __init__(
        self,
        outcomes: list[HttpResponse | BaseException],
        *,
        representation_marker: str = "",
    ) -> None:
        self.outcomes = list(outcomes)
        self.requests: list[SecRequest] = []
        self.representation_marker = representation_marker

    def send(self, request: SecRequest) -> HttpResponse:
        self.requests.append(request)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome

    def __repr__(self) -> str:
        return f"_FakeClient({self.representation_marker})"


def _adapter(client: _FakeClient) -> SecCompanyFactsAdapter:
    return SecCompanyFactsAdapter(client)  # type: ignore[arg-type]


def test_construction_is_inert_frozen_slotted_and_repr_safe() -> None:
    marker = "CLIENT_REPR_MARKER_1A2B"
    client = _FakeClient([_response(b"body")], representation_marker=marker)
    adapter = _adapter(client)

    assert client.requests == []
    assert repr(adapter) == "SecCompanyFactsAdapter()"
    assert marker not in repr(adapter)
    assert not hasattr(adapter, "__dict__")
    assert tuple(adapter.__slots__) == ("_client",)
    with pytest.raises(FrozenInstanceError):
        adapter._client = _FakeClient([])  # type: ignore[misc]


@pytest.mark.parametrize(
    ("source_value", "expected_path"),
    [
        (789019, "/api/xbrl/companyfacts/CIK0000789019.json"),
        (1, "/api/xbrl/companyfacts/CIK0000000001.json"),
        (9_999_999_999, "/api/xbrl/companyfacts/CIK9999999999.json"),
    ],
)
def test_fetch_builds_exact_canonical_cik_path(
    source_value: int,
    expected_path: str,
) -> None:
    client = _FakeClient([_response(b"body")])
    adapter = _adapter(client)

    adapter.fetch(SecCik(source_value), retrieved_at=_RETRIEVED_AT)

    assert len(client.requests) == 1
    request = client.requests[0]
    assert request.path == expected_path
    assert request.query == {}
    assert "https://" not in request.path
    with pytest.raises(FrozenInstanceError):
        request.path = "/changed"  # type: ignore[misc]
    with pytest.raises(TypeError):
        request.query["override"] = "value"  # type: ignore[index]


def test_fetch_signature_has_no_endpoint_source_or_query_override() -> None:
    parameters = signature(SecCompanyFactsAdapter.fetch).parameters

    assert tuple(parameters) == ("self", "cik", "retrieved_at")
    assert parameters["retrieved_at"].kind.name == "KEYWORD_ONLY"


@pytest.mark.parametrize("invalid_cik", [789019, "0000789019", True, 789019.0, None])
def test_fetch_rejects_non_cik_without_calling_client(invalid_cik: object) -> None:
    client = _FakeClient([_response(b"body")])
    adapter = _adapter(client)

    with pytest.raises(
        ValueError,
        match="cik must be a SecCik",
    ) as exception_info:
        adapter.fetch(
            invalid_cik,  # type: ignore[arg-type]
            retrieved_at=_RETRIEVED_AT,
        )

    assert str(exception_info.value) == "cik must be a SecCik."
    assert repr(invalid_cik) not in str(exception_info.value)
    assert client.requests == []


@pytest.mark.parametrize(
    "body",
    [
        b'{"cik":789019,"facts":{}}',
        b"",
        b'{"malformed":',
        b"\x00\xff\x80binary",
        b'\xef\xbb\xbf{"bom":true}',
        b"line-one\r\nline-two\r\n",
        b' \t\n{"space":true}\r\n ',
    ],
)
def test_fetch_preserves_exact_body_without_parsing(body: bytes) -> None:
    response = _response(
        body,
        headers={"X-Synthetic": "RESPONSE_HEADER_MARKER_2B3C"},
    )
    client = _FakeClient([response])

    artifact = _adapter(client).fetch(
        SecCik(789019),
        retrieved_at=_RETRIEVED_AT,
    )

    assert isinstance(artifact, SecRawArtifact)
    assert artifact.source is SecSource.COMPANY_FACTS
    assert artifact.body is response.body
    assert artifact.body == body
    assert artifact.byte_length == len(body)
    assert artifact.sha256.value == hashlib.sha256(body).hexdigest()
    assert artifact.retrieved_at == _RETRIEVED_AT
    assert not hasattr(artifact, "headers")
    assert not hasattr(artifact, "status_code")


def test_fetch_delegates_offset_normalization_and_preserves_microseconds() -> None:
    supplied = datetime(
        2026,
        7,
        24,
        11,
        10,
        11,
        654321,
        tzinfo=timezone(timedelta(hours=2)),
    )

    artifact = _adapter(_FakeClient([_response(b"body")])).fetch(
        SecCik(789019),
        retrieved_at=supplied,
    )

    assert artifact.retrieved_at == _RETRIEVED_AT
    assert artifact.retrieved_at.tzinfo is timezone.utc
    assert artifact.retrieved_at.microsecond == 654321


def test_returned_artifact_is_immutable() -> None:
    artifact = _adapter(_FakeClient([_response(b"body")])).fetch(
        SecCik(789019),
        retrieved_at=_RETRIEVED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        artifact.body = b"changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    "error",
    [
        SecTimeoutError(timeout_seconds=10),
        SecTransportError(),
        SecRateLimitError(),
        SecNotFoundError(),
        SecServerError(status_code=500),
        SecResponseError(status_code=400),
    ],
)
def test_sec_client_errors_propagate_unchanged(error: Exception) -> None:
    client = _FakeClient([error])
    adapter = _adapter(client)

    with pytest.raises(type(error)) as exception_info:
        adapter.fetch(SecCik(789019), retrieved_at=_RETRIEVED_AT)

    assert exception_info.value is error
    assert len(client.requests) == 1


@pytest.mark.parametrize(
    "retrieved_at",
    [
        datetime(2026, 7, 24, 9, 10, 11),
        "2026-07-24T09:10:11Z",
        True,
        None,
    ],
)
def test_provenance_timestamp_errors_propagate_after_one_client_call(
    retrieved_at: object,
) -> None:
    body_marker = b"RAW_BODY_MARKER_3C4D"
    client = _FakeClient([_response(body_marker)])
    adapter = _adapter(client)

    with pytest.raises(SecRawArtifactError) as exception_info:
        adapter.fetch(
            SecCik(789019),
            retrieved_at=retrieved_at,  # type: ignore[arg-type]
        )

    error = exception_info.value
    assert str(error) == "SEC raw artifact input is invalid."
    assert "RAW_BODY_MARKER_3C4D" not in str(error)
    assert "RAW_BODY_MARKER_3C4D" not in repr(error)
    assert len(client.requests) == 1


class _RaisingTimezone(tzinfo):
    def utcoffset(self, _value: datetime | None) -> timedelta:
        raise RuntimeError("TIMEZONE_MARKER_4D5E")

    def dst(self, _value: datetime | None) -> timedelta:
        return timedelta(0)

    def tzname(self, _value: datetime | None) -> str:
        return "SYNTHETIC"


def test_pathological_timezone_error_remains_safe_and_unwrapped() -> None:
    client = _FakeClient([_response(b"body")])
    adapter = _adapter(client)

    with pytest.raises(SecRawArtifactError) as exception_info:
        adapter.fetch(
            SecCik(789019),
            retrieved_at=datetime(2026, 7, 24, tzinfo=_RaisingTimezone()),
        )

    error = exception_info.value
    assert "TIMEZONE_MARKER_4D5E" not in str(error)
    assert "TIMEZONE_MARKER_4D5E" not in repr(error)
    assert error.__cause__ is None
    assert len(client.requests) == 1


def test_unexpected_client_error_propagates_unchanged() -> None:
    error = RuntimeError("DEPENDENCY_ERROR_MARKER_5E6F")
    client = _FakeClient([error])
    adapter = _adapter(client)

    with pytest.raises(RuntimeError) as exception_info:
        adapter.fetch(SecCik(789019), retrieved_at=_RETRIEVED_AT)

    assert exception_info.value is error
    assert len(client.requests) == 1


def test_repeated_calls_are_fresh_and_not_cached() -> None:
    first_body = b'{"version":1}'
    second_body = b'{"version":2}'
    client = _FakeClient([_response(first_body), _response(second_body)])
    adapter = _adapter(client)

    first = adapter.fetch(SecCik(789019), retrieved_at=_RETRIEVED_AT)
    second = adapter.fetch(SecCik(789019), retrieved_at=_RETRIEVED_AT)

    assert first is not second
    assert first.body == first_body
    assert second.body == second_body
    assert first.sha256 != second.sha256
    assert len(client.requests) == 2
    assert client.requests[0] == client.requests[1]
    assert client.requests[0] is not client.requests[1]
    assert not hasattr(adapter, "request")
    assert not hasattr(adapter, "response")
    assert not hasattr(adapter, "body")
    assert not hasattr(adapter, "artifact")
    assert not hasattr(adapter, "history")


def test_repeated_equal_inputs_produce_value_equal_artifacts() -> None:
    body = b'{"same":true}'
    client = _FakeClient([_response(body), _response(body)])
    adapter = _adapter(client)

    first = adapter.fetch(SecCik(789019), retrieved_at=_RETRIEVED_AT)
    second = adapter.fetch(SecCik(789019), retrieved_at=_RETRIEVED_AT)

    assert first == second
    assert first is not second
    assert len(client.requests) == 2


def test_adapter_repr_and_state_exclude_operation_markers() -> None:
    client_marker = "CLIENT_MARKER_6F70"
    header_marker = "HEADER_MARKER_7081"
    body_marker = "BODY_MARKER_8192"
    client = _FakeClient(
        [
            _response(
                body_marker.encode(),
                headers={"X-Synthetic": header_marker},
            )
        ],
        representation_marker=client_marker,
    )
    adapter = _adapter(client)

    artifact = adapter.fetch(SecCik(789019), retrieved_at=_RETRIEVED_AT)

    representation = repr(adapter)
    assert client_marker not in representation
    assert header_marker not in representation
    assert body_marker not in representation
    assert body_marker not in repr(artifact)
    assert artifact.body == body_marker.encode()
    assert tuple(adapter.__slots__) == ("_client",)


class _RecordingTransport:
    def __init__(self, response: HttpResponse) -> None:
        self.response = response
        self.requests: list[HttpRequest] = []

    def send(self, request: HttpRequest) -> HttpResponse:
        self.requests.append(request)
        return self.response


class _FixedClock:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self) -> float:
        self.calls += 1
        return 0.0


class _UnexpectedTimingDependency:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, _delay_seconds: float | None = None) -> float:
        self.calls += 1
        raise AssertionError("unexpected timing dependency call")


def test_full_data_authority_composition_without_network_access() -> None:
    body = b'{"cik":789019,"entityName":"SYNTHETIC COMPANY","facts":{}}'
    settings = AppSettings.from_mapping(
        {
            "SEC_USER_AGENT": "Synthetic Company Facts Adapter/0.1",
            "SEC_CONTACT_EMAIL": "company-facts-adapter@example.test",
            "SEC_REQUEST_TIMEOUT_SECONDS": "13.5",
        }
    )
    builder = SecRequestBuilder(
        settings,
        base_url=settings.sec_data_base_url,
    )
    transport = _RecordingTransport(_response(body))
    clock = _FixedClock()
    sleeper = _UnexpectedTimingDependency()
    jitter = _UnexpectedTimingDependency()
    client = SecClient(
        builder=builder,
        transport=transport,
        retry_policy=RetryPolicy(),
        rate_limit_policy=RateLimitPolicy(max_requests_per_second=5),
        clock=clock,
        sleeper=sleeper,
        jitter_sample_provider=jitter,
    )
    adapter = SecCompanyFactsAdapter(client)

    artifact = adapter.fetch(SecCik(789019), retrieved_at=_RETRIEVED_AT)

    assert len(transport.requests) == 1
    request = transport.requests[0]
    assert (
        request.url == "https://data.sec.gov/api/xbrl/companyfacts/CIK0000789019.json"
    )
    assert request.method == "GET"
    assert "?" not in request.url
    assert request.timeout_seconds == 13.5
    assert dict(request.headers) == {
        "User-Agent": (
            "Synthetic Company Facts Adapter/0.1 company-facts-adapter@example.test"
        ),
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate",
    }
    assert artifact.source is SecSource.COMPANY_FACTS
    assert artifact.body == body
    assert artifact.byte_length == len(body)
    assert artifact.sha256.value == hashlib.sha256(body).hexdigest()
    assert clock.calls == 1
    assert sleeper.calls == 0
    assert jitter.calls == 0


def test_adapter_is_exported_only_from_sec_package() -> None:
    assert sec_providers.SecCompanyFactsAdapter is SecCompanyFactsAdapter
    assert "SecCompanyFactsAdapter" in sec_providers.__all__
    assert "SecCompanyFactsAdapter" not in generic_providers.__all__
    assert not hasattr(generic_providers, "SecCompanyFactsAdapter")
    assert not hasattr(sec_providers, "_COMPANY_FACTS_PATH_PREFIX")
    assert not hasattr(sec_providers, "_COMPANY_FACTS_PATH_SUFFIX")
    assert adapter_module._COMPANY_FACTS_PATH_PREFIX == ("/api/xbrl/companyfacts/CIK")
    assert adapter_module._COMPANY_FACTS_PATH_SUFFIX == ".json"
