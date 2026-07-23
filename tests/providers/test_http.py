"""Tests for transport-independent HTTP contracts."""

from dataclasses import FrozenInstanceError
from typing import assert_type

import pytest

from credit_risk_platform.providers import HttpRequest, HttpResponse, HttpTransport


def _request(**overrides: object) -> HttpRequest:
    values: dict[str, object] = {
        "method": "get",
        "url": "https://data.sec.gov/submissions/test.json?name=value",
        "headers": {"Accept": "application/json"},
        "timeout_seconds": 30.0,
    }
    values.update(overrides)
    return HttpRequest(**values)  # type: ignore[arg-type]


def test_valid_request_is_normalized_and_immutable() -> None:
    request = _request()

    assert request.method == "GET"
    with pytest.raises(FrozenInstanceError):
        request.url = "https://changed.example.test"  # type: ignore[misc]


def test_request_headers_are_defensively_copied_and_immutable() -> None:
    source = {"Accept": "application/json"}
    request = _request(headers=source)

    source["Accept"] = "text/plain"
    assert request.headers == {"Accept": "application/json"}
    with pytest.raises(TypeError):
        request.headers["Accept"] = "text/plain"  # type: ignore[index]


@pytest.mark.parametrize("method", ["", " \t ", "G ET", "GET\n", "GET\x00", None])
def test_invalid_methods_are_rejected(method: object) -> None:
    with pytest.raises(ValueError, match="method"):
        _request(method=method)


@pytest.mark.parametrize(
    "url",
    [
        "http://data.sec.gov/path",
        "/relative/path",
        "https:///missing-host",
        "https://user:secret@data.sec.gov/path",
        "https://data.sec.gov/path#fragment",
        "https://data.sec.gov/path with-space",
        "https://data.sec.gov:not-a-port/path",
        "https://data.sec.gov\\path",
        "",
        None,
    ],
)
def test_invalid_request_urls_are_rejected(url: object) -> None:
    with pytest.raises(ValueError, match="url"):
        _request(url=url)


@pytest.mark.parametrize("timeout", [0.0, -1.0, float("inf"), float("nan"), True, "30"])
def test_invalid_timeouts_are_rejected(timeout: object) -> None:
    with pytest.raises(ValueError, match="timeout_seconds"):
        _request(timeout_seconds=timeout)


@pytest.mark.parametrize(
    "headers",
    [
        {"": "value"},
        {" \t ": "value"},
        {"Bad Name": "value"},
        {"Bad:Name": "value"},
        {"Bad\nName": "value"},
        {"Bad\x00Name": "value"},
        {"Name": "bad\rvalue"},
        {"Name": "bad\nvalue"},
        {"Name": "bad\x7fvalue"},
        {"Name": "bad\x85value"},
    ],
)
def test_invalid_headers_are_rejected(headers: dict[str, str]) -> None:
    with pytest.raises(ValueError, match="header"):
        _request(headers=headers)


def test_case_insensitive_duplicate_header_names_are_rejected() -> None:
    with pytest.raises(ValueError, match="unique"):
        _request(headers={"Accept": "application/json", "accept": "text/plain"})


@pytest.mark.parametrize("headers", [None, {"Name": 1}, {1: "value"}])
def test_headers_must_be_a_string_mapping(headers: object) -> None:
    with pytest.raises(ValueError, match="header"):
        _request(headers=headers)


def test_valid_response_boundaries_and_body_copy() -> None:
    mutable_body = bytearray(b"payload")
    lower = HttpResponse(100, {"X-Test": "yes"}, mutable_body)  # type: ignore[arg-type]
    upper = HttpResponse(599, {}, b"")

    mutable_body[:] = b"changed"
    assert lower.body == b"payload"
    assert upper.status_code == 599


@pytest.mark.parametrize("status_code", [99, 600, True, 200.0])
def test_invalid_response_status_codes_are_rejected(status_code: object) -> None:
    with pytest.raises(ValueError, match="status_code"):
        HttpResponse(status_code, {}, b"")  # type: ignore[arg-type]


def test_response_body_must_be_bytes_like() -> None:
    with pytest.raises(ValueError, match="body"):
        HttpResponse(200, {}, "not bytes")  # type: ignore[arg-type]


def test_response_headers_are_defensively_copied_and_immutable() -> None:
    source = {"Content-Type": "application/json"}
    response = HttpResponse(200, source, b"{}")

    source["Content-Type"] = "text/plain"
    assert response.headers == {"Content-Type": "application/json"}
    with pytest.raises(TypeError):
        response.headers["Content-Type"] = "text/plain"  # type: ignore[index]


class _FakeTransport:
    def send(self, request: HttpRequest) -> HttpResponse:
        return HttpResponse(200, {}, request.url.encode())


def _send(transport: HttpTransport, request: HttpRequest) -> HttpResponse:
    return transport.send(request)


def test_protocol_supports_structural_use_without_network_code() -> None:
    response = _send(_FakeTransport(), _request())

    assert_type(response, HttpResponse)
    assert response.status_code == 200
