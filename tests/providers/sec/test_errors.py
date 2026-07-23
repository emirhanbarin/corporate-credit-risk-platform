"""Tests for safe SEC provider exceptions."""

import pytest

from credit_risk_platform.providers.sec import (
    SecNotFoundError,
    SecProviderError,
    SecRateLimitError,
    SecRequestError,
    SecResponseError,
    SecServerError,
    SecTimeoutError,
    SecTransportError,
)


def test_exception_hierarchy() -> None:
    assert issubclass(SecRequestError, SecProviderError)
    assert issubclass(SecTransportError, SecProviderError)
    assert issubclass(SecTimeoutError, SecTransportError)
    assert issubclass(SecResponseError, SecProviderError)
    assert issubclass(SecRateLimitError, SecResponseError)
    assert issubclass(SecNotFoundError, SecResponseError)
    assert issubclass(SecServerError, SecResponseError)


def test_safe_default_messages() -> None:
    assert str(SecProviderError()) == "SEC provider operation failed."
    assert str(SecRequestError()) == "SEC request construction failed."
    assert str(SecTransportError()) == "SEC request transport failed."
    assert str(SecTimeoutError()) == "SEC request timed out."
    assert str(SecResponseError(status_code=400)) == (
        "SEC returned an unexpected response."
    )
    assert str(SecRateLimitError()) == "SEC rate limit was reached."
    assert str(SecNotFoundError()) == "SEC resource was not found."
    assert str(SecServerError(status_code=500)) == "SEC returned a server error."


@pytest.mark.parametrize("status_code", [400, 599])
def test_response_status_boundaries(status_code: int) -> None:
    assert SecResponseError(status_code=status_code).status_code == status_code


@pytest.mark.parametrize("status_code", [399, 600, True])
def test_invalid_response_status_is_rejected(status_code: int) -> None:
    with pytest.raises(ValueError, match="status_code"):
        SecResponseError(status_code=status_code)


def test_response_url_is_sanitized_and_credentials_are_not_retained() -> None:
    error = SecResponseError(
        status_code=500,
        request_url=(
            "https://user:secret@data.sec.gov:8443/path/file.json"
            "?private=value#fragment"
        ),
    )

    assert error.request_url == "https://data.sec.gov:8443/path/file.json"
    assert "secret" not in error.request_url


@pytest.mark.parametrize(
    "request_url",
    [
        "http://data.sec.gov/path",
        "not-a-url",
        "https:///missing-host",
        "https://data.sec.gov:not-a-port/path",
        "https://data.sec.gov/path with-space",
        "https://data.sec.gov\\path",
        "https://data.sec.gov/path\x85value",
        "",
    ],
)
def test_malformed_and_non_https_urls_are_rejected(request_url: str) -> None:
    with pytest.raises(ValueError, match="request_url"):
        SecResponseError(status_code=500, request_url=request_url)


def test_transport_url_uses_the_same_sanitization() -> None:
    error = SecTransportError(
        request_url="https://identity@data.sec.gov/path?token=private#fragment"
    )

    assert error.request_url == "https://data.sec.gov/path"


@pytest.mark.parametrize(
    "timeout_seconds",
    [0.0, -1.0, float("inf"), float("nan"), True],
)
def test_invalid_timeout_metadata_is_rejected(timeout_seconds: float) -> None:
    with pytest.raises(ValueError, match="timeout_seconds"):
        SecTimeoutError(timeout_seconds=timeout_seconds)


def test_valid_timeout_metadata_is_stored_without_affecting_message() -> None:
    error = SecTimeoutError(
        request_url="https://data.sec.gov/path?secret=value",
        timeout_seconds=12,
    )

    assert error.timeout_seconds == 12.0
    assert error.request_url == "https://data.sec.gov/path"
    assert "secret" not in str(error)


def test_exception_strings_do_not_expose_sensitive_context() -> None:
    query_value = "query-secret-value"
    response_body = "private response body"
    contact_email = "sec-operations@example.test"
    user_agent = "Corporate Credit Risk Platform/0.1"
    error = SecResponseError(
        status_code=500,
        request_url=f"https://data.sec.gov/path?token={query_value}",
    )

    message = str(error)
    assert query_value not in message
    assert response_body not in message
    assert contact_email not in message
    assert user_agent not in message


def test_public_metadata_properties_are_immutable() -> None:
    response_error = SecResponseError(status_code=500)
    timeout_error = SecTimeoutError(timeout_seconds=10)

    with pytest.raises(AttributeError):
        response_error.status_code = 400  # type: ignore[misc]
    with pytest.raises(AttributeError):
        response_error.request_url = "https://changed.example.test"  # type: ignore[misc]
    with pytest.raises(AttributeError):
        timeout_error.timeout_seconds = 20  # type: ignore[misc]
