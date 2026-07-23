"""Tests for SEC request inputs."""

from dataclasses import FrozenInstanceError

import pytest

from credit_risk_platform.providers.sec import SecRequest


def test_valid_path_and_empty_query() -> None:
    request = SecRequest("/submissions/CIK0000000000.json", {})
    multiply_encoded = SecRequest("/path/%252541", {})

    assert request.path == "/submissions/CIK0000000000.json"
    assert request.query == {}
    assert multiply_encoded.path == "/path/%252541"


def test_sec_request_and_query_are_immutable_and_defensively_copied() -> None:
    source = {"format": "json"}
    request = SecRequest("/api/data", source)

    source["format"] = "xml"
    assert request.query == {"format": "json"}
    with pytest.raises(TypeError):
        request.query["format"] = "xml"  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        request.path = "/changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    "path",
    [
        "",
        " \t ",
        "relative/path",
        "https://data.sec.gov/path",
        "//other.example.test/path",
        "/path\\segment",
        "/path#fragment",
        "/path?key=value",
        "/./path",
        "/path/../other",
        "/path/%2e/other",
        "/path/%2E%2E/other",
        "/path/.%2e/other",
        "/path/%252e%252e/other",
        "/path%2fother",
        "/path%5Cother",
        "/path%252fother",
        "/path%255Cother",
        "/path with-space",
        "/path/%",
        "/path/%0a",
        "/path/\x85",
    ],
)
def test_invalid_paths_are_rejected(path: str) -> None:
    with pytest.raises(ValueError, match="path"):
        SecRequest(path, {})


def test_blank_query_keys_are_rejected() -> None:
    with pytest.raises(ValueError, match="query keys"):
        SecRequest("/path", {" \t ": "value"})


@pytest.mark.parametrize("query", [None, {1: "value"}, {"key": 1}])
def test_query_must_be_a_string_mapping(query: object) -> None:
    with pytest.raises(ValueError, match="query"):
        SecRequest("/path", query)  # type: ignore[arg-type]


class _DuplicateQuery:
    def items(self) -> list[tuple[str, str]]:
        return [("key", "first"), ("key", "second")]


def test_duplicate_case_sensitive_query_keys_are_rejected() -> None:
    with pytest.raises(ValueError, match="unique"):
        SecRequest("/path", _DuplicateQuery())  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "query",
    [
        {"bad\nkey": "value"},
        {"key": "bad\rvalue"},
        {"key": "bad\x00value"},
        {"key": "bad\x85value"},
    ],
)
def test_query_controls_are_rejected(query: dict[str, str]) -> None:
    with pytest.raises(ValueError, match="query"):
        SecRequest("/path", query)


def test_ordinary_query_strings_are_preserved_exactly() -> None:
    request = SecRequest(
        "/path",
        {"CaseSensitive": "value with spaces", "empty": "", "symbols": "a&b=c"},
    )

    assert dict(request.query) == {
        "CaseSensitive": "value with spaces",
        "empty": "",
        "symbols": "a&b=c",
    }
