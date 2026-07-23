"""Tests for deterministic, authority-isolated SEC request construction."""

from dataclasses import FrozenInstanceError
from urllib.parse import parse_qsl, urlsplit

import pytest

from credit_risk_platform.config import AppSettings
from credit_risk_platform.providers.sec import SecRequest, SecRequestBuilder


def _settings(**overrides: str) -> AppSettings:
    values = {
        "SEC_USER_AGENT": "Corporate Credit Risk Platform/0.1",
        "SEC_CONTACT_EMAIL": "sec-operations@example.test",
    }
    values.update(overrides)
    return AppSettings.from_mapping(values)


def _data_builder(settings: AppSettings | None = None) -> SecRequestBuilder:
    retained_settings = _settings() if settings is None else settings
    return SecRequestBuilder(
        retained_settings,
        base_url=retained_settings.sec_data_base_url,
    )


def _files_builder(settings: AppSettings | None = None) -> SecRequestBuilder:
    retained_settings = _settings() if settings is None else settings
    return SecRequestBuilder(
        retained_settings,
        base_url=retained_settings.sec_files_base_url,
    )


def test_data_authority_method_timeout_and_exact_headers() -> None:
    request = _data_builder().build(
        SecRequest("/api/xbrl/companyfacts/CIK0000789019.json", {})
    )

    assert (
        request.url == "https://data.sec.gov/api/xbrl/companyfacts/CIK0000789019.json"
    )
    assert request.method == "GET"
    assert request.timeout_seconds == 30.0
    assert dict(request.headers) == {
        "User-Agent": (
            "Corporate Credit Risk Platform/0.1 sec-operations@example.test"
        ),
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate",
    }


def test_files_authority_builds_exact_ticker_file_url_without_query() -> None:
    request_input = SecRequest("/files/company_tickers.json", {})
    request = _files_builder().build(request_input)

    assert request.url == "https://www.sec.gov/files/company_tickers.json"
    assert request.method == "GET"
    assert request.timeout_seconds == 30.0
    assert dict(request.headers) == {
        "User-Agent": (
            "Corporate Credit Risk Platform/0.1 sec-operations@example.test"
        ),
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate",
    }
    assert "?" not in request.url
    assert request_input == SecRequest("/files/company_tickers.json", {})


def test_custom_authority_and_configured_timeout_are_preserved() -> None:
    settings = _settings(
        SEC_DATA_BASE_URL="https://data-source.example.test:8443/",
        SEC_REQUEST_TIMEOUT_SECONDS="12.5",
    )

    request = _data_builder(settings).build(SecRequest("/endpoint", {}))

    assert request.url == "https://data-source.example.test:8443/endpoint"
    assert request.timeout_seconds == 12.5


def test_builder_selects_and_normalizes_authority_once_at_construction() -> None:
    settings = _settings()
    builder = SecRequestBuilder(
        settings,
        base_url="https://selected.example.test/",
    )

    assert builder._base_url == "https://selected.example.test"
    assert builder.settings is settings
    assert "selected.example.test" not in repr(builder)
    with pytest.raises(FrozenInstanceError):
        builder._base_url = "https://changed.example.test"  # type: ignore[misc]


@pytest.mark.parametrize(
    "invalid_authority",
    [
        None,
        42,
        True,
        "",
        " \t ",
        "http://sec.example.test",
        "https:///missing-host",
        "https://user@sec.example.test",
        "https://user:password@sec.example.test",
        "https://sec.example.test?query=value",
        "https://sec.example.test?",
        "https://sec.example.test#fragment",
        "https://sec.example.test#",
        "https://sec.example.test\\path",
        "https://sec.example.test/\r\npath",
        "https://sec.example.test/\x00path",
        "https://sec.example.test/path",
        "https://sec.example.test///",
        "https://sec.example.test:not-a-port",
        "https://sec.example.test:0",
    ],
)
def test_invalid_explicit_authority_is_rejected_safely(
    invalid_authority: object,
) -> None:
    with pytest.raises(
        ValueError,
        match=r"^base_url must be a valid root HTTPS authority\.$",
    ) as exception_info:
        SecRequestBuilder(
            _settings(),
            base_url=invalid_authority,  # type: ignore[arg-type]
        )

    assert "password" not in str(exception_info.value)
    assert "query=value" not in str(exception_info.value)


def test_builder_rejects_non_settings_without_using_it() -> None:
    with pytest.raises(ValueError, match="settings must be an AppSettings"):
        SecRequestBuilder(  # type: ignore[arg-type]
            object(),
            base_url="https://sec.example.test",
        )


def test_builder_requires_explicit_authority() -> None:
    with pytest.raises(TypeError):
        SecRequestBuilder(_settings())  # type: ignore[call-arg]


def test_exact_standalone_contact_email_is_not_duplicated_case_insensitively() -> None:
    settings = _settings(
        SEC_USER_AGENT=(
            "Corporate Credit Risk Platform/0.1 (SEC-OPERATIONS@EXAMPLE.TEST)"
        )
    )

    request = _data_builder(settings).build(SecRequest("/path", {}))

    assert request.headers["User-Agent"] == settings.sec_user_agent


def test_email_like_substring_does_not_suppress_contact_email() -> None:
    settings = _settings(
        SEC_USER_AGENT=(
            "Corporate Credit Risk Platform/0.1 "
            "prefixsec-operations@example.test-suffix"
        )
    )

    request = _data_builder(settings).build(SecRequest("/path", {}))

    assert request.headers["User-Agent"].endswith(" sec-operations@example.test")


def test_empty_query_has_no_question_mark() -> None:
    request = _data_builder().build(SecRequest("/path", {}))

    assert "?" not in request.url


def test_query_is_sorted_and_percent_encoded_deterministically() -> None:
    sec_request = SecRequest(
        "/path",
        {"z key": "space value", "a&key": "a&b=c", "middle": "/"},
    )
    builder = _data_builder()

    first = builder.build(sec_request)
    second = builder.build(sec_request)

    assert first == second
    assert first.url.endswith("?a%26key=a%26b%3Dc&middle=%2F&z+key=space+value")
    assert parse_qsl(urlsplit(first.url).query) == [
        ("a&key", "a&b=c"),
        ("middle", "/"),
        ("z key", "space value"),
    ]


def test_builder_preserves_origin_and_has_no_credentials_or_fragment() -> None:
    settings = _settings(
        SEC_FILES_BASE_URL="https://files-source.example.test:9443/",
    )
    request = _files_builder(settings).build(SecRequest("/resource", {}))
    parsed = urlsplit(request.url)

    assert parsed.scheme == "https"
    assert parsed.hostname == "files-source.example.test"
    assert parsed.port == 9443
    assert parsed.username is None
    assert parsed.password is None
    assert parsed.fragment == ""


def test_path_text_and_query_cannot_switch_data_builder_authority() -> None:
    builder = _data_builder()
    request = builder.build(
        SecRequest(
            "/https://www.sec.gov/files/company_tickers.json",
            {"host": "www.sec.gov", "url": "https://www.sec.gov"},
        )
    )
    parsed = urlsplit(request.url)

    assert parsed.hostname == "data.sec.gov"
    assert parsed.path == "/https://www.sec.gov/files/company_tickers.json"
    assert parse_qsl(parsed.query) == [
        ("host", "www.sec.gov"),
        ("url", "https://www.sec.gov"),
    ]


def test_path_text_cannot_switch_files_builder_authority() -> None:
    request = _files_builder().build(
        SecRequest("/https://data.sec.gov/api/xbrl/companyfacts.json", {})
    )

    assert urlsplit(request.url).hostname == "www.sec.gov"
    assert request.url == (
        "https://www.sec.gov/https://data.sec.gov/api/xbrl/companyfacts.json"
    )


@pytest.mark.parametrize(
    "invalid_path",
    [
        "https://www.sec.gov/files/company_tickers.json",
        "//www.sec.gov/files/company_tickers.json",
        "/%2f%2fwww.sec.gov/path",
        "/%252f%252fwww.sec.gov/path",
    ],
)
def test_existing_request_validation_blocks_authority_override_paths(
    invalid_path: str,
) -> None:
    with pytest.raises(ValueError, match="path"):
        SecRequest(invalid_path, {})


def test_two_builders_from_same_settings_remain_independent() -> None:
    settings = _settings(
        SEC_DATA_BASE_URL="https://data-source.example.test",
        SEC_FILES_BASE_URL="https://files-source.example.test",
    )
    data_builder = _data_builder(settings)
    files_builder = _files_builder(settings)

    data_request = data_builder.build(SecRequest("/same-path", {}))
    files_request = files_builder.build(SecRequest("/same-path", {}))

    assert data_request.url == "https://data-source.example.test/same-path"
    assert files_request.url == "https://files-source.example.test/same-path"
    assert data_builder._base_url == settings.sec_data_base_url
    assert files_builder._base_url == settings.sec_files_base_url


def test_inputs_are_not_mutated_and_builder_has_no_transport() -> None:
    settings = _settings()
    expected_settings = _settings()
    source_query = {"key": "value"}
    sec_request = SecRequest("/path", source_query)
    builder = _data_builder(settings)

    builder.build(sec_request)
    source_query["key"] = "changed"

    assert settings == expected_settings
    assert sec_request.query == {"key": "value"}
    assert not hasattr(builder, "transport")
