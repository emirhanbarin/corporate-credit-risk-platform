"""Pure retry decisions without request execution, sleeping, clocks, or randomness."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum

_DEFAULT_RETRYABLE_STATUS_CODES = frozenset({408, 429, 500, 502, 503, 504})


class RetryOutcome(Enum):
    """A completed attempt outcome already narrowed for generic retry policy."""

    RETRYABLE_TRANSPORT_FAILURE = "retryable_transport_failure"
    NON_RETRYABLE_TRANSPORT_FAILURE = "non_retryable_transport_failure"
    HTTP_RESPONSE = "http_response"


class RetryDecisionReason(Enum):
    """The exhaustive reason for a retry decision."""

    RETRY_ALLOWED = "retry_allowed"
    OUTCOME_NOT_RETRYABLE = "outcome_not_retryable"
    ATTEMPTS_EXHAUSTED = "attempts_exhausted"


@dataclass(frozen=True, slots=True)
class RetryDecision:
    """An immutable retry decision with no request or response data."""

    reason: RetryDecisionReason
    delay_seconds: float | None

    def __post_init__(self) -> None:
        if not isinstance(self.reason, RetryDecisionReason):
            raise ValueError("reason must be a RetryDecisionReason.")

        if self.reason is RetryDecisionReason.RETRY_ALLOWED:
            delay = _validate_non_negative_finite_number(
                self.delay_seconds,
                "delay_seconds",
            )
            object.__setattr__(self, "delay_seconds", delay)
        elif self.delay_seconds is not None:
            raise ValueError("delay_seconds must be absent when retry is denied.")

    @property
    def should_retry(self) -> bool:
        """Return whether the caller may make one more attempt."""
        return self.reason is RetryDecisionReason.RETRY_ALLOWED


@dataclass(frozen=True, slots=True, init=False)
class RetryPolicy:
    """Immutable total-attempt, backoff, and retry-classification policy.

    ``max_attempts`` includes the initial request. Attempts are one-based, and
    ``decide`` is called after the supplied attempt completes. Nominal delay is
    ``initial_delay_seconds * 2 ** (attempt_number - 1)``, capped at
    ``max_delay_seconds``.

    Jitter is deterministic and caller-supplied. For jitter proportion ``p`` and
    normalized sample ``s``, the bounded symmetric factor is
    ``1 - p + 2 * p * s``. A pre-interpreted ``retry_after_seconds`` is a minimum
    delay hint; the final delay remains capped. Raw Retry-After parsing, HTTP-date
    interpretation, request execution, sleeping, clocks, and randomness belong to
    later orchestration.
    """

    max_attempts: int
    initial_delay_seconds: float
    max_delay_seconds: float
    jitter_proportion: float
    retryable_status_codes: frozenset[int]

    def __init__(
        self,
        *,
        max_attempts: int = 3,
        initial_delay_seconds: float = 1.0,
        max_delay_seconds: float = 60.0,
        jitter_proportion: float = 0.2,
        retryable_status_codes: Iterable[int] = _DEFAULT_RETRYABLE_STATUS_CODES,
    ) -> None:
        validated_attempts = _validate_max_attempts(max_attempts)
        validated_initial = _validate_positive_finite_number(
            initial_delay_seconds,
            "initial_delay_seconds",
        )
        validated_maximum = _validate_positive_finite_number(
            max_delay_seconds,
            "max_delay_seconds",
        )
        if validated_maximum < validated_initial:
            raise ValueError(
                "max_delay_seconds must be greater than or equal to "
                "initial_delay_seconds."
            )
        validated_jitter = _validate_jitter_proportion(jitter_proportion)
        validated_statuses = _copy_and_validate_status_codes(retryable_status_codes)

        object.__setattr__(self, "max_attempts", validated_attempts)
        object.__setattr__(self, "initial_delay_seconds", validated_initial)
        object.__setattr__(self, "max_delay_seconds", validated_maximum)
        object.__setattr__(self, "jitter_proportion", validated_jitter)
        object.__setattr__(self, "retryable_status_codes", validated_statuses)

    def decide(
        self,
        *,
        attempt_number: int,
        outcome: RetryOutcome,
        jitter_sample: float,
        http_status_code: int | None = None,
        retry_after_seconds: float | None = None,
    ) -> RetryDecision:
        """Evaluate one completed attempt without executing or delaying work."""
        validated_attempt = _validate_attempt_number(attempt_number)
        validated_outcome = _validate_outcome(outcome)
        validated_status = _validate_outcome_status(
            validated_outcome,
            http_status_code,
        )
        validated_sample = _validate_jitter_sample(jitter_sample)
        validated_retry_after = _validate_retry_after(retry_after_seconds)

        if not self._is_retryable(validated_outcome, validated_status):
            return RetryDecision(
                reason=RetryDecisionReason.OUTCOME_NOT_RETRYABLE,
                delay_seconds=None,
            )
        if validated_attempt >= self.max_attempts:
            return RetryDecision(
                reason=RetryDecisionReason.ATTEMPTS_EXHAUSTED,
                delay_seconds=None,
            )

        nominal_delay = self._nominal_delay(validated_attempt)
        jittered_delay = self._apply_jitter(nominal_delay, validated_sample)
        delay = jittered_delay
        if validated_retry_after is not None:
            delay = max(delay, validated_retry_after)
        delay = min(delay, self.max_delay_seconds)

        return RetryDecision(
            reason=RetryDecisionReason.RETRY_ALLOWED,
            delay_seconds=delay,
        )

    def _is_retryable(
        self,
        outcome: RetryOutcome,
        http_status_code: int | None,
    ) -> bool:
        if outcome is RetryOutcome.RETRYABLE_TRANSPORT_FAILURE:
            return True
        if outcome is RetryOutcome.NON_RETRYABLE_TRANSPORT_FAILURE:
            return False
        assert http_status_code is not None
        return http_status_code in self.retryable_status_codes

    def _nominal_delay(self, attempt_number: int) -> float:
        exponent = attempt_number - 1
        initial_mantissa, initial_exponent = math.frexp(self.initial_delay_seconds)
        maximum_mantissa, maximum_exponent = math.frexp(self.max_delay_seconds)
        cap_exponent = maximum_exponent - initial_exponent
        if initial_mantissa < maximum_mantissa:
            cap_exponent += 1
        if exponent >= cap_exponent:
            return self.max_delay_seconds

        delay = math.ldexp(self.initial_delay_seconds, exponent)
        return min(delay, self.max_delay_seconds)

    def _apply_jitter(self, nominal_delay: float, jitter_sample: float) -> float:
        if self.jitter_proportion == 0.0:
            return nominal_delay

        factor = (
            1.0
            - self.jitter_proportion
            + (2.0 * self.jitter_proportion * jitter_sample)
        )
        if factor > 1.0 and nominal_delay > self.max_delay_seconds / factor:
            return self.max_delay_seconds
        return min(nominal_delay * factor, self.max_delay_seconds)


def _validate_max_attempts(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError("max_attempts must be a positive integer.")
    return value


def _validate_attempt_number(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError("attempt_number must be a positive integer.")
    return value


def _validate_positive_finite_number(value: float, field: str) -> float:
    converted = _as_finite_float(value, field)
    if converted <= 0.0:
        raise ValueError(f"{field} must be a positive finite number.")
    return converted


def _validate_non_negative_finite_number(
    value: float | None,
    field: str,
) -> float:
    converted = _as_finite_float(value, field)
    if converted < 0.0:
        raise ValueError(f"{field} must be a non-negative finite number.")
    return converted


def _as_finite_float(value: float | None, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a finite number.")
    try:
        converted = float(value)
    except OverflowError as error:
        raise ValueError(f"{field} must be a finite number.") from error
    if not math.isfinite(converted):
        raise ValueError(f"{field} must be a finite number.")
    return converted


def _validate_jitter_proportion(value: float) -> float:
    converted = _as_finite_float(value, "jitter_proportion")
    if not 0.0 <= converted < 1.0:
        raise ValueError(
            "jitter_proportion must be greater than or equal to zero and less than one."
        )
    return converted


def _copy_and_validate_status_codes(values: Iterable[int]) -> frozenset[int]:
    try:
        copied = tuple(values)
    except TypeError as error:
        raise ValueError(
            "retryable_status_codes must be an iterable of integers."
        ) from error

    for status_code in copied:
        if (
            isinstance(status_code, bool)
            or not isinstance(status_code, int)
            or not 100 <= status_code <= 599
        ):
            raise ValueError(
                "retryable_status_codes must contain HTTP status integers "
                "from 100 through 599."
            )
    return frozenset(copied)


def _validate_outcome(value: RetryOutcome) -> RetryOutcome:
    if not isinstance(value, RetryOutcome):
        raise ValueError("outcome must be a RetryOutcome.")
    return value


def _validate_outcome_status(
    outcome: RetryOutcome,
    status_code: int | None,
) -> int | None:
    if outcome is RetryOutcome.HTTP_RESPONSE:
        if (
            isinstance(status_code, bool)
            or not isinstance(status_code, int)
            or not 100 <= status_code <= 599
        ):
            raise ValueError(
                "http_status_code must be an HTTP status integer from 100 through 599."
            )
        return status_code
    if status_code is not None:
        raise ValueError("http_status_code must be absent for transport outcomes.")
    return None


def _validate_jitter_sample(value: float) -> float:
    converted = _as_finite_float(value, "jitter_sample")
    if not 0.0 <= converted <= 1.0:
        raise ValueError("jitter_sample must be from zero through one.")
    return converted


def _validate_retry_after(value: float | None) -> float | None:
    if value is None:
        return None
    return _validate_non_negative_finite_number(value, "retry_after_seconds")
