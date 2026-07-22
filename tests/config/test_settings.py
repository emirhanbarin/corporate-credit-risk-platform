"""Tests for deterministic application configuration."""

from dataclasses import FrozenInstanceError, fields

import pytest

from credit_risk_platform.config import AppSettings, ConfigurationError

_REQUIRED_VALUES = {
    "SEC_USER_AGENT": "Corporate Credit Risk Platform/0.1",
    "SEC_CONTACT_EMAIL": "operations@example.test",
}
_ENVIRONMENT_VARIABLES = (
    "SEC_USER_AGENT",
    "SEC_CONTACT_EMAIL",
    "SEC_BASE_URL",
    "SEC_REQUEST_TIMEOUT_SECONDS",
    "SEC_MAX_REQUESTS_PER_SECOND",
)


def _values(**overrides: str) -> dict[str, str]:
    values = _REQUIRED_VALUES.copy()
    values.update(overrides)
    return values


def test_settings_fields_are_exactly_the_approved_initial_fields() -> None:
    assert [field.name for field in fields(AppSettings)] == [
        "sec_user_agent",
        "sec_contact_email",
        "sec_base_url",
        "sec_request_timeout_seconds",
        "sec_max_requests_per_second",
    ]


def test_from_mapping_uses_safe_optional_defaults() -> None:
    settings = AppSettings.from_mapping(_values())

    assert settings.sec_user_agent == "Corporate Credit Risk Platform/0.1"
    assert settings.sec_contact_email == "operations@example.test"
    assert settings.sec_base_url == "https://data.sec.gov"
    assert settings.sec_request_timeout_seconds == 30.0
    assert settings.sec_max_requests_per_second == 5.0


def test_from_mapping_trims_values_and_parses_overrides() -> None:
    settings = AppSettings.from_mapping(
        {
            "SEC_USER_AGENT": "  Corporate Credit Risk Platform/0.1  ",
            "SEC_CONTACT_EMAIL": "  operations@example.test  ",
            "SEC_BASE_URL": "  https://sec-compatible.example.test/api/  ",
            "SEC_REQUEST_TIMEOUT_SECONDS": " 45.5 ",
            "SEC_MAX_REQUESTS_PER_SECOND": " 7 ",
        }
    )

    assert settings.sec_user_agent == "Corporate Credit Risk Platform/0.1"
    assert settings.sec_contact_email == "operations@example.test"
    assert settings.sec_base_url == "https://sec-compatible.example.test/api"
    assert settings.sec_request_timeout_seconds == 45.5
    assert settings.sec_max_requests_per_second == 7.0


def test_base_url_trailing_slashes_are_removed() -> None:
    settings = AppSettings.from_mapping(_values(SEC_BASE_URL="https://data.sec.gov///"))

    assert settings.sec_base_url == "https://data.sec.gov"


def test_settings_are_immutable() -> None:
    settings = AppSettings.from_mapping(_values())

    with pytest.raises(FrozenInstanceError):
        settings.sec_base_url = "https://changed.example.test"


@pytest.mark.parametrize(
    ("user_agent", "contact_email", "field"),
    [
        ("", "operations@example.test", "SEC_USER_AGENT"),
        ("Corporate Credit Risk Platform/0.1", "", "SEC_CONTACT_EMAIL"),
    ],
)
def test_direct_construction_preserves_required_value_invariants(
    user_agent: str, contact_email: str, field: str
) -> None:
    with pytest.raises(ConfigurationError, match=field):
        AppSettings(
            sec_user_agent=user_agent,
            sec_contact_email=contact_email,
        )


def test_from_mapping_does_not_read_process_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SEC_USER_AGENT", "Environment Application/9.9")
    monkeypatch.setenv("SEC_CONTACT_EMAIL", "environment@example.test")

    with pytest.raises(ConfigurationError, match="SEC_USER_AGENT"):
        AppSettings.from_mapping({})

    settings = AppSettings.from_mapping(_values())
    assert settings.sec_user_agent == "Corporate Credit Risk Platform/0.1"
    assert settings.sec_contact_email == "operations@example.test"


def test_from_environment_reads_current_process_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for variable in _ENVIRONMENT_VARIABLES:
        monkeypatch.delenv(variable, raising=False)

    monkeypatch.setenv("SEC_USER_AGENT", "Environment Application/1.0")
    monkeypatch.setenv("SEC_CONTACT_EMAIL", "environment@example.test")
    monkeypatch.setenv("SEC_BASE_URL", "https://environment.example.test/")
    monkeypatch.setenv("SEC_REQUEST_TIMEOUT_SECONDS", "60")
    monkeypatch.setenv("SEC_MAX_REQUESTS_PER_SECOND", "4.5")

    settings = AppSettings.from_environment()

    assert settings == AppSettings(
        sec_user_agent="Environment Application/1.0",
        sec_contact_email="environment@example.test",
        sec_base_url="https://environment.example.test",
        sec_request_timeout_seconds=60.0,
        sec_max_requests_per_second=4.5,
    )


@pytest.mark.parametrize("field", ["SEC_USER_AGENT", "SEC_CONTACT_EMAIL"])
def test_missing_required_value_is_rejected(field: str) -> None:
    values = _values()
    del values[field]

    with pytest.raises(ConfigurationError, match=rf"^{field} is required\.$"):
        AppSettings.from_mapping(values)


@pytest.mark.parametrize("field", ["SEC_USER_AGENT", "SEC_CONTACT_EMAIL"])
def test_blank_required_value_is_rejected(field: str) -> None:
    with pytest.raises(ConfigurationError, match=rf"^{field} is required\.$"):
        AppSettings.from_mapping(_values(**{field: " \t "}))


@pytest.mark.parametrize(
    "placeholder",
    ["your-user-agent", "change-me", "example", "placeholder", "TODO"],
)
def test_placeholder_user_agent_is_rejected(placeholder: str) -> None:
    with pytest.raises(ConfigurationError, match="SEC_USER_AGENT"):
        AppSettings.from_mapping(_values(SEC_USER_AGENT=placeholder))


@pytest.mark.parametrize(
    "placeholder",
    [
        "your-email@example.test",
        "change-me@example.test",
        "example@example.test",
        "placeholder@example.test",
        "TODO@example.test",
    ],
)
def test_placeholder_contact_email_is_rejected(placeholder: str) -> None:
    with pytest.raises(ConfigurationError, match="SEC_CONTACT_EMAIL"):
        AppSettings.from_mapping(_values(SEC_CONTACT_EMAIL=placeholder))


@pytest.mark.parametrize(
    "invalid_user_agent",
    [
        "Corporate Platform\nInjected",
        "Corporate Platform\x00Injected",
        "A" * 257,
        "12345",
    ],
)
def test_invalid_user_agent_is_rejected(invalid_user_agent: str) -> None:
    with pytest.raises(ConfigurationError, match="SEC_USER_AGENT"):
        AppSettings.from_mapping(_values(SEC_USER_AGENT=invalid_user_agent))


@pytest.mark.parametrize(
    "invalid_email",
    [
        "operations.example.test",
        "@example.test",
        "operations@",
        "operations @example.test",
        "operations@exam ple.test",
        "operations\n@example.test",
        "operations\x00@example.test",
        f"{'a' * 245}@example.test",
        f"{'a' * 65}@example.test",
    ],
)
def test_invalid_contact_email_is_rejected(invalid_email: str) -> None:
    with pytest.raises(ConfigurationError, match="SEC_CONTACT_EMAIL"):
        AppSettings.from_mapping(_values(SEC_CONTACT_EMAIL=invalid_email))


@pytest.mark.parametrize(
    "invalid_url",
    [
        "http://data.sec.gov",
        "https:///companyfacts",
        "https://user@data.sec.gov",
        "https://data.sec.gov?source=test",
        "https://data.sec.gov#section",
        "https://data.sec.gov/\x00path",
        "https://data.sec.gov/invalid path",
        "https://data.sec.gov:not-a-port",
        "https://data.sec.gov:0",
    ],
)
def test_invalid_base_url_is_rejected(invalid_url: str) -> None:
    with pytest.raises(ConfigurationError, match="SEC_BASE_URL"):
        AppSettings.from_mapping(_values(SEC_BASE_URL=invalid_url))


def test_blank_optional_url_uses_default() -> None:
    settings = AppSettings.from_mapping(_values(SEC_BASE_URL=" \t "))

    assert settings.sec_base_url == "https://data.sec.gov"


@pytest.mark.parametrize(
    ("timeout", "expected"),
    [("15", 15.0), ("15.75", 15.75)],
)
def test_valid_timeout_strings_are_parsed(timeout: str, expected: float) -> None:
    settings = AppSettings.from_mapping(_values(SEC_REQUEST_TIMEOUT_SECONDS=timeout))

    assert settings.sec_request_timeout_seconds == expected


@pytest.mark.parametrize(
    "invalid_timeout",
    ["not-a-number", "0", "-1", "nan", "inf", "-inf", "300.1"],
)
def test_invalid_timeout_is_rejected(invalid_timeout: str) -> None:
    with pytest.raises(ConfigurationError, match="SEC_REQUEST_TIMEOUT_SECONDS"):
        AppSettings.from_mapping(_values(SEC_REQUEST_TIMEOUT_SECONDS=invalid_timeout))


@pytest.mark.parametrize(
    ("rate_limit", "expected"),
    [("4", 4.0), ("4.25", 4.25), ("10", 10.0)],
)
def test_valid_rate_limit_strings_are_parsed(rate_limit: str, expected: float) -> None:
    settings = AppSettings.from_mapping(_values(SEC_MAX_REQUESTS_PER_SECOND=rate_limit))

    assert settings.sec_max_requests_per_second == expected


@pytest.mark.parametrize(
    "invalid_rate_limit",
    ["not-a-number", "0", "-1", "nan", "inf", "-inf", "10.1"],
)
def test_invalid_rate_limit_is_rejected(invalid_rate_limit: str) -> None:
    with pytest.raises(ConfigurationError, match="SEC_MAX_REQUESTS_PER_SECOND"):
        AppSettings.from_mapping(
            _values(SEC_MAX_REQUESTS_PER_SECOND=invalid_rate_limit)
        )


def test_blank_numeric_values_use_defaults() -> None:
    settings = AppSettings.from_mapping(
        _values(
            SEC_REQUEST_TIMEOUT_SECONDS=" ",
            SEC_MAX_REQUESTS_PER_SECOND="\t",
        )
    )

    assert settings.sec_request_timeout_seconds == 30.0
    assert settings.sec_max_requests_per_second == 5.0


def test_configuration_errors_do_not_expose_values_or_mapping() -> None:
    invalid_contact = "private-contact-value"
    unrelated_value = "unrelated-context"
    values = _values(SEC_CONTACT_EMAIL=invalid_contact)
    values["UNRELATED_SETTING"] = unrelated_value

    with pytest.raises(ConfigurationError) as exception_info:
        AppSettings.from_mapping(values)

    message = str(exception_info.value)
    assert "SEC_CONTACT_EMAIL" in message
    assert invalid_contact not in message
    assert unrelated_value not in message
    assert repr(values) not in message
    assert isinstance(exception_info.value, ValueError)
