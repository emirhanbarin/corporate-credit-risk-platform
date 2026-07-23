"""Tests for the official SEC ticker-mapping retrieval adapter."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from inspect import signature

import pytest

import credit_risk_platform.providers as generic_providers
import credit_risk_platform.providers.sec as sec_providers
import credit_risk_platform.providers.sec.ticker_mapping_adapter as adapter_module
from credit_risk_platform.config import AppSettings
from credit_risk_platform.providers import (
    HttpRequest,
    HttpResponse,
    RateLimitPolicy,
    RetryPolicy,
)
from credit_risk_platform.providers.sec import (
    SecClient,
    SecNotFoundError,
    SecRateLimitError,
    SecRequest,
    SecRequestBuilder,
    SecResponseError,
    SecServerError,
    SecTickerCatalog,
    SecTickerMappingAdapter,
    SecTickerMappingError,
    SecTickerNotFoundError,
    SecTimeoutError,
    SecTransportError,
)


def _body(
    *,
    ticker: str = "MSFT",
    cik: int = 789019,
    title: str = "MICROSOFT CORP",
) -> bytes:
    return json.dumps(
        {
            "0": {
                "cik_str": cik,
                "ticker": ticker,
                "title": title,
            }
        },
        separators=(",", ":"),
    ).encode()


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


def _adapter(client: _FakeClient) -> SecTickerMappingAdapter:
    return SecTickerMappingAdapter(client)  # type: ignore[arg-type]


def test_construction_is_inert_immutable_and_has_safe_representation() -> None:
    client_marker = "CLIENT_INTERNAL_MARKER_1A2B"
    client = _FakeClient([_response(_body())], representation_marker=client_marker)
    adapter = _adapter(client)

    assert client.requests == []
    assert repr(adapter) == "SecTickerMappingAdapter()"
    assert client_marker not in repr(adapter)
    assert not hasattr(adapter, "__dict__")
    with pytest.raises(FrozenInstanceError):
        adapter._client = _FakeClient([])  # type: ignore[misc]


def test_fetch_sends_exact_fixed_immutable_request_once() -> None:
    client = _FakeClient([_response(_body())])
    adapter = _adapter(client)

    catalog = adapter.fetch()

    assert isinstance(catalog, SecTickerCatalog)
    assert len(client.requests) == 1
    request = client.requests[0]
    assert request == SecRequest("/files/company_tickers.json", {})
    assert request.path == "/files/company_tickers.json"
    assert request.query == {}
    with pytest.raises(FrozenInstanceError):
        request.path = "/changed"  # type: ignore[misc]
    with pytest.raises(TypeError):
        request.query["key"] = "value"  # type: ignore[index]


def test_fetch_has_no_caller_control_over_path_query_url_or_ticker() -> None:
    adapter = _adapter(_FakeClient([_response(_body())]))

    assert tuple(signature(SecTickerMappingAdapter.fetch).parameters) == ("self",)
    with pytest.raises(TypeError):
        adapter.fetch("https://other.example.test")  # type: ignore[call-arg]


def test_valid_microsoft_mapping_returns_parsed_catalog() -> None:
    response = _response(
        _body(),
        headers={"X-Synthetic": "HEADER_MARKER_2B3C"},
    )
    adapter = _adapter(_FakeClient([response]))

    catalog = adapter.fetch()
    record = catalog.require("MSFT")

    assert record.ticker == "MSFT"
    assert record.cik.value == "0000789019"
    assert record.title == "MICROSOFT CORP"


def test_multiple_records_are_parsed_without_adapter_normalization() -> None:
    body = json.dumps(
        {
            "9": {
                "cik_str": 789019,
                "ticker": "msft",
                "title": "Microsoft Corp., Class A",
            },
            "2": {
                "cik_str": 320193,
                "ticker": "AAPL",
                "title": "APPLE INC.",
            },
        },
        separators=(",", ":"),
    ).encode()
    adapter = _adapter(_FakeClient([_response(body)]))

    catalog = adapter.fetch()

    assert tuple(record.ticker for record in catalog.records) == ("AAPL", "MSFT")
    assert catalog.require("MSFT").title == "Microsoft Corp., Class A"


def test_adapter_does_not_reinterpret_response_metadata() -> None:
    body = _body()
    response = _response(
        body,
        status_code=599,
        headers={"Content-Type": "text/plain", "X-Marker": "HEADER_MARKER_3C4D"},
    )
    adapter = _adapter(_FakeClient([response]))

    catalog = adapter.fetch()

    assert catalog.require("MSFT").cik.value == "0000789019"
    assert response.body is body


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
def test_existing_retrieval_errors_propagate_by_identity(
    error: Exception,
) -> None:
    client = _FakeClient([error])
    adapter = _adapter(client)

    with pytest.raises(type(error)) as exception_info:
        adapter.fetch()

    assert exception_info.value is error
    assert len(client.requests) == 1


@pytest.mark.parametrize(
    "body",
    [
        b"",
        b"\xff\xfe",
        b'{"MALFORMED_BODY_MARKER_4D5E":',
        b'{"0":{"cik_str":0,"ticker":"TEST","title":"TEST"}}',
        (
            b'{"0":{"cik_str":1,"ticker":"TEST","title":"TEST"},'
            b'"1":{"cik_str":1,"ticker":"test","title":"TEST"}}'
        ),
    ],
)
def test_mapping_parser_errors_propagate_without_reclassification(body: bytes) -> None:
    client = _FakeClient([_response(body)])
    adapter = _adapter(client)

    with pytest.raises(SecTickerMappingError) as exception_info:
        adapter.fetch()

    error = exception_info.value
    assert type(error) is SecTickerMappingError
    assert not isinstance(error, (SecTransportError, SecResponseError))
    assert "MALFORMED_BODY_MARKER_4D5E" not in str(error)
    assert "MALFORMED_BODY_MARKER_4D5E" not in repr(error)
    assert len(client.requests) == 1


def test_unexpected_client_error_propagates_unchanged() -> None:
    error = RuntimeError("DEPENDENCY_MARKER_5E6F")
    client = _FakeClient([error])
    adapter = _adapter(client)

    with pytest.raises(RuntimeError) as exception_info:
        adapter.fetch()

    assert exception_info.value is error
    assert len(client.requests) == 1


def test_ticker_absence_remains_a_catalog_lookup_concern() -> None:
    adapter = _adapter(_FakeClient([_response(_body())]))

    catalog = adapter.fetch()

    assert catalog.find("UNKNOWN") is None
    with pytest.raises(SecTickerNotFoundError):
        catalog.require("UNKNOWN")


def test_repeated_fetches_make_fresh_calls_without_caching() -> None:
    first_body = _body()
    second_body = _body(ticker="AAPL", cik=320193, title="APPLE INC.")
    client = _FakeClient([_response(first_body), _response(second_body)])
    adapter = _adapter(client)

    first = adapter.fetch()
    second = adapter.fetch()

    assert first is not second
    assert first.require("MSFT").cik.value == "0000789019"
    assert second.require("AAPL").cik.value == "0000320193"
    assert len(client.requests) == 2
    assert client.requests[0] == client.requests[1]
    assert client.requests[0] is not client.requests[1]
    assert not hasattr(adapter, "response")
    assert not hasattr(adapter, "body")
    assert not hasattr(adapter, "catalog")


def test_adapter_representation_retains_no_dependency_or_response_markers() -> None:
    client_marker = "CLIENT_MARKER_6F70"
    header_marker = "HEADER_MARKER_7081"
    body_marker = "BODY_MARKER_8192"
    client = _FakeClient(
        [
            _response(
                (
                    b'{"0":{"cik_str":1,"ticker":"TEST","title":"'
                    + body_marker.encode()
                    + b'"}}'
                ),
                headers={"X-Synthetic": header_marker},
            )
        ],
        representation_marker=client_marker,
    )
    adapter = _adapter(client)

    adapter.fetch()

    representation = repr(adapter)
    assert client_marker not in representation
    assert header_marker not in representation
    assert body_marker not in representation
    assert not hasattr(adapter, "request")
    assert not hasattr(adapter, "response")
    assert not hasattr(adapter, "headers")


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


class _UnexpectedCallable:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, _value: float | None = None) -> float:
        self.calls += 1
        raise AssertionError("unexpected timing dependency call")


def test_full_files_authority_composition_without_network_access() -> None:
    settings = AppSettings.from_mapping(
        {
            "SEC_USER_AGENT": "Synthetic Ticker Adapter/0.1",
            "SEC_CONTACT_EMAIL": "ticker-adapter@example.test",
            "SEC_REQUEST_TIMEOUT_SECONDS": "12.5",
        }
    )
    builder = SecRequestBuilder(
        settings,
        base_url=settings.sec_files_base_url,
    )
    transport = _RecordingTransport(_response(_body()))
    clock = _FixedClock()
    sleeper = _UnexpectedCallable()
    jitter = _UnexpectedCallable()
    client = SecClient(
        builder=builder,
        transport=transport,
        retry_policy=RetryPolicy(),
        rate_limit_policy=RateLimitPolicy(max_requests_per_second=5),
        clock=clock,
        sleeper=sleeper,
        jitter_sample_provider=jitter,
    )
    adapter = SecTickerMappingAdapter(client)

    catalog = adapter.fetch()

    assert catalog.require("MSFT").cik.value == "0000789019"
    assert len(transport.requests) == 1
    request = transport.requests[0]
    assert request.url == "https://www.sec.gov/files/company_tickers.json"
    assert request.method == "GET"
    assert request.timeout_seconds == 12.5
    assert dict(request.headers) == {
        "User-Agent": ("Synthetic Ticker Adapter/0.1 ticker-adapter@example.test"),
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate",
    }
    assert clock.calls == 1
    assert sleeper.calls == 0
    assert jitter.calls == 0


def test_adapter_is_exported_only_from_sec_package() -> None:
    assert sec_providers.SecTickerMappingAdapter is SecTickerMappingAdapter
    assert "SecTickerMappingAdapter" in sec_providers.__all__
    assert "SecTickerMappingAdapter" not in generic_providers.__all__
    assert not hasattr(generic_providers, "SecTickerMappingAdapter")
    assert not hasattr(sec_providers, "_TICKER_MAPPING_PATH")
    assert adapter_module._TICKER_MAPPING_PATH == "/files/company_tickers.json"
