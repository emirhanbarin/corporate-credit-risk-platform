"""Tests for deterministic SEC request construction."""

from urllib.parse import parse_qsl, urlsplit

from credit_risk_platform.config import AppSettings
from credit_risk_platform.providers.sec import SecRequest, SecRequestBuilder


def _settings(**overrides: str) -> AppSettings:
    values = {
        "SEC_USER_AGENT": "Corporate Credit Risk Platform/0.1",
        "SEC_CONTACT_EMAIL": "sec-operations@example.test",
    }
    values.update(overrides)
    return AppSettings.from_mapping(values)


def test_default_base_url_method_timeout_and_exact_headers() -> None:
    request = SecRequestBuilder(_settings()).build(SecRequest("/path", {}))

    assert request.url == "https://data.sec.gov/path"
    assert request.method == "GET"
    assert request.timeout_seconds == 30.0
    assert dict(request.headers) == {
        "User-Agent": (
            "Corporate Credit Risk Platform/0.1 sec-operations@example.test"
        ),
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate",
    }


def test_custom_base_url_path_and_configured_timeout_are_preserved() -> None:
    settings = _settings(
        SEC_BASE_URL="https://sec-api.example.test:8443/base/",
        SEC_REQUEST_TIMEOUT_SECONDS="12.5",
    )

    request = SecRequestBuilder(settings).build(SecRequest("/endpoint", {}))

    assert request.url == "https://sec-api.example.test:8443/base/endpoint"
    assert request.timeout_seconds == 12.5


def test_exact_standalone_contact_email_is_not_duplicated_case_insensitively() -> None:
    settings = _settings(
        SEC_USER_AGENT=(
            "Corporate Credit Risk Platform/0.1 (SEC-OPERATIONS@EXAMPLE.TEST)"
        )
    )

    request = SecRequestBuilder(settings).build(SecRequest("/path", {}))

    assert request.headers["User-Agent"] == settings.sec_user_agent


def test_email_like_substring_does_not_suppress_contact_email() -> None:
    settings = _settings(
        SEC_USER_AGENT=(
            "Corporate Credit Risk Platform/0.1 "
            "prefixsec-operations@example.test-suffix"
        )
    )

    request = SecRequestBuilder(settings).build(SecRequest("/path", {}))

    assert request.headers["User-Agent"].endswith(" sec-operations@example.test")


def test_empty_query_has_no_question_mark() -> None:
    request = SecRequestBuilder(_settings()).build(SecRequest("/path", {}))

    assert "?" not in request.url


def test_query_is_sorted_and_percent_encoded_deterministically() -> None:
    sec_request = SecRequest(
        "/path",
        {"z key": "space value", "a&key": "a&b=c", "middle": "/"},
    )
    builder = SecRequestBuilder(_settings())

    first = builder.build(sec_request)
    second = builder.build(sec_request)

    assert first == second
    assert first.url.endswith("?a%26key=a%26b%3Dc&middle=%2F&z+key=space+value")
    assert parse_qsl(urlsplit(first.url).query) == [
        ("a&key", "a&b=c"),
        ("middle", "/"),
        ("z key", "space value"),
    ]


def test_builder_preserves_origin_and_produces_no_credentials_or_fragment() -> None:
    settings = _settings(
        SEC_BASE_URL="https://sec-api.example.test:9443/root",
    )
    request = SecRequestBuilder(settings).build(SecRequest("/resource", {}))
    parsed = urlsplit(request.url)

    assert parsed.scheme == "https"
    assert parsed.hostname == "sec-api.example.test"
    assert parsed.port == 9443
    assert parsed.username is None
    assert parsed.password is None
    assert parsed.fragment == ""


def test_source_settings_are_not_mutated_and_builder_has_no_transport() -> None:
    settings = _settings()
    expected = _settings()
    builder = SecRequestBuilder(settings)

    builder.build(SecRequest("/path", {}))

    assert settings == expected
    assert not hasattr(builder, "transport")
