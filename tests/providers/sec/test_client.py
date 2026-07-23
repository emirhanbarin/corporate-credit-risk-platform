"""Deterministic tests for synchronous SEC request orchestration."""

from __future__ import annotations

from collections.abc import Callable

import pytest

import credit_risk_platform.providers as generic_providers
import credit_risk_platform.providers.sec as sec_providers
from credit_risk_platform.config import AppSettings
from credit_risk_platform.providers import (
    HttpRequest,
    HttpResponse,
    HttpTimeoutError,
    HttpTransportError,
    RateLimitPolicy,
    RateLimitState,
    RetryDecision,
    RetryOutcome,
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
    SecTimeoutError,
    SecTransportError,
)


class _FakeBuilder:
    def __init__(
        self,
        http_request: HttpRequest,
        *,
        error: BaseException | None = None,
    ) -> None:
        self.http_request = http_request
        self.error = error
        self.calls: list[SecRequest] = []

    def build(self, request: SecRequest) -> HttpRequest:
        self.calls.append(request)
        if self.error is not None:
            raise self.error
        return self.http_request


class _FakeTransport:
    def __init__(self, outcomes: list[HttpResponse | BaseException]) -> None:
        self.outcomes = list(outcomes)
        self.requests: list[HttpRequest] = []

    def send(self, request: HttpRequest) -> HttpResponse:
        self.requests.append(request)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


class _MutableClock:
    def __init__(
        self,
        value: float = 0.0,
        *,
        error: BaseException | None = None,
    ) -> None:
        self.value = value
        self.error = error
        self.calls = 0

    def __call__(self) -> float:
        self.calls += 1
        if self.error is not None:
            raise self.error
        return self.value


class _SequenceClock:
    def __init__(self, values: list[float]) -> None:
        self.values = list(values)
        self.calls = 0

    def __call__(self) -> float:
        self.calls += 1
        return self.values.pop(0)


class _Sleeper:
    def __init__(
        self,
        clock: _MutableClock | None = None,
        *,
        advance_clock: bool = True,
        error: BaseException | None = None,
    ) -> None:
        self.clock = clock
        self.advance_clock = advance_clock
        self.error = error
        self.delays: list[float] = []

    def __call__(self, delay_seconds: float) -> None:
        self.delays.append(delay_seconds)
        if self.error is not None:
            raise self.error
        if self.clock is not None and self.advance_clock:
            self.clock.value += delay_seconds


class _JitterSamples:
    def __init__(
        self,
        samples: list[float] | None = None,
        *,
        error: BaseException | None = None,
    ) -> None:
        self.samples = [] if samples is None else list(samples)
        self.error = error
        self.calls = 0

    def __call__(self) -> float:
        self.calls += 1
        if self.error is not None:
            raise self.error
        if self.samples:
            return self.samples.pop(0)
        return 0.5


class _RecordingRetryPolicy(RetryPolicy):
    __slots__ = ("calls",)

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)  # type: ignore[arg-type]
        object.__setattr__(
            self,
            "calls",
            [],
        )

    def decide(
        self,
        *,
        attempt_number: int,
        outcome: RetryOutcome,
        jitter_sample: float,
        http_status_code: int | None = None,
        retry_after_seconds: float | None = None,
    ) -> RetryDecision:
        self.calls.append((attempt_number, outcome, jitter_sample, http_status_code))
        return super().decide(
            attempt_number=attempt_number,
            outcome=outcome,
            jitter_sample=jitter_sample,
            http_status_code=http_status_code,
            retry_after_seconds=retry_after_seconds,
        )


def _http_request() -> HttpRequest:
    return HttpRequest(
        method="GET",
        url="https://data.sec.gov/path?item=ordinary",
        headers={
            "User-Agent": "Synthetic SEC Client operations@example.test",
            "Accept": "application/json",
        },
        timeout_seconds=10,
    )


def _response(
    status_code: int = 200,
    *,
    body: bytes = b"response",
    headers: dict[str, str] | None = None,
) -> HttpResponse:
    return HttpResponse(
        status_code=status_code,
        headers={} if headers is None else headers,
        body=body,
    )


def _sec_request() -> SecRequest:
    return SecRequest("/path", {"item": "ordinary"})


def _client(
    outcomes: list[HttpResponse | BaseException],
    *,
    retry_policy: RetryPolicy | None = None,
    rate_limit_policy: RateLimitPolicy | None = None,
    clock: _MutableClock | _SequenceClock | None = None,
    sleeper: _Sleeper | None = None,
    jitter: _JitterSamples | None = None,
    builder: _FakeBuilder | None = None,
) -> tuple[
    SecClient,
    _FakeBuilder,
    _FakeTransport,
    _MutableClock | _SequenceClock,
    _Sleeper,
    _JitterSamples,
]:
    retained_clock = _MutableClock() if clock is None else clock
    retained_sleeper = (
        _Sleeper(retained_clock if isinstance(retained_clock, _MutableClock) else None)
        if sleeper is None
        else sleeper
    )
    retained_jitter = _JitterSamples() if jitter is None else jitter
    retained_builder = _FakeBuilder(_http_request()) if builder is None else builder
    transport = _FakeTransport(outcomes)
    client = SecClient(
        builder=retained_builder,
        transport=transport,
        retry_policy=RetryPolicy(jitter_proportion=0)
        if retry_policy is None
        else retry_policy,
        rate_limit_policy=RateLimitPolicy(max_requests_per_second=5)
        if rate_limit_policy is None
        else rate_limit_policy,
        clock=retained_clock,
        sleeper=retained_sleeper,
        jitter_sample_provider=retained_jitter,
    )
    return (
        client,
        retained_builder,
        transport,
        retained_clock,
        retained_sleeper,
        retained_jitter,
    )


def test_construction_calls_no_dependency_and_starts_with_empty_state() -> None:
    client, builder, transport, clock, sleeper, jitter = _client([_response()])

    assert builder.calls == []
    assert transport.requests == []
    assert clock.calls == 0
    assert sleeper.delays == []
    assert jitter.calls == 0
    assert client.rate_limit_state == RateLimitState()
    assert builder.http_request == _http_request()


@pytest.mark.parametrize(
    ("dependency", "invalid_value", "message"),
    [
        ("builder", object(), "builder"),
        ("transport", object(), "transport"),
        ("retry_policy", object(), "retry_policy"),
        ("rate_limit_policy", object(), "rate_limit_policy"),
        ("clock", object(), "clock"),
        ("sleeper", object(), "sleeper"),
        ("jitter_sample_provider", object(), "jitter_sample_provider"),
    ],
)
def test_invalid_constructor_dependencies_are_rejected_without_execution(
    dependency: str,
    invalid_value: object,
    message: str,
) -> None:
    builder = _FakeBuilder(_http_request())
    transport = _FakeTransport([_response()])
    clock = _MutableClock()
    sleeper = _Sleeper(clock)
    jitter = _JitterSamples()
    arguments: dict[str, object] = {
        "builder": builder,
        "transport": transport,
        "retry_policy": RetryPolicy(),
        "rate_limit_policy": RateLimitPolicy(max_requests_per_second=5),
        "clock": clock,
        "sleeper": sleeper,
        "jitter_sample_provider": jitter,
    }
    arguments[dependency] = invalid_value

    with pytest.raises(ValueError, match=message):
        SecClient(**arguments)  # type: ignore[arg-type]

    assert builder.calls == []
    assert transport.requests == []
    assert clock.calls == 0
    assert sleeper.delays == []
    assert jitter.calls == 0


def test_send_accepts_only_sec_request() -> None:
    client, builder, transport, clock, sleeper, jitter = _client([_response()])

    with pytest.raises(ValueError, match="request must be a SecRequest"):
        client.send("/path")  # type: ignore[arg-type]

    assert builder.calls == []
    assert transport.requests == []
    assert clock.calls == 0
    assert sleeper.delays == []
    assert jitter.calls == 0


def test_builder_failure_prevents_all_execution_dependencies() -> None:
    failure = LookupError("builder-programming-marker")
    builder = _FakeBuilder(_http_request(), error=failure)
    client, _, transport, clock, sleeper, jitter = _client(
        [_response()],
        builder=builder,
    )

    with pytest.raises(LookupError, match="builder-programming-marker"):
        client.send(_sec_request())

    assert builder.calls == [_sec_request()]
    assert transport.requests == []
    assert clock.calls == 0
    assert sleeper.delays == []
    assert jitter.calls == 0
    assert client.rate_limit_state == RateLimitState()


def test_first_attempt_success_returns_original_response_without_extra_calls() -> None:
    response = _response(
        headers={"X-Synthetic": "header-value"},
        body=b"\x00raw-body\xff",
    )
    client, builder, transport, clock, sleeper, jitter = _client([response])
    request = _sec_request()

    returned = client.send(request)

    assert returned is response
    assert returned.headers is response.headers
    assert returned.body is response.body
    assert builder.calls == [request]
    assert transport.requests == [builder.http_request]
    assert clock.calls == 1
    assert sleeper.delays == []
    assert jitter.calls == 0
    assert client.rate_limit_state == RateLimitState(last_request_start_time_seconds=0)


def test_real_request_builder_is_used_without_client_request_changes() -> None:
    settings = AppSettings.from_mapping(
        {
            "SEC_USER_AGENT": "Synthetic SEC Orchestrator/0.1",
            "SEC_CONTACT_EMAIL": "orchestration@example.test",
        }
    )
    builder = SecRequestBuilder(settings)
    transport = _FakeTransport([_response()])
    clock = _MutableClock()
    sleeper = _Sleeper(clock)
    client = SecClient(
        builder=builder,
        transport=transport,
        retry_policy=RetryPolicy(),
        rate_limit_policy=RateLimitPolicy(max_requests_per_second=5),
        clock=clock,
        sleeper=sleeper,
        jitter_sample_provider=_JitterSamples(),
    )

    client.send(SecRequest("/resource", {"z": "last", "a": "first"}))

    sent = transport.requests[0]
    assert sent.method == "GET"
    assert sent.url == "https://data.sec.gov/resource?a=first&z=last"
    assert sent.timeout_seconds == 30.0
    assert dict(sent.headers) == {
        "User-Agent": ("Synthetic SEC Orchestrator/0.1 orchestration@example.test"),
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate",
    }


def test_builder_runs_once_and_all_retries_reuse_exact_request() -> None:
    retry_policy = _RecordingRetryPolicy(
        max_attempts=3,
        initial_delay_seconds=1,
        jitter_proportion=0,
    )
    client, builder, transport, _, _, _ = _client(
        [_response(500), _response(503), _response(200)],
        retry_policy=retry_policy,
    )

    client.send(_sec_request())

    assert len(builder.calls) == 1
    assert len(transport.requests) == 3
    assert all(item is builder.http_request for item in transport.requests)
    assert [item[0] for item in retry_policy.calls] == [1, 2]
    assert [item[3] for item in retry_policy.calls] == [500, 503]


def test_sequential_calls_share_rate_limit_state_and_sleep_before_second() -> None:
    client, _, transport, clock, sleeper, jitter = _client([_response(), _response()])

    client.send(_sec_request())
    client.send(_sec_request())

    assert len(transport.requests) == 2
    assert sleeper.delays == pytest.approx([0.2])
    assert clock.calls == 3
    assert jitter.calls == 0
    assert client.rate_limit_state.last_request_start_time_seconds == pytest.approx(0.2)


def test_exact_rate_limit_boundary_needs_no_sleep() -> None:
    client, _, transport, clock, sleeper, _ = _client([_response(), _response()])
    assert isinstance(clock, _MutableClock)

    client.send(_sec_request())
    clock.value = 0.2
    client.send(_sec_request())

    assert len(transport.requests) == 2
    assert sleeper.delays == []
    assert client.rate_limit_state.last_request_start_time_seconds == 0.2


def test_non_advancing_clock_fails_deterministically_without_false_start() -> None:
    clock = _MutableClock()
    sleeper = _Sleeper(clock, advance_clock=False)
    client, _, transport, _, _, _ = _client(
        [_response(), _response()],
        clock=clock,
        sleeper=sleeper,
    )
    client.send(_sec_request())

    with pytest.raises(
        RuntimeError,
        match="SEC request pacing could not obtain an admissible start",
    ):
        client.send(_sec_request())

    assert len(transport.requests) == 1
    assert sleeper.delays == pytest.approx([0.2, 0.2])
    assert clock.calls == 4
    assert client.rate_limit_state == RateLimitState(last_request_start_time_seconds=0)


def test_retry_delay_shorter_than_rate_interval_adds_rate_limit_sleep() -> None:
    retry_policy = RetryPolicy(
        max_attempts=2,
        initial_delay_seconds=0.05,
        jitter_proportion=0,
    )
    client, _, transport, clock, sleeper, _ = _client(
        [_response(500), _response(200)],
        retry_policy=retry_policy,
    )

    client.send(_sec_request())

    assert len(transport.requests) == 2
    assert sleeper.delays == pytest.approx([0.05, 0.15])
    assert isinstance(clock, _MutableClock)
    assert clock.value == pytest.approx(0.2)
    assert client.rate_limit_state.last_request_start_time_seconds == pytest.approx(0.2)


def test_retry_delay_sufficient_for_rate_limit_needs_no_extra_sleep() -> None:
    client, _, transport, clock, sleeper, _ = _client([_response(500), _response(200)])

    client.send(_sec_request())

    assert len(transport.requests) == 2
    assert sleeper.delays == [1.0]
    assert isinstance(clock, _MutableClock)
    assert clock.value == 1.0
    assert client.rate_limit_state.last_request_start_time_seconds == 1.0


@pytest.mark.parametrize("status_code", [429, 500, 503])
def test_retryable_http_status_can_recover(status_code: int) -> None:
    retry_policy = _RecordingRetryPolicy(
        max_attempts=2,
        initial_delay_seconds=1,
        jitter_proportion=0,
    )
    response = _response(200)
    client, _, transport, _, sleeper, jitter = _client(
        [_response(status_code), response],
        retry_policy=retry_policy,
    )

    returned = client.send(_sec_request())

    assert returned is response
    assert len(transport.requests) == 2
    assert retry_policy.calls == [
        (
            1,
            RetryOutcome.HTTP_RESPONSE,
            0.5,
            status_code,
        )
    ]
    assert sleeper.delays == [1.0]
    assert jitter.calls == 1


@pytest.mark.parametrize(
    ("status_code", "expected_error"),
    [
        (404, SecNotFoundError),
        (400, SecResponseError),
        (403, SecResponseError),
        (410, SecResponseError),
    ],
)
def test_non_retryable_http_status_maps_without_second_attempt(
    status_code: int,
    expected_error: type[SecResponseError],
) -> None:
    client, _, transport, _, sleeper, jitter = _client([_response(status_code)])

    with pytest.raises(expected_error) as exception_info:
        client.send(_sec_request())

    assert type(exception_info.value) is expected_error
    assert len(transport.requests) == 1
    assert sleeper.delays == []
    assert jitter.calls == 1


def test_custom_retry_policy_controls_normally_non_retryable_status() -> None:
    retry_policy = RetryPolicy(
        max_attempts=2,
        initial_delay_seconds=1,
        jitter_proportion=0,
        retryable_status_codes={400},
    )
    response = _response(200)
    client, _, transport, _, sleeper, _ = _client(
        [_response(400), response],
        retry_policy=retry_policy,
    )

    assert client.send(_sec_request()) is response
    assert len(transport.requests) == 2
    assert sleeper.delays == [1.0]


@pytest.mark.parametrize(
    ("status_code", "expected_error"),
    [
        (429, SecRateLimitError),
        (500, SecServerError),
        (503, SecServerError),
        (404, SecNotFoundError),
        (400, SecResponseError),
    ],
)
def test_final_http_response_maps_last_attempt_at_exhaustion(
    status_code: int,
    expected_error: type[SecResponseError],
) -> None:
    retryable_statuses = {status_code}
    retry_policy = RetryPolicy(
        max_attempts=2,
        initial_delay_seconds=1,
        jitter_proportion=0,
        retryable_status_codes=retryable_statuses,
    )
    client, _, transport, _, sleeper, jitter = _client(
        [_response(status_code), _response(status_code)],
        retry_policy=retry_policy,
    )

    with pytest.raises(expected_error) as exception_info:
        client.send(_sec_request())

    assert type(exception_info.value) is expected_error
    assert exception_info.value.status_code == status_code
    assert len(transport.requests) == 2
    assert sleeper.delays == [1.0]
    assert jitter.calls == 2


def test_timeout_failure_retries_then_returns_later_success() -> None:
    timeout = HttpTimeoutError(timeout_seconds=10)
    response = _response()
    client, _, transport, _, sleeper, jitter = _client([timeout, response])

    assert client.send(_sec_request()) is response
    assert len(transport.requests) == 2
    assert sleeper.delays == [1.0]
    assert jitter.calls == 1


def test_timeout_exhaustion_translates_safely_without_visible_chain() -> None:
    timeout = HttpTimeoutError(timeout_seconds=10)
    timeout.args = ("RAW_TIMEOUT_MARKER_31A9",)
    client, _, transport, _, _, _ = _client(
        [timeout],
        retry_policy=RetryPolicy(max_attempts=1),
    )

    with pytest.raises(SecTimeoutError) as exception_info:
        client.send(_sec_request())

    error = exception_info.value
    assert len(transport.requests) == 1
    assert error.timeout_seconds == 10.0
    assert error.request_url == "https://data.sec.gov/path"
    assert str(error) == "SEC request timed out."
    assert "RAW_TIMEOUT_MARKER_31A9" not in str(error)
    assert "RAW_TIMEOUT_MARKER_31A9" not in repr(error)
    assert error.__cause__ is None
    assert error.__suppress_context__


def test_generic_transport_failure_retries_then_returns_later_success() -> None:
    response = _response()
    client, _, transport, _, sleeper, jitter = _client([HttpTransportError(), response])

    assert client.send(_sec_request()) is response
    assert len(transport.requests) == 2
    assert sleeper.delays == [1.0]
    assert jitter.calls == 1


def test_generic_transport_exhaustion_translates_safely() -> None:
    failure = HttpTransportError()
    failure.args = ("RAW_TRANSPORT_MARKER_42BA",)
    client, _, transport, _, _, _ = _client(
        [failure],
        retry_policy=RetryPolicy(max_attempts=1),
    )

    with pytest.raises(SecTransportError) as exception_info:
        client.send(_sec_request())

    error = exception_info.value
    assert len(transport.requests) == 1
    assert type(error) is SecTransportError
    assert error.request_url == "https://data.sec.gov/path"
    assert str(error) == "SEC request transport failed."
    assert "RAW_TRANSPORT_MARKER_42BA" not in str(error)
    assert "RAW_TRANSPORT_MARKER_42BA" not in repr(error)
    assert error.__cause__ is None
    assert error.__suppress_context__


def test_failed_attempts_persist_limiter_state_across_later_calls() -> None:
    client, _, transport, clock, sleeper, _ = _client(
        [HttpTransportError(), _response()],
        retry_policy=RetryPolicy(max_attempts=1),
    )

    with pytest.raises(SecTransportError):
        client.send(_sec_request())
    assert client.rate_limit_state.last_request_start_time_seconds == 0.0

    client.send(_sec_request())

    assert len(transport.requests) == 2
    assert sleeper.delays == pytest.approx([0.2])
    assert isinstance(clock, _MutableClock)
    assert clock.value == pytest.approx(0.2)


@pytest.mark.parametrize(
    ("dependency", "failure_factory"),
    [
        ("transport", lambda: ArithmeticError("transport-programming-marker")),
        ("clock", lambda: LookupError("clock-programming-marker")),
        ("sleeper", lambda: OSError("sleeper-programming-marker")),
        ("jitter", lambda: RuntimeError("jitter-programming-marker")),
    ],
)
def test_unexpected_dependency_exceptions_propagate(
    dependency: str,
    failure_factory: Callable[[], BaseException],
) -> None:
    failure = failure_factory()
    clock = _MutableClock(error=failure if dependency == "clock" else None)
    sleeper = _Sleeper(
        clock,
        error=failure if dependency == "sleeper" else None,
    )
    jitter = _JitterSamples(error=failure if dependency == "jitter" else None)
    outcomes: list[HttpResponse | BaseException] = [
        failure if dependency == "transport" else _response(500)
    ]
    client, _, _, _, _, _ = _client(
        outcomes,
        clock=clock,
        sleeper=sleeper,
        jitter=jitter,
    )

    with pytest.raises(type(failure), match=str(failure)):
        client.send(_sec_request())


def test_max_attempts_one_performs_exactly_one_transport_attempt() -> None:
    client, _, transport, _, sleeper, jitter = _client(
        [_response(503)],
        retry_policy=RetryPolicy(max_attempts=1),
    )

    with pytest.raises(SecServerError):
        client.send(_sec_request())

    assert len(transport.requests) == 1
    assert sleeper.delays == []
    assert jitter.calls == 1


def test_exact_maximum_attempts_and_one_based_numbering_are_respected() -> None:
    policy = _RecordingRetryPolicy(
        max_attempts=3,
        initial_delay_seconds=1,
        jitter_proportion=0,
    )
    client, _, transport, _, sleeper, _ = _client(
        [_response(503), _response(503), _response(503)],
        retry_policy=policy,
    )

    with pytest.raises(SecServerError):
        client.send(_sec_request())

    assert len(transport.requests) == 3
    assert [item[0] for item in policy.calls] == [1, 2, 3]
    assert sleeper.delays == [1.0, 2.0]


def test_zero_retry_delay_does_not_call_sleeper() -> None:
    retry_policy = RetryPolicy(
        max_attempts=2,
        initial_delay_seconds=float.fromhex("0x0.0000000000001p-1022"),
        max_delay_seconds=1,
        jitter_proportion=0.9,
    )
    clock = _SequenceClock([0.0, 1.0])
    sleeper = _Sleeper()
    client, _, transport, _, _, _ = _client(
        [_response(500), _response(200)],
        retry_policy=retry_policy,
        rate_limit_policy=RateLimitPolicy(max_requests_per_second=1),
        clock=clock,
        sleeper=sleeper,
        jitter=_JitterSamples([0.0]),
    )

    client.send(_sec_request())

    assert len(transport.requests) == 2
    assert sleeper.delays == []


def test_injected_jitter_samples_produce_policy_approved_delays() -> None:
    retry_policy = RetryPolicy(
        max_attempts=3,
        initial_delay_seconds=2,
        max_delay_seconds=10,
        jitter_proportion=0.5,
    )
    jitter = _JitterSamples([0.0, 1.0])
    client, _, _, _, sleeper, _ = _client(
        [_response(500), _response(500), _response(200)],
        retry_policy=retry_policy,
        jitter=jitter,
    )

    client.send(_sec_request())

    assert sleeper.delays == [1.0, 6.0]
    assert jitter.calls == 2


def test_invalid_jitter_sample_fails_through_retry_policy_validation() -> None:
    client, _, transport, _, sleeper, jitter = _client(
        [_response(500)],
        jitter=_JitterSamples([1.5]),
    )

    with pytest.raises(ValueError, match="jitter_sample"):
        client.send(_sec_request())

    assert len(transport.requests) == 1
    assert sleeper.delays == []
    assert jitter.calls == 1


def test_http_failure_persists_limiter_state_across_later_calls() -> None:
    client, _, transport, clock, sleeper, _ = _client([_response(404), _response(200)])

    with pytest.raises(SecNotFoundError):
        client.send(_sec_request())
    client.send(_sec_request())

    assert len(transport.requests) == 2
    assert sleeper.delays == pytest.approx([0.2])
    assert isinstance(clock, _MutableClock)
    assert clock.value == pytest.approx(0.2)


def test_client_retains_only_safe_limiter_state_not_operation_objects() -> None:
    query_marker = "QUERY_MARKER_53CB"
    user_agent_marker = "USER_AGENT_MARKER_64DC"
    request_header_marker = "REQUEST_HEADER_MARKER_75ED"
    response_header_marker = "RESPONSE_HEADER_MARKER_86FE"
    response_body_marker = b"RESPONSE_BODY_MARKER_97AF"
    request = HttpRequest(
        method="GET",
        url=f"https://data.sec.gov/path?item={query_marker}",
        headers={
            "User-Agent": user_agent_marker,
            "X-Synthetic": request_header_marker,
        },
        timeout_seconds=10,
    )
    builder = _FakeBuilder(request)
    client, _, _, _, _, _ = _client(
        [
            _response(
                500,
                headers={"X-Synthetic": response_header_marker},
                body=response_body_marker,
            )
        ],
        retry_policy=RetryPolicy(max_attempts=1),
        builder=builder,
    )

    with pytest.raises(SecServerError) as exception_info:
        client.send(_sec_request())

    error = exception_info.value
    exposed = (
        str(error),
        repr(error),
        str(error.request_url),
        repr(client.rate_limit_state),
        repr(client),
    )
    for value in exposed:
        assert query_marker not in value
        assert user_agent_marker not in value
        assert request_header_marker not in value
        assert response_header_marker not in value
        assert response_body_marker.decode() not in value
    assert error.request_url == "https://data.sec.gov/path"
    assert not hasattr(error, "request")
    assert not hasattr(error, "response")
    assert not hasattr(client, "request")
    assert not hasattr(client, "response")
    assert client.rate_limit_state == RateLimitState(last_request_start_time_seconds=0)


def test_sec_client_is_exported_only_from_sec_package() -> None:
    assert sec_providers.SecClient is SecClient
    assert "SecClient" in sec_providers.__all__
    assert "SecClient" not in generic_providers.__all__
    assert not hasattr(generic_providers, "SecClient")
