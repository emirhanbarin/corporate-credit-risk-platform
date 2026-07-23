"""Immutable SEC request inputs."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from urllib.parse import unquote

_INVALID_PERCENT_ESCAPE = re.compile(r"%(?![0-9A-Fa-f]{2})")
_ENCODED_SLASH_OR_BACKSLASH = re.compile(r"%(?:2f|5c)", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class SecRequest:
    """A validated SEC API path and query mapping."""

    path: str
    query: Mapping[str, str]

    def __post_init__(self) -> None:
        _validate_path(self.path)
        query = _copy_and_validate_query(self.query)
        object.__setattr__(self, "query", query)


def _validate_path(value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("path must be a non-blank absolute API path.")
    if any(character.isspace() or _is_control(character) for character in value):
        raise ValueError("path must not contain whitespace or control characters.")
    if "\\" in value:
        raise ValueError("path must not contain backslashes.")
    if not value.startswith("/") or value.startswith("//"):
        raise ValueError("path must begin with exactly one leading slash.")
    if "?" in value:
        raise ValueError("path must not contain query syntax.")
    if "#" in value:
        raise ValueError("path must not contain a fragment.")

    if _INVALID_PERCENT_ESCAPE.search(value):
        raise ValueError("path must not contain malformed percent encoding.")
    if _ENCODED_SLASH_OR_BACKSLASH.search(value):
        raise ValueError("path must not contain encoded slashes or backslashes.")

    decoded = value
    for _ in range(3):
        next_decoded = unquote(decoded)
        if next_decoded == decoded:
            break
        decoded = next_decoded
        if _ENCODED_SLASH_OR_BACKSLASH.search(decoded):
            raise ValueError("path must not contain encoded slashes or backslashes.")
        if any(_is_control(character) for character in decoded):
            raise ValueError("path must not contain encoded control characters.")
        if any(segment in {".", ".."} for segment in decoded.split("/")):
            raise ValueError("path must not contain dot path segments.")

    if any(segment in {".", ".."} for segment in value.split("/")):
        raise ValueError("path must not contain dot path segments.")


def _copy_and_validate_query(query: Mapping[str, str]) -> Mapping[str, str]:
    copied: dict[str, str] = {}

    try:
        query_items = query.items()
    except AttributeError as error:
        raise ValueError("query must be a string mapping.") from error

    for key, value in query_items:
        if not isinstance(key, str) or not key.strip():
            raise ValueError("query keys must be non-blank strings.")
        if not isinstance(value, str):
            raise ValueError("query values must be strings.")
        if any(_is_control(character) for character in key):
            raise ValueError("query keys must not contain control characters.")
        if any(_is_control(character) for character in value):
            raise ValueError("query values must not contain control characters.")
        if key in copied:
            raise ValueError("query keys must be unique.")
        copied[key] = value

    return MappingProxyType(copied)


def _is_control(character: str) -> bool:
    return unicodedata.category(character) == "Cc"
