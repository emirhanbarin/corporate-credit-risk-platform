"""Pure fixed-interval pacing with caller-supplied monotonic timestamps."""

from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class RateLimitState:
    """Immutable record of the most recent admitted request start."""

    last_request_start_time_seconds: float | None = None

    def __post_init__(self) -> None:
        if self.last_request_start_time_seconds is None:
            return
        timestamp = _validate_timestamp(self.last_request_start_time_seconds)
        object.__setattr__(
            self,
            "last_request_start_time_seconds",
            timestamp,
        )


@dataclass(frozen=True, slots=True)
class RateLimitDecision:
    """Immutable result of evaluating whether a request may start."""

    can_start_immediately: bool
    delay_seconds: float
    earliest_start_time_seconds: float

    def __post_init__(self) -> None:
        if not isinstance(self.can_start_immediately, bool):
            raise ValueError("can_start_immediately must be a boolean.")
        delay = _validate_non_negative_number(
            self.delay_seconds,
            "delay_seconds",
        )
        earliest = _validate_non_negative_number(
            self.earliest_start_time_seconds,
            "earliest_start_time_seconds",
        )
        if self.can_start_immediately and delay != 0.0:
            raise ValueError("an immediate rate-limit decision must have zero delay.")
        if not self.can_start_immediately and delay == 0.0:
            raise ValueError("a waiting rate-limit decision must have positive delay.")

        object.__setattr__(self, "delay_seconds", delay)
        object.__setattr__(self, "earliest_start_time_seconds", earliest)


@dataclass(frozen=True, slots=True)
class RateLimitPolicy:
    """Immutable fixed-interval policy that never reads clocks or sleeps.

    The minimum interval is ``1 / max_requests_per_second``. ``evaluate`` uses a
    caller-supplied monotonic timestamp and never records a start. After any
    externally performed wait, the caller supplies the actual monotonic start time
    to ``record_start``. Wall clocks, request execution, retry-delay composition,
    and sleeping belong to future orchestration.
    """

    max_requests_per_second: float
    minimum_interval_seconds: float = field(init=False)

    def __post_init__(self) -> None:
        rate = _validate_positive_number(
            self.max_requests_per_second,
            "max_requests_per_second",
        )
        interval = 1.0 / rate
        if not math.isfinite(interval) or interval <= 0.0:
            raise ValueError(
                "max_requests_per_second must produce a positive finite interval."
            )

        object.__setattr__(self, "max_requests_per_second", rate)
        object.__setattr__(self, "minimum_interval_seconds", interval)

    def evaluate(
        self,
        *,
        state: RateLimitState,
        current_time_seconds: float,
    ) -> RateLimitDecision:
        """Calculate pacing at a caller-supplied monotonic time without side effects."""
        validated_state = _validate_state(state)
        current_time = _validate_timestamp(current_time_seconds)
        previous_start = validated_state.last_request_start_time_seconds

        if previous_start is None:
            return RateLimitDecision(
                can_start_immediately=True,
                delay_seconds=0.0,
                earliest_start_time_seconds=current_time,
            )
        if current_time < previous_start:
            raise ValueError(
                "current_time_seconds must not precede the recorded request start."
            )

        earliest_start = self._next_start_time(previous_start)
        if current_time >= earliest_start:
            return RateLimitDecision(
                can_start_immediately=True,
                delay_seconds=0.0,
                earliest_start_time_seconds=earliest_start,
            )

        delay = earliest_start - current_time
        return RateLimitDecision(
            can_start_immediately=False,
            delay_seconds=delay,
            earliest_start_time_seconds=earliest_start,
        )

    def record_start(
        self,
        *,
        state: RateLimitState,
        start_time_seconds: float,
    ) -> RateLimitState:
        """Return new state after validating an actual monotonic request start."""
        validated_state = _validate_state(state)
        start_time = _validate_timestamp(start_time_seconds)
        previous_start = validated_state.last_request_start_time_seconds

        if previous_start is not None:
            if start_time < previous_start:
                raise ValueError(
                    "start_time_seconds must not precede the recorded request start."
                )
            earliest_start = self._next_start_time(previous_start)
            if start_time < earliest_start:
                raise ValueError(
                    "start_time_seconds must not precede the permitted request start."
                )

        return RateLimitState(last_request_start_time_seconds=start_time)

    def _next_start_time(self, previous_start: float) -> float:
        earliest_start = previous_start + self.minimum_interval_seconds
        if not math.isfinite(earliest_start):
            raise ValueError("rate-limit timestamp arithmetic must remain finite.")
        if earliest_start <= previous_start:
            raise ValueError(
                "rate-limit timestamp arithmetic must advance monotonically."
            )
        return earliest_start


def _validate_state(value: RateLimitState) -> RateLimitState:
    if not isinstance(value, RateLimitState):
        raise ValueError("state must be a RateLimitState.")
    return value


def _validate_timestamp(value: float) -> float:
    return _validate_non_negative_number(value, "monotonic timestamp")


def _validate_positive_number(value: float, field_name: str) -> float:
    converted = _validate_finite_number(value, field_name)
    if converted <= 0.0:
        raise ValueError(f"{field_name} must be a positive finite number.")
    return converted


def _validate_non_negative_number(value: float, field_name: str) -> float:
    converted = _validate_finite_number(value, field_name)
    if converted < 0.0:
        raise ValueError(f"{field_name} must be a non-negative finite number.")
    return 0.0 if converted == 0.0 else converted


def _validate_finite_number(value: float, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a finite number.")
    try:
        converted = float(value)
    except OverflowError as error:
        raise ValueError(f"{field_name} must be a finite number.") from error
    if not math.isfinite(converted):
        raise ValueError(f"{field_name} must be a finite number.")
    return converted
