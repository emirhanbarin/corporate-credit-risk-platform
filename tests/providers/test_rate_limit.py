"""Tests for deterministic fixed-interval request pacing."""

from dataclasses import FrozenInstanceError, fields
from sys import float_info

import pytest

import credit_risk_platform.providers as providers
from credit_risk_platform.providers import (
    RateLimitDecision,
    RateLimitPolicy,
    RateLimitState,
)


def test_policy_accepts_integer_and_float_rates_and_derives_interval() -> None:
    integer_policy = RateLimitPolicy(max_requests_per_second=5)
    float_policy = RateLimitPolicy(max_requests_per_second=2.5)

    assert integer_policy.max_requests_per_second == 5.0
    assert integer_policy.minimum_interval_seconds == 0.2
    assert float_policy.max_requests_per_second == 2.5
    assert float_policy.minimum_interval_seconds == 0.4


def test_policy_is_frozen() -> None:
    policy = RateLimitPolicy(max_requests_per_second=5)

    with pytest.raises(FrozenInstanceError):
        policy.max_requests_per_second = 10  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        policy.minimum_interval_seconds = 0.1  # type: ignore[misc]


@pytest.mark.parametrize(
    "rate",
    [
        True,
        0,
        -1,
        float("nan"),
        float("inf"),
        float("-inf"),
        "5",
        None,
    ],
)
def test_invalid_rates_are_rejected(rate: object) -> None:
    with pytest.raises(ValueError, match="max_requests_per_second"):
        RateLimitPolicy(max_requests_per_second=rate)  # type: ignore[arg-type]


def test_integer_rate_too_large_for_finite_float_is_rejected() -> None:
    with pytest.raises(ValueError, match="max_requests_per_second"):
        RateLimitPolicy(max_requests_per_second=10**10000)


def test_rate_that_produces_non_finite_interval_is_rejected() -> None:
    with pytest.raises(ValueError, match="positive finite interval"):
        RateLimitPolicy(
            max_requests_per_second=float.fromhex("0x0.0000000000001p-1022")
        )


def test_extreme_finite_rate_with_positive_interval_is_accepted() -> None:
    policy = RateLimitPolicy(max_requests_per_second=float_info.max)

    assert policy.minimum_interval_seconds > 0.0
    assert policy.minimum_interval_seconds < float_info.min


def test_empty_and_populated_states_are_normalized_and_frozen() -> None:
    empty = RateLimitState()
    populated = RateLimitState(last_request_start_time_seconds=10)

    assert empty.last_request_start_time_seconds is None
    assert populated.last_request_start_time_seconds == 10.0
    with pytest.raises(FrozenInstanceError):
        populated.last_request_start_time_seconds = 20.0  # type: ignore[misc]


@pytest.mark.parametrize(
    "timestamp",
    [
        True,
        -1,
        float("nan"),
        float("inf"),
        float("-inf"),
        "10",
    ],
)
def test_invalid_state_timestamps_are_rejected(timestamp: object) -> None:
    with pytest.raises(ValueError, match="monotonic timestamp"):
        RateLimitState(
            last_request_start_time_seconds=timestamp  # type: ignore[arg-type]
        )


def test_negative_zero_timestamp_is_normalized_to_zero() -> None:
    state = RateLimitState(last_request_start_time_seconds=-0.0)

    assert state.last_request_start_time_seconds == 0.0
    assert str(state.last_request_start_time_seconds) == "0.0"


def test_first_request_is_immediate_and_evaluation_does_not_record() -> None:
    policy = RateLimitPolicy(max_requests_per_second=5)
    state = RateLimitState()

    decision = policy.evaluate(state=state, current_time_seconds=10)

    assert decision == RateLimitDecision(
        can_start_immediately=True,
        delay_seconds=0.0,
        earliest_start_time_seconds=10.0,
    )
    assert state == RateLimitState()


def test_recording_first_start_returns_new_state() -> None:
    policy = RateLimitPolicy(max_requests_per_second=5)
    original = RateLimitState()

    recorded = policy.record_start(state=original, start_time_seconds=10)

    assert recorded == RateLimitState(last_request_start_time_seconds=10.0)
    assert recorded is not original
    assert original.last_request_start_time_seconds is None


@pytest.mark.parametrize(
    ("rate", "expected_interval"),
    [(1, 1.0), (2, 0.5), (5, 0.2), (10, 0.1)],
)
def test_realistic_rates_enforce_fixed_intervals(
    rate: float,
    expected_interval: float,
) -> None:
    policy = RateLimitPolicy(max_requests_per_second=rate)
    state = RateLimitState(last_request_start_time_seconds=10)

    decision = policy.evaluate(state=state, current_time_seconds=10)

    assert not decision.can_start_immediately
    assert decision.delay_seconds == pytest.approx(expected_interval)
    assert decision.earliest_start_time_seconds == pytest.approx(10 + expected_interval)


def test_request_before_interval_has_correct_positive_delay() -> None:
    policy = RateLimitPolicy(max_requests_per_second=5)
    state = RateLimitState(last_request_start_time_seconds=10)

    decision = policy.evaluate(state=state, current_time_seconds=10.05)

    assert not decision.can_start_immediately
    assert decision.delay_seconds == pytest.approx(0.15)
    assert decision.delay_seconds > 0.0
    assert decision.earliest_start_time_seconds == pytest.approx(10.2)
    assert decision.earliest_start_time_seconds > 10.05


def test_request_at_exact_computed_boundary_is_immediate() -> None:
    policy = RateLimitPolicy(max_requests_per_second=5)
    state = RateLimitState(last_request_start_time_seconds=10)
    waiting = policy.evaluate(state=state, current_time_seconds=10)

    boundary = policy.evaluate(
        state=state,
        current_time_seconds=waiting.earliest_start_time_seconds,
    )

    assert boundary.can_start_immediately
    assert boundary.delay_seconds == 0.0
    assert boundary.earliest_start_time_seconds == waiting.earliest_start_time_seconds


def test_request_after_boundary_is_immediate() -> None:
    policy = RateLimitPolicy(max_requests_per_second=2)
    state = RateLimitState(last_request_start_time_seconds=10)

    decision = policy.evaluate(state=state, current_time_seconds=11)

    assert decision.can_start_immediately
    assert decision.delay_seconds == 0.0
    assert decision.earliest_start_time_seconds == 10.5


def test_evaluation_alone_never_changes_recorded_start() -> None:
    policy = RateLimitPolicy(max_requests_per_second=1)
    state = RateLimitState(last_request_start_time_seconds=10)

    first = policy.evaluate(state=state, current_time_seconds=10.25)
    second = policy.evaluate(state=state, current_time_seconds=10.25)

    assert first == second
    assert state.last_request_start_time_seconds == 10.0


def test_start_can_be_recorded_at_exact_earliest_time() -> None:
    policy = RateLimitPolicy(max_requests_per_second=2)
    original = RateLimitState(last_request_start_time_seconds=10)
    decision = policy.evaluate(state=original, current_time_seconds=10)

    recorded = policy.record_start(
        state=original,
        start_time_seconds=decision.earliest_start_time_seconds,
    )

    assert recorded.last_request_start_time_seconds == 10.5
    assert original.last_request_start_time_seconds == 10.0


def test_start_can_be_recorded_after_earliest_time() -> None:
    policy = RateLimitPolicy(max_requests_per_second=2)
    original = RateLimitState(last_request_start_time_seconds=10)

    recorded = policy.record_start(state=original, start_time_seconds=11)

    assert recorded.last_request_start_time_seconds == 11.0


def test_multiple_sequential_starts_return_distinct_immutable_states() -> None:
    policy = RateLimitPolicy(max_requests_per_second=5)
    initial = RateLimitState()
    first = policy.record_start(state=initial, start_time_seconds=10)
    second = policy.record_start(state=first, start_time_seconds=10.2)
    third = policy.record_start(state=second, start_time_seconds=10.4)

    assert initial.last_request_start_time_seconds is None
    assert first.last_request_start_time_seconds == 10.0
    assert second.last_request_start_time_seconds == 10.2
    assert third.last_request_start_time_seconds == 10.4


def test_start_before_permitted_time_is_rejected() -> None:
    policy = RateLimitPolicy(max_requests_per_second=5)
    state = RateLimitState(last_request_start_time_seconds=10)

    with pytest.raises(ValueError, match="permitted request start"):
        policy.record_start(state=state, start_time_seconds=10.1)


def test_rerecording_same_start_is_rejected() -> None:
    policy = RateLimitPolicy(max_requests_per_second=5)
    state = RateLimitState(last_request_start_time_seconds=10)

    with pytest.raises(ValueError, match="permitted request start"):
        policy.record_start(state=state, start_time_seconds=10)


def test_evaluation_clock_regression_is_rejected_before_delay_calculation() -> None:
    policy = RateLimitPolicy(max_requests_per_second=5)
    state = RateLimitState(last_request_start_time_seconds=10)

    with pytest.raises(ValueError, match="current_time_seconds"):
        policy.evaluate(state=state, current_time_seconds=9.999)


def test_recording_clock_regression_is_rejected() -> None:
    policy = RateLimitPolicy(max_requests_per_second=5)
    state = RateLimitState(last_request_start_time_seconds=10)

    with pytest.raises(ValueError, match="start_time_seconds"):
        policy.record_start(state=state, start_time_seconds=9.999)


@pytest.mark.parametrize(
    "current_time",
    [True, -1, float("nan"), float("inf"), float("-inf"), "10"],
)
def test_invalid_evaluation_times_are_rejected(current_time: object) -> None:
    with pytest.raises(ValueError, match="monotonic timestamp"):
        RateLimitPolicy(max_requests_per_second=5).evaluate(
            state=RateLimitState(),
            current_time_seconds=current_time,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "start_time",
    [True, -1, float("nan"), float("inf"), float("-inf"), "10"],
)
def test_invalid_recording_times_are_rejected(start_time: object) -> None:
    with pytest.raises(ValueError, match="monotonic timestamp"):
        RateLimitPolicy(max_requests_per_second=5).record_start(
            state=RateLimitState(),
            start_time_seconds=start_time,  # type: ignore[arg-type]
        )


def test_invalid_state_object_is_rejected_by_both_operations() -> None:
    policy = RateLimitPolicy(max_requests_per_second=5)

    with pytest.raises(ValueError, match="state"):
        policy.evaluate(state=None, current_time_seconds=10)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="state"):
        policy.record_start(state=None, start_time_seconds=10)  # type: ignore[arg-type]


def test_large_finite_timestamp_with_representable_interval_is_supported() -> None:
    policy = RateLimitPolicy(max_requests_per_second=1e-292)
    state = RateLimitState(last_request_start_time_seconds=1e300)

    decision = policy.evaluate(state=state, current_time_seconds=1e300)

    assert not decision.can_start_immediately
    assert math_is_finite_positive(decision.delay_seconds)
    assert decision.earliest_start_time_seconds > 1e300


def test_timestamp_plus_interval_overflow_is_rejected() -> None:
    policy = RateLimitPolicy(max_requests_per_second=1e-308)
    state = RateLimitState(last_request_start_time_seconds=1e308)

    with pytest.raises(ValueError, match="remain finite"):
        policy.evaluate(state=state, current_time_seconds=1e308)
    with pytest.raises(ValueError, match="remain finite"):
        policy.record_start(state=state, start_time_seconds=float_info.max)


def test_unrepresentable_timestamp_advancement_is_rejected() -> None:
    policy = RateLimitPolicy(max_requests_per_second=5)
    state = RateLimitState(last_request_start_time_seconds=1e20)

    with pytest.raises(ValueError, match="advance monotonically"):
        policy.evaluate(state=state, current_time_seconds=1e20)


def test_derived_delay_is_finite_and_never_negative() -> None:
    policy = RateLimitPolicy(max_requests_per_second=10)
    state = RateLimitState(last_request_start_time_seconds=0)

    waiting = policy.evaluate(state=state, current_time_seconds=0.025)
    boundary = policy.evaluate(
        state=state,
        current_time_seconds=waiting.earliest_start_time_seconds,
    )

    assert math_is_finite_positive(waiting.delay_seconds)
    assert boundary.delay_seconds == 0.0


def test_decision_validation_and_immutability() -> None:
    immediate = RateLimitDecision(True, 0, 10)
    waiting = RateLimitDecision(False, 0.5, 10.5)

    assert immediate.delay_seconds == 0.0
    assert waiting.delay_seconds == 0.5
    with pytest.raises(FrozenInstanceError):
        waiting.delay_seconds = 1.0  # type: ignore[misc]
    with pytest.raises(ValueError, match="can_start_immediately"):
        RateLimitDecision(1, 0, 10)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="immediate"):
        RateLimitDecision(True, 0.1, 10)
    with pytest.raises(ValueError, match="waiting"):
        RateLimitDecision(False, 0, 10)


@pytest.mark.parametrize(
    ("field_name", "values"),
    [
        ("delay_seconds", [-1, True, "1", float("nan"), float("inf")]),
        (
            "earliest_start_time_seconds",
            [-1, True, "1", float("nan"), float("inf")],
        ),
    ],
)
def test_invalid_decision_numeric_metadata_is_rejected(
    field_name: str,
    values: list[object],
) -> None:
    for value in values:
        arguments: dict[str, object] = {
            "can_start_immediately": True,
            "delay_seconds": 0,
            "earliest_start_time_seconds": 10,
        }
        arguments[field_name] = value
        with pytest.raises(ValueError, match=field_name):
            RateLimitDecision(**arguments)  # type: ignore[arg-type]


def test_public_models_contain_only_safe_numeric_pacing_metadata() -> None:
    policy = RateLimitPolicy(max_requests_per_second=5)
    state = RateLimitState(last_request_start_time_seconds=10)
    decision = policy.evaluate(state=state, current_time_seconds=10.2)

    assert {item.name for item in fields(policy)} == {
        "max_requests_per_second",
        "minimum_interval_seconds",
    }
    assert {item.name for item in fields(state)} == {"last_request_start_time_seconds"}
    assert {item.name for item in fields(decision)} == {
        "can_start_immediately",
        "delay_seconds",
        "earliest_start_time_seconds",
    }
    representations = f"{policy!r} {state!r} {decision!r}".casefold()
    for excluded_name in (
        "url",
        "query",
        "header",
        "body",
        "credential",
        "token",
        "user_agent",
        "contact_email",
    ):
        assert excluded_name not in representations


def test_rate_limit_contracts_are_intentionally_exported() -> None:
    expected = {
        "RateLimitDecision",
        "RateLimitPolicy",
        "RateLimitState",
    }

    assert expected <= set(providers.__all__)
    assert providers.RateLimitPolicy is RateLimitPolicy


def math_is_finite_positive(value: float) -> bool:
    return value > 0.0 and value < float("inf")
