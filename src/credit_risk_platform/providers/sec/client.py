"""Synchronous, dependency-injected orchestration for generic SEC requests."""

from __future__ import annotations

from typing import Protocol, cast

from credit_risk_platform.providers.http import (
    HttpRequest,
    HttpResponse,
    HttpTransport,
)
from credit_risk_platform.providers.rate_limit import RateLimitPolicy, RateLimitState
from credit_risk_platform.providers.retry import RetryOutcome, RetryPolicy
from credit_risk_platform.providers.sec.errors import (
    SecTimeoutError,
    SecTransportError,
)
from credit_risk_platform.providers.sec.models import SecRequest
from credit_risk_platform.providers.sec.response_mapper import (
    _is_success_status,
    validate_sec_response,
)
from credit_risk_platform.providers.urllib_transport import (
    HttpTimeoutError,
    HttpTransportError,
)

_MAX_RATE_LIMIT_ADMISSION_CHECKS = 3
_PACING_FAILURE_MESSAGE = "SEC request pacing could not obtain an admissible start."


class _RequestBuilder(Protocol):
    def build(self, request: SecRequest) -> HttpRequest:
        """Build one immutable HTTP request."""
        ...


class _MonotonicClock(Protocol):
    def __call__(self) -> float:
        """Return caller-owned monotonic seconds."""
        ...


class _Sleeper(Protocol):
    def __call__(self, delay_seconds: float) -> None:
        """Wait for the supplied non-negative duration."""
        ...


class _JitterSampleProvider(Protocol):
    def __call__(self) -> float:
        """Return one deterministic normalized jitter sample."""
        ...


class SecClient:
    """Execute serialized SEC operations with injected transport and timing.

    One logical ``send`` builds one request and may make multiple one-based
    transport attempts. Every attempt is rate-limited before transport execution.
    Retry delay is slept first; rate-limit pacing is then independently rechecked.
    The client does not parse JSON and is not designed for concurrent use.
    """

    __slots__ = (
        "_builder",
        "_clock",
        "_jitter_sample_provider",
        "_rate_limit_policy",
        "_rate_limit_state",
        "_retry_policy",
        "_sleeper",
        "_transport",
    )

    def __init__(
        self,
        *,
        builder: _RequestBuilder,
        transport: HttpTransport,
        retry_policy: RetryPolicy,
        rate_limit_policy: RateLimitPolicy,
        clock: _MonotonicClock,
        sleeper: _Sleeper,
        jitter_sample_provider: _JitterSampleProvider,
    ) -> None:
        if not callable(getattr(builder, "build", None)):
            raise ValueError("builder must provide a callable build method.")
        if not callable(getattr(transport, "send", None)):
            raise ValueError("transport must provide a callable send method.")
        if not isinstance(retry_policy, RetryPolicy):
            raise ValueError("retry_policy must be a RetryPolicy.")
        if not isinstance(rate_limit_policy, RateLimitPolicy):
            raise ValueError("rate_limit_policy must be a RateLimitPolicy.")
        if not callable(clock):
            raise ValueError("clock must be callable.")
        if not callable(sleeper):
            raise ValueError("sleeper must be callable.")
        if not callable(jitter_sample_provider):
            raise ValueError("jitter_sample_provider must be callable.")

        self._builder = builder
        self._transport = transport
        self._retry_policy = retry_policy
        self._rate_limit_policy = rate_limit_policy
        self._clock = clock
        self._sleeper = sleeper
        self._jitter_sample_provider = jitter_sample_provider
        self._rate_limit_state = RateLimitState()

    @property
    def rate_limit_state(self) -> RateLimitState:
        """Return the current immutable pacing state."""
        return self._rate_limit_state

    def send(self, request: SecRequest) -> HttpResponse:
        """Execute one logical SEC operation and return its successful response."""
        if not isinstance(request, SecRequest):
            raise ValueError("request must be a SecRequest.")

        http_request = self._builder.build(request)
        attempt_number = 1

        while True:
            self._admit_attempt()
            try:
                response = self._transport.send(http_request)
            except HttpTimeoutError as error:
                if self._should_retry(
                    attempt_number=attempt_number,
                    outcome=RetryOutcome.RETRYABLE_TRANSPORT_FAILURE,
                ):
                    attempt_number += 1
                    continue
                raise SecTimeoutError(
                    request_url=http_request.url,
                    timeout_seconds=error.timeout_seconds,
                ) from None
            except HttpTransportError:
                if self._should_retry(
                    attempt_number=attempt_number,
                    outcome=RetryOutcome.RETRYABLE_TRANSPORT_FAILURE,
                ):
                    attempt_number += 1
                    continue
                raise SecTransportError(request_url=http_request.url) from None

            if _is_success_status(response.status_code):
                return validate_sec_response(
                    response,
                    request_url=http_request.url,
                )

            if self._should_retry(
                attempt_number=attempt_number,
                outcome=RetryOutcome.HTTP_RESPONSE,
                http_status_code=response.status_code,
            ):
                attempt_number += 1
                continue
            return validate_sec_response(
                response,
                request_url=http_request.url,
            )

    def _admit_attempt(self) -> None:
        for check_number in range(_MAX_RATE_LIMIT_ADMISSION_CHECKS):
            current_time = self._clock()
            decision = self._rate_limit_policy.evaluate(
                state=self._rate_limit_state,
                current_time_seconds=current_time,
            )
            if decision.can_start_immediately:
                self._rate_limit_state = self._rate_limit_policy.record_start(
                    state=self._rate_limit_state,
                    start_time_seconds=current_time,
                )
                return
            if check_number < _MAX_RATE_LIMIT_ADMISSION_CHECKS - 1:
                self._sleeper(decision.delay_seconds)

        raise RuntimeError(_PACING_FAILURE_MESSAGE)

    def _should_retry(
        self,
        *,
        attempt_number: int,
        outcome: RetryOutcome,
        http_status_code: int | None = None,
    ) -> bool:
        decision = self._retry_policy.decide(
            attempt_number=attempt_number,
            outcome=outcome,
            jitter_sample=self._jitter_sample_provider(),
            http_status_code=http_status_code,
        )
        if not decision.should_retry:
            return False

        delay_seconds = cast(float, decision.delay_seconds)
        if delay_seconds > 0.0:
            self._sleeper(delay_seconds)
        return True
