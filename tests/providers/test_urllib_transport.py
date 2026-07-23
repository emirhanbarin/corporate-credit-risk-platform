"""Offline tests for the synchronous standard-library HTTP transport."""

from __future__ import annotations

import socket
import ssl
import urllib.error
import urllib.request
from collections.abc import Iterable
from dataclasses import FrozenInstanceError
from typing import Any

import pytest

from credit_risk_platform.providers import (
    HttpRequest,
    HttpResponse,
    HttpResponseTooLargeError,
    HttpTimeoutError,
    HttpTransport,
    HttpTransportError,
    UrllibHttpTransport,
)


class _FakeHeaders:
    def __init__(self, items: Iterable[tuple[str, str]] = ()) -> None:
        self._items = list(items)

    def raw_items(self) -> Iterable[tuple[str, str]]:
        return iter(self._items)


class _FakeResponse:
    def __init__(
        self,
        *,
        status: int = 200,
        headers: Iterable[tuple[str, str]] = (),
        body: bytes = b"",
        read_error: BaseException | None = None,
        maximum_chunk_size: int | None = None,
    ) -> None:
        self.status = status
        self.headers = _FakeHeaders(headers)
        self._body = body
        self._position = 0
        self._read_error = read_error
        self._maximum_chunk_size = maximum_chunk_size
        self.read_amounts: list[int] = []
        self.closed = False

    def read(self, amount: int = -1) -> bytes:
        self.read_amounts.append(amount)
        if self._read_error is not None:
            raise self._read_error
        if amount < 0:
            amount = len(self._body) - self._position
        if self._maximum_chunk_size is not None:
            amount = min(amount, self._maximum_chunk_size)
        start = self._position
        self._position += amount
        return self._body[start : self._position]

    def close(self) -> None:
        self.closed = True


class _UrlopenCapture:
    def __init__(
        self,
        outcomes: _FakeResponse | BaseException | list[_FakeResponse],
    ) -> None:
        self._outcomes = outcomes
        self.calls: list[tuple[urllib.request.Request, float, ssl.SSLContext]] = []

    def __call__(
        self,
        request: urllib.request.Request,
        *,
        timeout: float,
        context: ssl.SSLContext,
    ) -> _FakeResponse:
        self.calls.append((request, timeout, context))
        if isinstance(self._outcomes, list):
            outcome: _FakeResponse | BaseException = self._outcomes.pop(0)
        else:
            outcome = self._outcomes
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


def _request(**overrides: object) -> HttpRequest:
    values: dict[str, object] = {
        "method": "get",
        "url": "https://service.example.test/resource?item=ordinary",
        "headers": {
            "Accept": "application/octet-stream",
            "X-Request-ID": "request-1",
        },
        "timeout_seconds": 12.5,
    }
    values.update(overrides)
    return HttpRequest(**values)  # type: ignore[arg-type]


def _install_urlopen(
    monkeypatch: pytest.MonkeyPatch,
    outcomes: _FakeResponse | BaseException | list[_FakeResponse],
) -> _UrlopenCapture:
    capture = _UrlopenCapture(outcomes)
    monkeypatch.setattr(urllib.request, "urlopen", capture)
    return capture


def _send_structurally(
    transport: HttpTransport,
    request: HttpRequest,
) -> HttpResponse:
    return transport.send(request)


def test_default_limit_and_default_ssl_context_are_created_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    create_calls = 0

    def create_context() -> ssl.SSLContext:
        nonlocal create_calls
        create_calls += 1
        return context

    monkeypatch.setattr(ssl, "create_default_context", create_context)
    capture = _install_urlopen(
        monkeypatch,
        [
            _FakeResponse(headers=[("Content-Length", "10000001")]),
            _FakeResponse(body=b"second"),
        ],
    )
    transport = UrllibHttpTransport()

    with pytest.raises(HttpResponseTooLargeError) as exception_info:
        transport.send(_request())
    response = transport.send(_request())

    assert exception_info.value.max_response_bytes == 10_000_000
    assert response.body == b"second"
    assert create_calls == 1
    assert capture.calls[0][2] is context
    assert capture.calls[1][2] is context


def test_custom_limit_and_supplied_ssl_context_are_retained_without_mutation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    before = (context.check_hostname, context.verify_mode)
    capture = _install_urlopen(monkeypatch, _FakeResponse(body=b"1234"))
    transport = UrllibHttpTransport(max_response_bytes=4, ssl_context=context)

    response = transport.send(_request())

    assert response.body == b"1234"
    assert capture.calls[0][2] is context
    assert (context.check_hostname, context.verify_mode) == before


@pytest.mark.parametrize("limit", [0, -1, True, 1.5, "10"])
def test_invalid_response_limits_are_rejected(limit: object) -> None:
    with pytest.raises(ValueError, match="max_response_bytes"):
        UrllibHttpTransport(max_response_bytes=limit)  # type: ignore[arg-type]


def test_transport_is_structurally_compatible_with_protocol(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_urlopen(monkeypatch, _FakeResponse(status=204))

    response = _send_structurally(UrllibHttpTransport(), _request())

    assert response.status_code == 204


def test_request_conversion_preserves_request_without_adding_a_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    capture = _install_urlopen(monkeypatch, _FakeResponse(body=b"ok"))
    request = _request(method="post")
    original = _request(method="post")

    response = UrllibHttpTransport(ssl_context=context).send(request)
    sent_request, timeout, sent_context = capture.calls[0]

    assert response.body == b"ok"
    assert sent_request.full_url == request.url
    assert sent_request.get_method() == "POST"
    assert dict(sent_request.header_items()) == {
        "Accept": "application/octet-stream",
        "X-request-id": "request-1",
    }
    assert sent_request.data is None
    assert timeout == request.timeout_seconds
    assert sent_context is context
    assert request == original


def test_repeated_calls_do_not_share_response_or_request_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_source = _FakeResponse(body=b"first")
    second_source = _FakeResponse(body=b"second")
    capture = _install_urlopen(monkeypatch, [first_source, second_source])
    transport = UrllibHttpTransport()
    request = _request()

    first = transport.send(request)
    second = transport.send(request)

    assert first.body == b"first"
    assert second.body == b"second"
    assert capture.calls[0][0] is not capture.calls[1][0]
    assert first_source.closed
    assert second_source.closed


@pytest.mark.parametrize(("status", "body"), [(200, b"payload"), (204, b"")])
def test_ordinary_responses_preserve_status_headers_and_body_and_close(
    monkeypatch: pytest.MonkeyPatch,
    status: int,
    body: bytes,
) -> None:
    source = _FakeResponse(
        status=status,
        headers=[("Content-Type", "application/octet-stream"), ("X-Test", "yes")],
        body=body,
    )
    _install_urlopen(monkeypatch, source)

    response = UrllibHttpTransport().send(_request())

    assert response.status_code == status
    assert dict(response.headers) == {
        "Content-Type": "application/octet-stream",
        "X-Test": "yes",
    }
    assert response.body == body
    assert source.closed


def test_response_body_is_copied_from_the_transport_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mutable = bytearray(b"payload")
    source = _FakeResponse(body=bytes(mutable))
    _install_urlopen(monkeypatch, source)

    response = UrllibHttpTransport().send(_request())
    mutable[:] = b"changed"

    assert response.body == b"payload"


def test_short_reads_are_accumulated_without_exceeding_read_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _FakeResponse(body=b"12345", maximum_chunk_size=2)
    _install_urlopen(monkeypatch, source)

    response = UrllibHttpTransport(max_response_bytes=5).send(_request())

    assert response.body == b"12345"
    assert sum(source.read_amounts) > 0
    assert source.closed


def test_body_exactly_at_limit_is_accepted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _FakeResponse(body=b"12345")
    _install_urlopen(monkeypatch, source)

    response = UrllibHttpTransport(max_response_bytes=5).send(_request())

    assert response.body == b"12345"
    assert source.read_amounts == [6, 1]
    assert source.closed


def test_body_one_byte_over_limit_is_rejected_and_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _FakeResponse(body=b"123456")
    _install_urlopen(monkeypatch, source)

    with pytest.raises(HttpResponseTooLargeError) as exception_info:
        UrllibHttpTransport(max_response_bytes=5).send(_request())

    assert exception_info.value.max_response_bytes == 5
    assert source.read_amounts == [6]
    assert source.closed


def test_large_valid_content_length_is_rejected_before_reading(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _FakeResponse(
        headers=[("Content-Length", " 6 ")],
        body=b"ignored",
    )
    _install_urlopen(monkeypatch, source)

    with pytest.raises(HttpResponseTooLargeError):
        UrllibHttpTransport(max_response_bytes=5).send(_request())

    assert source.read_amounts == []
    assert source.closed


@pytest.mark.parametrize("content_length", ["invalid", "-1", "0"])
def test_untrusted_content_length_uses_bounded_body_read(
    monkeypatch: pytest.MonkeyPatch,
    content_length: str,
) -> None:
    source = _FakeResponse(
        headers=[("Content-Length", content_length)],
        body=b"123456",
    )
    _install_urlopen(monkeypatch, source)

    with pytest.raises(HttpResponseTooLargeError):
        UrllibHttpTransport(max_response_bytes=5).send(_request())

    assert source.read_amounts == [6]
    assert source.closed


def test_unreasonably_large_numeric_content_length_uses_bounded_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _FakeResponse(
        headers=[("Content-Length", "9" * 5000)],
        body=b"123456",
    )
    _install_urlopen(monkeypatch, source)

    with pytest.raises(HttpResponseTooLargeError):
        UrllibHttpTransport(max_response_bytes=5).send(_request())

    assert source.read_amounts == [6]
    assert source.closed


def test_declared_small_content_length_cannot_bypass_actual_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _FakeResponse(
        headers=[("Content-Length", "1")],
        body=b"123456",
    )
    _install_urlopen(monkeypatch, source)

    with pytest.raises(HttpResponseTooLargeError):
        UrllibHttpTransport(max_response_bytes=5).send(_request())

    assert source.closed


def _http_error(
    status_code: int,
    response: _FakeResponse,
) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        "https://service.example.test/resource",
        status_code,
        "synthetic status",
        response.headers,  # type: ignore[arg-type]
        response,  # type: ignore[arg-type]
    )


@pytest.mark.parametrize("status_code", [404, 429, 500])
def test_http_errors_are_returned_as_uninterpreted_responses(
    monkeypatch: pytest.MonkeyPatch,
    status_code: int,
) -> None:
    source = _FakeResponse(
        headers=[("Content-Type", "application/problem+json")],
        body=b'{"status":"synthetic"}',
    )
    _install_urlopen(monkeypatch, _http_error(status_code, source))

    response = UrllibHttpTransport().send(_request())

    assert response.status_code == status_code
    assert response.headers == {"Content-Type": "application/problem+json"}
    assert response.body == b'{"status":"synthetic"}'
    assert source.closed


def test_oversized_http_error_body_is_rejected_and_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _FakeResponse(body=b"123456")
    _install_urlopen(monkeypatch, _http_error(500, source))

    with pytest.raises(HttpResponseTooLargeError):
        UrllibHttpTransport(max_response_bytes=5).send(_request())

    assert source.closed


def test_large_http_error_content_length_is_rejected_and_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _FakeResponse(
        headers=[("Content-Length", "6")],
        body=b"not-read",
    )
    _install_urlopen(monkeypatch, _http_error(429, source))

    with pytest.raises(HttpResponseTooLargeError):
        UrllibHttpTransport(max_response_bytes=5).send(_request())

    assert source.read_amounts == []
    assert source.closed


@pytest.mark.parametrize(
    "failure",
    [
        socket.timeout("sensitive timeout detail"),
        TimeoutError("sensitive timeout detail"),
        urllib.error.URLError(socket.timeout("nested sensitive timeout")),
        urllib.error.URLError(TimeoutError("nested sensitive timeout")),
    ],
)
def test_timeout_failures_are_mapped_safely(
    monkeypatch: pytest.MonkeyPatch,
    failure: BaseException,
) -> None:
    _install_urlopen(monkeypatch, failure)

    with pytest.raises(HttpTimeoutError) as exception_info:
        UrllibHttpTransport().send(_request())

    assert exception_info.value.timeout_seconds == 12.5
    assert str(exception_info.value) == "HTTP request timed out."
    assert "sensitive" not in str(exception_info.value)


@pytest.mark.parametrize(
    "failure",
    [
        urllib.error.URLError("sensitive DNS detail"),
        socket.gaierror("sensitive DNS detail"),
        ConnectionRefusedError("sensitive refused detail"),
        ssl.SSLError("sensitive certificate detail"),
        OSError("sensitive network detail"),
    ],
)
def test_non_timeout_failures_are_mapped_to_safe_transport_error(
    monkeypatch: pytest.MonkeyPatch,
    failure: BaseException,
) -> None:
    _install_urlopen(monkeypatch, failure)
    request = _request(
        url="https://service.example.test/resource?token=query-secret",
        headers={
            "User-Agent": ("Corporate Credit Risk Platform/0.1 transport@example.test"),
            "X-Private": "header-secret",
        },
    )

    with pytest.raises(HttpTransportError) as exception_info:
        UrllibHttpTransport().send(request)

    message = str(exception_info.value)
    assert message == "HTTP transport failed."
    assert "sensitive" not in message
    assert "service.example.test" not in message
    assert "query-secret" not in message
    assert "header-secret" not in message
    assert "transport@example.test" not in message


def test_repeated_response_headers_are_joined_case_insensitively(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _FakeResponse(
        headers=[
            ("X-Repeat", "first"),
            ("X-Repeat", "second"),
            ("x-repeat", "third"),
        ]
    )
    _install_urlopen(monkeypatch, source)

    response = UrllibHttpTransport().send(_request())

    assert dict(response.headers) == {"X-Repeat": "first, second, third"}


def test_duplicate_content_length_is_not_trusted_for_early_rejection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _FakeResponse(
        headers=[("Content-Length", "100"), ("content-length", "1")],
        body=b"ok",
    )
    _install_urlopen(monkeypatch, source)

    response = UrllibHttpTransport(max_response_bytes=5).send(_request())

    assert response.body == b"ok"
    assert response.headers == {"Content-Length": "100, 1"}


def test_unsafe_response_header_is_rejected_without_exposing_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    unsafe_value = "private-value\r\nInjected: yes"
    source = _FakeResponse(headers=[("X-Test", unsafe_value)])
    _install_urlopen(monkeypatch, source)

    with pytest.raises(HttpTransportError) as exception_info:
        UrllibHttpTransport().send(_request())

    assert str(exception_info.value) == "HTTP transport failed."
    assert unsafe_value not in str(exception_info.value)
    assert source.closed


class _MissingRawItems:
    pass


def test_unrepresentable_header_container_is_rejected_and_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _FakeResponse()
    source.headers = _MissingRawItems()  # type: ignore[assignment]
    _install_urlopen(monkeypatch, source)

    with pytest.raises(HttpTransportError):
        UrllibHttpTransport().send(_request())

    assert source.closed


def test_non_string_response_header_is_rejected_and_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _FakeResponse()
    source.headers = _FakeHeaders([("X-Test", 1)])  # type: ignore[list-item]
    _install_urlopen(monkeypatch, source)

    with pytest.raises(HttpTransportError):
        UrllibHttpTransport().send(_request())

    assert source.closed


def test_read_failure_is_mapped_and_response_is_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _FakeResponse(read_error=OSError("private body read detail"))
    _install_urlopen(monkeypatch, source)

    with pytest.raises(HttpTransportError) as exception_info:
        UrllibHttpTransport().send(_request())

    assert str(exception_info.value) == "HTTP transport failed."
    assert "private" not in str(exception_info.value)
    assert source.closed


def test_read_timeout_is_mapped_and_response_is_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _FakeResponse(read_error=socket.timeout("private timeout detail"))
    _install_urlopen(monkeypatch, source)

    with pytest.raises(HttpTimeoutError) as exception_info:
        UrllibHttpTransport().send(_request())

    assert exception_info.value.timeout_seconds == 12.5
    assert source.closed


@pytest.mark.parametrize("failure", [TypeError("programming"), AssertionError("bug")])
def test_programming_errors_are_not_normalized(
    monkeypatch: pytest.MonkeyPatch,
    failure: BaseException,
) -> None:
    _install_urlopen(monkeypatch, failure)

    with pytest.raises(type(failure), match=str(failure)):
        UrllibHttpTransport().send(_request())


class _MissingStatus:
    headers = _FakeHeaders()

    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


def test_malformed_response_without_status_is_mapped_and_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _MissingStatus()
    monkeypatch.setattr(urllib.request, "urlopen", lambda *args, **kwargs: source)

    with pytest.raises(HttpTransportError):
        UrllibHttpTransport().send(_request())

    assert source.closed


class _MissingHeaders:
    status = 200

    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


def test_malformed_response_without_headers_is_mapped_and_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _MissingHeaders()
    monkeypatch.setattr(urllib.request, "urlopen", lambda *args, **kwargs: source)

    with pytest.raises(HttpTransportError):
        UrllibHttpTransport().send(_request())

    assert source.closed


def test_non_bytes_body_chunk_is_rejected_and_response_is_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _FakeResponse()
    source.read = lambda amount=-1: "not-bytes"  # type: ignore[method-assign,return-value]
    _install_urlopen(monkeypatch, source)

    with pytest.raises(HttpTransportError):
        UrllibHttpTransport().send(_request())

    assert source.closed


def test_generic_exception_hierarchy_messages_and_metadata_are_safe() -> None:
    transport_error = HttpTransportError()
    timeout_error = HttpTimeoutError(timeout_seconds=5)
    size_error = HttpResponseTooLargeError(max_response_bytes=20)

    assert isinstance(timeout_error, HttpTransportError)
    assert isinstance(size_error, HttpTransportError)
    assert str(transport_error) == "HTTP transport failed."
    assert str(timeout_error) == "HTTP request timed out."
    assert str(size_error) == ("HTTP response body exceeded the configured size limit.")
    assert timeout_error.timeout_seconds == 5.0
    assert size_error.max_response_bytes == 20


@pytest.mark.parametrize(
    "timeout",
    [0, -1, float("inf"), float("nan"), True, "5", None],
)
def test_invalid_timeout_metadata_is_rejected(timeout: Any) -> None:
    with pytest.raises(ValueError, match="timeout_seconds"):
        HttpTimeoutError(timeout_seconds=timeout)


@pytest.mark.parametrize("limit", [0, -1, True, 1.5, "5"])
def test_invalid_size_metadata_is_rejected(limit: Any) -> None:
    with pytest.raises(ValueError, match="max_response_bytes"):
        HttpResponseTooLargeError(max_response_bytes=limit)


def test_error_metadata_and_transport_state_are_read_only() -> None:
    timeout_error = HttpTimeoutError(timeout_seconds=5)
    size_error = HttpResponseTooLargeError(max_response_bytes=10)
    transport = UrllibHttpTransport()

    with pytest.raises(AttributeError):
        timeout_error.timeout_seconds = 10  # type: ignore[misc]
    with pytest.raises(AttributeError):
        size_error.max_response_bytes = 20  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        transport._max_response_bytes = 20  # type: ignore[misc]


def test_size_error_does_not_expose_body_content() -> None:
    private_body = "private response body"
    error = HttpResponseTooLargeError(max_response_bytes=10)

    assert private_body not in str(error)
