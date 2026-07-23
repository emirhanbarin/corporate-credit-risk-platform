"""Tests for pure, transport-independent retry policy decisions."""

from dataclasses import FrozenInstanceError, fields

import pytest

import credit_risk_platform.providers as providers
from credit_risk_platform.providers import (
    RetryDecision,
    RetryDecisionReason,
    RetryOutcome,
    RetryPolicy,
)


def _decide(
    policy: RetryPolicy,
    *,
    attempt_number: int = 1,
    outcome: RetryOutcome = RetryOutcome.RETRYABLE_TRANSPORT_FAILURE,
    jitter_sample: float = 0.5,
    http_status_code: int | None = None,
    retry_after_seconds: float | None = None,
) -> RetryDecision:
    return policy.decide(
        attempt_number=attempt_number,
        outcome=outcome,
        jitter_sample=jitter_sample,
        http_status_code=http_status_code,
        retry_after_seconds=retry_after_seconds,
    )


def test_default_policy_has_conservative_immutable_configuration() -> None:
    policy = RetryPolicy()

    assert policy.max_attempts == 3
    assert policy.initial_delay_seconds == 1.0
    assert policy.max_delay_seconds == 60.0
    assert policy.jitter_proportion == 0.2
    assert policy.retryable_status_codes == frozenset({408, 429, 500, 502, 503, 504})


def test_custom_policy_is_normalized_and_frozen() -> None:
    policy = RetryPolicy(
        max_attempts=5,
        initial_delay_seconds=2,
        max_delay_seconds=20,
        jitter_proportion=0,
        retryable_status_codes=(),
    )

    assert policy.initial_delay_seconds == 2.0
    assert policy.max_delay_seconds == 20.0
    assert policy.jitter_proportion == 0.0
    assert policy.retryable_status_codes == frozenset()
    with pytest.raises(FrozenInstanceError):
        policy.max_attempts = 6  # type: ignore[misc]


def test_retryable_status_codes_are_defensively_copied_and_immutable() -> None:
    source = {429, 503}
    policy = RetryPolicy(retryable_status_codes=source)

    source.add(500)

    assert policy.retryable_status_codes == frozenset({429, 503})
    with pytest.raises(AttributeError):
        policy.retryable_status_codes.add(500)  # type: ignore[attr-defined]


@pytest.mark.parametrize("max_attempts", [0, -1, True, 1.5, "3"])
def test_invalid_max_attempts_are_rejected(max_attempts: object) -> None:
    with pytest.raises(ValueError, match="max_attempts"):
        RetryPolicy(max_attempts=max_attempts)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("initial_delay_seconds", 0),
        ("initial_delay_seconds", -1),
        ("initial_delay_seconds", True),
        ("initial_delay_seconds", "1"),
        ("initial_delay_seconds", float("nan")),
        ("initial_delay_seconds", float("inf")),
        ("max_delay_seconds", 0),
        ("max_delay_seconds", -1),
        ("max_delay_seconds", True),
        ("max_delay_seconds", "60"),
        ("max_delay_seconds", float("nan")),
        ("max_delay_seconds", float("inf")),
    ],
)
def test_invalid_policy_delays_are_rejected(field: str, value: object) -> None:
    with pytest.raises(ValueError, match=field):
        RetryPolicy(**{field: value})  # type: ignore[arg-type]


def test_integer_delay_too_large_for_finite_float_is_rejected() -> None:
    with pytest.raises(ValueError, match="initial_delay_seconds"):
        RetryPolicy(initial_delay_seconds=10**10000)


def test_maximum_delay_cannot_be_less_than_initial_delay() -> None:
    with pytest.raises(ValueError, match="max_delay_seconds"):
        RetryPolicy(initial_delay_seconds=2, max_delay_seconds=1)


@pytest.mark.parametrize(
    "jitter_proportion",
    [-0.1, 1.0, True, "0.2", float("nan"), float("inf")],
)
def test_invalid_jitter_proportions_are_rejected(
    jitter_proportion: object,
) -> None:
    with pytest.raises(ValueError, match="jitter_proportion"):
        RetryPolicy(jitter_proportion=jitter_proportion)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "retryable_status_codes",
    [
        None,
        [99],
        [600],
        [True],
        [500.0],
        ["500"],
    ],
)
def test_invalid_retryable_status_collections_are_rejected(
    retryable_status_codes: object,
) -> None:
    with pytest.raises(ValueError, match="retryable_status_codes"):
        RetryPolicy(
            retryable_status_codes=retryable_status_codes  # type: ignore[arg-type]
        )


@pytest.mark.parametrize("attempt_number", [0, -1, True, 1.5, "1"])
def test_invalid_attempt_numbers_are_rejected(attempt_number: object) -> None:
    with pytest.raises(ValueError, match="attempt_number"):
        _decide(RetryPolicy(), attempt_number=attempt_number)  # type: ignore[arg-type]


def test_attempts_are_one_based_and_below_maximum_can_retry() -> None:
    decision = _decide(
        RetryPolicy(max_attempts=3, jitter_proportion=0),
        attempt_number=1,
    )

    assert decision == RetryDecision(
        reason=RetryDecisionReason.RETRY_ALLOWED,
        delay_seconds=1.0,
    )
    assert decision.should_retry


@pytest.mark.parametrize("attempt_number", [3, 4])
def test_attempt_at_or_above_maximum_is_exhausted(attempt_number: int) -> None:
    decision = _decide(RetryPolicy(max_attempts=3), attempt_number=attempt_number)

    assert decision.reason is RetryDecisionReason.ATTEMPTS_EXHAUSTED
    assert decision.delay_seconds is None
    assert not decision.should_retry


def test_single_total_attempt_never_allows_a_retry() -> None:
    decision = _decide(RetryPolicy(max_attempts=1))

    assert decision.reason is RetryDecisionReason.ATTEMPTS_EXHAUSTED


@pytest.mark.parametrize(
    ("outcome", "expected_reason"),
    [
        (
            RetryOutcome.RETRYABLE_TRANSPORT_FAILURE,
            RetryDecisionReason.RETRY_ALLOWED,
        ),
        (
            RetryOutcome.NON_RETRYABLE_TRANSPORT_FAILURE,
            RetryDecisionReason.OUTCOME_NOT_RETRYABLE,
        ),
    ],
)
def test_transport_outcomes_are_classified_by_the_caller(
    outcome: RetryOutcome,
    expected_reason: RetryDecisionReason,
) -> None:
    decision = _decide(RetryPolicy(), outcome=outcome)

    assert decision.reason is expected_reason


@pytest.mark.parametrize(
    ("status_code", "expected_reason"),
    [
        (408, RetryDecisionReason.RETRY_ALLOWED),
        (429, RetryDecisionReason.RETRY_ALLOWED),
        (500, RetryDecisionReason.RETRY_ALLOWED),
        (502, RetryDecisionReason.RETRY_ALLOWED),
        (503, RetryDecisionReason.RETRY_ALLOWED),
        (504, RetryDecisionReason.RETRY_ALLOWED),
        (403, RetryDecisionReason.OUTCOME_NOT_RETRYABLE),
        (404, RetryDecisionReason.OUTCOME_NOT_RETRYABLE),
    ],
)
def test_http_status_retryability_uses_the_policy_set(
    status_code: int,
    expected_reason: RetryDecisionReason,
) -> None:
    decision = _decide(
        RetryPolicy(),
        outcome=RetryOutcome.HTTP_RESPONSE,
        http_status_code=status_code,
    )

    assert decision.reason is expected_reason


def test_custom_and_empty_status_sets_control_http_classification() -> None:
    custom = _decide(
        RetryPolicy(retryable_status_codes={418}),
        outcome=RetryOutcome.HTTP_RESPONSE,
        http_status_code=418,
    )
    empty = _decide(
        RetryPolicy(retryable_status_codes=()),
        outcome=RetryOutcome.HTTP_RESPONSE,
        http_status_code=503,
    )

    assert custom.should_retry
    assert empty.reason is RetryDecisionReason.OUTCOME_NOT_RETRYABLE


def test_non_retryable_reason_precedes_attempt_exhaustion() -> None:
    decision = _decide(
        RetryPolicy(max_attempts=1),
        outcome=RetryOutcome.NON_RETRYABLE_TRANSPORT_FAILURE,
    )

    assert decision.reason is RetryDecisionReason.OUTCOME_NOT_RETRYABLE


def test_retryable_http_status_at_attempt_limit_is_exhausted() -> None:
    decision = _decide(
        RetryPolicy(max_attempts=2),
        attempt_number=2,
        outcome=RetryOutcome.HTTP_RESPONSE,
        http_status_code=503,
    )

    assert decision.reason is RetryDecisionReason.ATTEMPTS_EXHAUSTED


def test_exponential_backoff_progression_and_cap() -> None:
    policy = RetryPolicy(
        max_attempts=10,
        initial_delay_seconds=1,
        max_delay_seconds=4,
        jitter_proportion=0,
    )

    delays = [
        _decide(policy, attempt_number=attempt).delay_seconds
        for attempt in (1, 2, 3, 4)
    ]

    assert delays == [1.0, 2.0, 4.0, 4.0]


def test_non_power_of_two_maximum_caps_the_nominal_delay() -> None:
    policy = RetryPolicy(
        max_attempts=5,
        initial_delay_seconds=2,
        max_delay_seconds=5,
        jitter_proportion=0,
    )

    assert _decide(policy, attempt_number=2).delay_seconds == 4.0
    assert _decide(policy, attempt_number=3).delay_seconds == 5.0


def test_very_large_attempt_number_is_capped_without_overflow() -> None:
    huge_attempt = 10**10000
    policy = RetryPolicy(
        max_attempts=huge_attempt + 1,
        initial_delay_seconds=0.001,
        max_delay_seconds=10,
        jitter_proportion=0,
    )

    decision = _decide(policy, attempt_number=huge_attempt)

    assert decision.delay_seconds == 10.0


@pytest.mark.parametrize(
    ("sample", "expected_delay"),
    [(0.0, 1.6), (0.5, 2.0), (1.0, 2.4)],
)
def test_symmetric_jitter_boundaries_are_deterministic(
    sample: float,
    expected_delay: float,
) -> None:
    policy = RetryPolicy(
        initial_delay_seconds=2,
        jitter_proportion=0.2,
    )

    first = _decide(policy, jitter_sample=sample)
    second = _decide(policy, jitter_sample=sample)

    assert first.delay_seconds == pytest.approx(expected_delay)
    assert second == first


def test_zero_jitter_returns_nominal_delay_for_every_valid_sample() -> None:
    policy = RetryPolicy(initial_delay_seconds=2, jitter_proportion=0)

    assert {
        _decide(policy, jitter_sample=sample).delay_seconds
        for sample in (0.0, 0.5, 1.0)
    } == {2.0}


def test_jittered_delay_remains_capped() -> None:
    policy = RetryPolicy(
        initial_delay_seconds=4,
        max_delay_seconds=5,
        jitter_proportion=0.5,
    )

    decision = _decide(policy, jitter_sample=1.0)

    assert decision.delay_seconds == 5.0


@pytest.mark.parametrize(
    "jitter_sample",
    [-0.1, 1.1, True, "0.5", float("nan"), float("inf")],
)
def test_invalid_jitter_samples_are_rejected(jitter_sample: object) -> None:
    with pytest.raises(ValueError, match="jitter_sample"):
        _decide(RetryPolicy(), jitter_sample=jitter_sample)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("retry_after_seconds", "expected_delay"),
    [
        (None, 2.0),
        (1.0, 2.0),
        (2.0, 2.0),
        (3.0, 3.0),
        (100.0, 5.0),
        (0.0, 2.0),
    ],
)
def test_retry_after_is_a_capped_minimum_delay(
    retry_after_seconds: float | None,
    expected_delay: float,
) -> None:
    policy = RetryPolicy(
        initial_delay_seconds=2,
        max_delay_seconds=5,
        jitter_proportion=0,
    )

    decision = _decide(policy, retry_after_seconds=retry_after_seconds)

    assert decision.delay_seconds == expected_delay


@pytest.mark.parametrize(
    "retry_after_seconds",
    [-0.1, True, "1", float("nan"), float("inf")],
)
def test_invalid_retry_after_values_are_rejected(
    retry_after_seconds: object,
) -> None:
    with pytest.raises(ValueError, match="retry_after_seconds"):
        _decide(
            RetryPolicy(),
            retry_after_seconds=retry_after_seconds,  # type: ignore[arg-type]
        )


def test_retry_after_does_not_make_non_retryable_outcome_retryable() -> None:
    decision = _decide(
        RetryPolicy(),
        outcome=RetryOutcome.NON_RETRYABLE_TRANSPORT_FAILURE,
        retry_after_seconds=30,
    )

    assert decision.reason is RetryDecisionReason.OUTCOME_NOT_RETRYABLE
    assert decision.delay_seconds is None


def test_retry_after_does_not_bypass_exhausted_attempts() -> None:
    decision = _decide(
        RetryPolicy(max_attempts=1),
        retry_after_seconds=30,
    )

    assert decision.reason is RetryDecisionReason.ATTEMPTS_EXHAUSTED
    assert decision.delay_seconds is None


@pytest.mark.parametrize("status_code", [None, 99, 600, True, 500.0, "500"])
def test_http_outcome_requires_a_valid_status_code(status_code: object) -> None:
    with pytest.raises(ValueError, match="http_status_code"):
        _decide(
            RetryPolicy(),
            outcome=RetryOutcome.HTTP_RESPONSE,
            http_status_code=status_code,  # type: ignore[arg-type]
        )


def test_transport_outcome_rejects_http_status_code() -> None:
    with pytest.raises(ValueError, match="http_status_code"):
        _decide(RetryPolicy(), http_status_code=503)


def test_invalid_outcome_is_rejected() -> None:
    with pytest.raises(ValueError, match="outcome"):
        _decide(RetryPolicy(), outcome="retryable")  # type: ignore[arg-type]


def test_decision_invariants_and_immutability() -> None:
    allowed = RetryDecision(RetryDecisionReason.RETRY_ALLOWED, 0)
    denied = RetryDecision(RetryDecisionReason.OUTCOME_NOT_RETRYABLE, None)

    assert allowed.delay_seconds == 0.0
    assert allowed.should_retry
    assert not denied.should_retry
    with pytest.raises(FrozenInstanceError):
        allowed.delay_seconds = 1.0  # type: ignore[misc]
    with pytest.raises(ValueError, match="delay_seconds"):
        RetryDecision(RetryDecisionReason.RETRY_ALLOWED, None)
    with pytest.raises(ValueError, match="delay_seconds"):
        RetryDecision(RetryDecisionReason.RETRY_ALLOWED, -1)
    with pytest.raises(ValueError, match="delay_seconds"):
        RetryDecision(RetryDecisionReason.ATTEMPTS_EXHAUSTED, 1)
    with pytest.raises(ValueError, match="reason"):
        RetryDecision("retry_allowed", 1)  # type: ignore[arg-type]


def test_policy_and_decision_representations_contain_only_operational_data() -> None:
    policy = RetryPolicy()
    decision = _decide(policy)

    assert {field.name for field in fields(policy)} == {
        "max_attempts",
        "initial_delay_seconds",
        "max_delay_seconds",
        "jitter_proportion",
        "retryable_status_codes",
    }
    assert {field.name for field in fields(decision)} == {
        "reason",
        "delay_seconds",
    }
    representations = f"{policy!r} {policy!s} {decision!r} {decision!s}".casefold()
    for excluded_name in (
        "url",
        "query",
        "header",
        "body",
        "credential",
        "user_agent",
        "contact_email",
    ):
        assert excluded_name not in representations


def test_retry_contracts_are_intentionally_exported() -> None:
    expected = {
        "RetryDecision",
        "RetryDecisionReason",
        "RetryOutcome",
        "RetryPolicy",
    }

    assert expected <= set(providers.__all__)
    assert providers.RetryPolicy is RetryPolicy
