"""Tests for pure SEC response-status interpretation."""

from inspect import signature

import pytest

import credit_risk_platform.providers as generic_providers
import credit_risk_platform.providers.sec as sec_providers
from credit_risk_platform.providers import HttpResponse
from credit_risk_platform.providers.sec import (
    SecNotFoundError,
    SecRateLimitError,
    SecResponseError,
    SecServerError,
    validate_sec_response,
)


def _response(
    status_code: int,
    *,
    headers: dict[str, str] | None = None,
    body: bytes = b"",
) -> HttpResponse:
    return HttpResponse(
        status_code=status_code,
        headers={} if headers is None else headers,
        body=body,
    )


@pytest.mark.parametrize(
    ("status_code", "body"),
    [
        (200, b'{"synthetic":"json-looking"}'),
        (201, b"\xff\x00\xfe"),
        (204, b""),
        (299, b"<html>synthetic success</html>"),
    ],
)
def test_success_statuses_return_exact_original_response(
    status_code: int,
    body: bytes,
) -> None:
    response = _response(
        status_code,
        headers={"X-Synthetic": "ordinary-value"},
        body=body,
    )
    original_headers = response.headers
    original_body = response.body

    returned = validate_sec_response(
        response,
        request_url="https://data.sec.gov/path",
    )

    assert returned is response
    assert returned.headers is original_headers
    assert returned.body is original_body
    assert returned.headers == {"X-Synthetic": "ordinary-value"}
    assert returned.body == body


def test_success_also_validates_optional_request_metadata() -> None:
    with pytest.raises(ValueError, match="request_url"):
        validate_sec_response(
            _response(200),
            request_url="http://data.sec.gov/path",
        )


@pytest.mark.parametrize(
    "status_code",
    [100, 199, 300, 399, 400, 401, 403, 405, 408, 409, 410, 422, 499],
)
def test_other_non_success_statuses_raise_exact_generic_response_error(
    status_code: int,
) -> None:
    with pytest.raises(SecResponseError) as exception_info:
        validate_sec_response(_response(status_code))

    assert type(exception_info.value) is SecResponseError
    assert exception_info.value.status_code == status_code


def test_not_found_mapping_has_precedence_over_generic_client_error() -> None:
    with pytest.raises(SecNotFoundError) as exception_info:
        validate_sec_response(_response(404))

    assert type(exception_info.value) is SecNotFoundError
    assert exception_info.value.status_code == 404


def test_rate_limit_mapping_has_precedence_over_generic_client_error() -> None:
    with pytest.raises(SecRateLimitError) as exception_info:
        validate_sec_response(_response(429))

    assert type(exception_info.value) is SecRateLimitError
    assert exception_info.value.status_code == 429


@pytest.mark.parametrize("status_code", [500, 503, 599])
def test_server_statuses_raise_exact_server_error(status_code: int) -> None:
    with pytest.raises(SecServerError) as exception_info:
        validate_sec_response(_response(status_code))

    assert type(exception_info.value) is SecServerError
    assert exception_info.value.status_code == status_code


def test_forbidden_and_timeout_statuses_are_not_overinterpreted() -> None:
    with pytest.raises(SecResponseError) as forbidden:
        validate_sec_response(_response(403))
    with pytest.raises(SecResponseError) as timeout:
        validate_sec_response(_response(408))

    assert type(forbidden.value) is SecResponseError
    assert type(timeout.value) is SecResponseError
    assert not isinstance(forbidden.value, SecRateLimitError)
    assert timeout.value.status_code == 408


def test_missing_request_metadata_is_supported() -> None:
    with pytest.raises(SecNotFoundError) as exception_info:
        validate_sec_response(_response(404))

    assert exception_info.value.request_url is None


def test_request_url_without_sensitive_components_is_preserved() -> None:
    with pytest.raises(SecServerError) as exception_info:
        validate_sec_response(
            _response(500),
            request_url="https://data.sec.gov:8443/path/file.json",
        )

    assert (
        exception_info.value.request_url == "https://data.sec.gov:8443/path/file.json"
    )


def test_request_url_is_sanitized_by_existing_exception_boundary() -> None:
    query_marker = "QUERY_VALUE_MARKER_7F31"
    fragment_marker = "FRAGMENT_MARKER_8A42"
    credential_marker = "CREDENTIAL_MARKER_9B53"

    with pytest.raises(SecRateLimitError) as exception_info:
        validate_sec_response(
            _response(429),
            request_url=(
                f"https://identity:{credential_marker}@data.sec.gov:8443/path"
                f"?item={query_marker}#{fragment_marker}"
            ),
        )

    error = exception_info.value
    assert error.request_url == "https://data.sec.gov:8443/path"
    for marker in (query_marker, fragment_marker, credential_marker):
        assert marker not in error.request_url
        assert marker not in str(error)
        assert marker not in repr(error)


@pytest.mark.parametrize(
    "request_url",
    [
        "http://data.sec.gov/path",
        "not-a-url",
        "https:///missing-host",
        "https://data.sec.gov:not-a-port/path",
        "",
        42,
    ],
)
def test_invalid_request_metadata_is_rejected_safely(request_url: object) -> None:
    with pytest.raises(ValueError, match="request_url"):
        validate_sec_response(
            _response(400),
            request_url=request_url,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "body",
    [
        b'{"BODY_MARKER_JSON_1A2B":"value"}',
        b"<html>BODY_MARKER_HTML_2B3C</html>",
        b"\x00\xffBODY_MARKER_BINARY_3C4D\x80",
    ],
)
def test_body_and_header_content_never_enters_exception(
    body: bytes,
) -> None:
    header_marker = "HEADER_VALUE_MARKER_4D5E"
    response = _response(
        500,
        headers={"X-Synthetic-Marker": header_marker},
        body=body,
    )
    original_headers = response.headers
    original_body = response.body

    with pytest.raises(SecServerError) as exception_info:
        validate_sec_response(
            response,
            request_url="https://data.sec.gov/path",
        )

    error = exception_info.value
    exposed_values = (
        str(error),
        repr(error),
        str(error.status_code),
        str(error.request_url),
    )
    for exposed in exposed_values:
        assert header_marker not in exposed
        assert body.decode("latin-1") not in exposed
    assert not hasattr(error, "response")
    assert not hasattr(error, "headers")
    assert not hasattr(error, "body")
    assert response.headers is original_headers
    assert response.body is original_body


def test_user_identity_is_not_accepted_or_stored() -> None:
    parameters = signature(validate_sec_response).parameters

    assert set(parameters) == {"response", "request_url"}
    with pytest.raises(SecResponseError) as exception_info:
        validate_sec_response(_response(400))

    error = exception_info.value
    assert not hasattr(error, "request_headers")
    assert not hasattr(error, "user_agent")
    assert not hasattr(error, "contact_email")


@pytest.mark.parametrize("invalid_response", [None, object(), "response"])
def test_arbitrary_response_like_inputs_are_rejected(
    invalid_response: object,
) -> None:
    with pytest.raises(ValueError, match="response must be an HttpResponse"):
        validate_sec_response(invalid_response)  # type: ignore[arg-type]


def test_mapper_is_exported_only_from_sec_package() -> None:
    assert sec_providers.validate_sec_response is validate_sec_response
    assert "validate_sec_response" in sec_providers.__all__
    assert "validate_sec_response" not in generic_providers.__all__
    assert not hasattr(generic_providers, "validate_sec_response")
