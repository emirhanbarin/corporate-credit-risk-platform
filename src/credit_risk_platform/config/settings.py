"""Application settings and explicit environment-loading boundaries."""

from __future__ import annotations

import math
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Self
from urllib.parse import urlsplit, urlunsplit

_DEFAULT_SEC_DATA_BASE_URL = "https://data.sec.gov"
_DEFAULT_SEC_FILES_BASE_URL = "https://www.sec.gov"
_DEFAULT_SEC_REQUEST_TIMEOUT_SECONDS = 30.0
_DEFAULT_SEC_MAX_REQUESTS_PER_SECOND = 5.0

_MAX_USER_AGENT_LENGTH = 256
_MAX_EMAIL_LENGTH = 254
_MAX_EMAIL_LOCAL_PART_LENGTH = 64
_MAX_REQUEST_TIMEOUT_SECONDS = 300.0
_MAX_REQUESTS_PER_SECOND = 10.0

_USER_AGENT_PLACEHOLDERS = frozenset(
    {"youruseragent", "changeme", "example", "placeholder", "todo"}
)
_EMAIL_LOCAL_PART_PLACEHOLDERS = frozenset(
    {"youremail", "changeme", "example", "placeholder", "todo"}
)
_EMAIL_PATTERN = re.compile(
    r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+"
)


class ConfigurationError(ValueError):
    """Raised when application configuration is missing or invalid."""


@dataclass(frozen=True, slots=True)
class AppSettings:
    """Immutable, validated runtime settings for future SEC access."""

    sec_user_agent: str
    sec_contact_email: str
    sec_data_base_url: str = _DEFAULT_SEC_DATA_BASE_URL
    sec_files_base_url: str = _DEFAULT_SEC_FILES_BASE_URL
    sec_request_timeout_seconds: float = _DEFAULT_SEC_REQUEST_TIMEOUT_SECONDS
    sec_max_requests_per_second: float = _DEFAULT_SEC_MAX_REQUESTS_PER_SECOND

    def __post_init__(self) -> None:
        """Normalize and validate settings regardless of construction path."""
        user_agent = self.sec_user_agent.strip()
        contact_email = self.sec_contact_email.strip()

        _validate_user_agent(user_agent)
        _validate_contact_email(contact_email)
        data_base_url = _validate_and_normalize_base_url(
            self.sec_data_base_url,
            "SEC_DATA_BASE_URL",
        )
        files_base_url = _validate_and_normalize_base_url(
            self.sec_files_base_url,
            "SEC_FILES_BASE_URL",
        )
        _validate_positive_number(
            self.sec_request_timeout_seconds,
            "SEC_REQUEST_TIMEOUT_SECONDS",
            _MAX_REQUEST_TIMEOUT_SECONDS,
        )
        _validate_positive_number(
            self.sec_max_requests_per_second,
            "SEC_MAX_REQUESTS_PER_SECOND",
            _MAX_REQUESTS_PER_SECOND,
        )

        object.__setattr__(self, "sec_user_agent", user_agent)
        object.__setattr__(self, "sec_contact_email", contact_email)
        object.__setattr__(self, "sec_data_base_url", data_base_url)
        object.__setattr__(self, "sec_files_base_url", files_base_url)

    @classmethod
    def from_mapping(cls, values: Mapping[str, str]) -> Self:
        """Build settings using only the supplied mapping."""
        return cls(
            sec_user_agent=_required_value(values, "SEC_USER_AGENT"),
            sec_contact_email=_required_value(values, "SEC_CONTACT_EMAIL"),
            sec_data_base_url=_optional_value(
                values,
                "SEC_DATA_BASE_URL",
                _DEFAULT_SEC_DATA_BASE_URL,
            ),
            sec_files_base_url=_optional_value(
                values,
                "SEC_FILES_BASE_URL",
                _DEFAULT_SEC_FILES_BASE_URL,
            ),
            sec_request_timeout_seconds=_optional_number(
                values,
                "SEC_REQUEST_TIMEOUT_SECONDS",
                _DEFAULT_SEC_REQUEST_TIMEOUT_SECONDS,
            ),
            sec_max_requests_per_second=_optional_number(
                values,
                "SEC_MAX_REQUESTS_PER_SECOND",
                _DEFAULT_SEC_MAX_REQUESTS_PER_SECOND,
            ),
        )

    @classmethod
    def from_environment(cls) -> Self:
        """Build settings from the current process environment explicitly."""
        return cls.from_mapping(os.environ)


def _required_value(values: Mapping[str, str], field: str) -> str:
    raw_value = values.get(field)
    if raw_value is None or not raw_value.strip():
        raise ConfigurationError(f"{field} is required.")
    return raw_value.strip()


def _optional_value(values: Mapping[str, str], field: str, default: str) -> str:
    raw_value = values.get(field)
    if raw_value is None:
        return default
    if not isinstance(raw_value, str):
        raise ConfigurationError(f"{field} must be a string.")
    return raw_value.strip()


def _optional_number(values: Mapping[str, str], field: str, default: float) -> float:
    raw_value = values.get(field)
    if raw_value is None or not raw_value.strip():
        return default
    try:
        return float(raw_value.strip())
    except ValueError as error:
        raise ConfigurationError(
            f"{field} must be a positive finite number."
        ) from error


def _validate_user_agent(value: str) -> None:
    field = "SEC_USER_AGENT"
    if not value:
        raise ConfigurationError(f"{field} is required.")
    if _contains_control_character(value):
        raise ConfigurationError(f"{field} must not contain control characters.")
    if len(value) > _MAX_USER_AGENT_LENGTH:
        raise ConfigurationError(
            f"{field} must be no longer than {_MAX_USER_AGENT_LENGTH} characters."
        )
    if _canonical_placeholder(value) in _USER_AGENT_PLACEHOLDERS:
        raise ConfigurationError(f"{field} must not use a placeholder value.")
    if not any(character.isalpha() for character in value):
        raise ConfigurationError(
            f"{field} must identify the application in human-readable text."
        )


def _validate_contact_email(value: str) -> None:
    field = "SEC_CONTACT_EMAIL"
    if not value:
        raise ConfigurationError(f"{field} is required.")
    if any(character.isspace() for character in value):
        raise ConfigurationError(f"{field} must not contain whitespace.")
    if _contains_control_character(value):
        raise ConfigurationError(f"{field} must not contain control characters.")
    if len(value) > _MAX_EMAIL_LENGTH:
        raise ConfigurationError(
            f"{field} must be no longer than {_MAX_EMAIL_LENGTH} characters."
        )
    if _EMAIL_PATTERN.fullmatch(value) is None:
        raise ConfigurationError(f"{field} must be a plausible email address.")

    local_part, _, _ = value.partition("@")
    if len(local_part) > _MAX_EMAIL_LOCAL_PART_LENGTH:
        raise ConfigurationError(
            f"{field} local part must be no longer than "
            f"{_MAX_EMAIL_LOCAL_PART_LENGTH} characters."
        )
    if _canonical_placeholder(local_part) in _EMAIL_LOCAL_PART_PLACEHOLDERS:
        raise ConfigurationError(f"{field} must not use a placeholder value.")


def _validate_and_normalize_base_url(value: str, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ConfigurationError(f"{field} must be a non-empty string.")
    if _contains_control_character(value):
        raise ConfigurationError(f"{field} must not contain control characters.")
    if any(character.isspace() for character in value):
        raise ConfigurationError(f"{field} must not contain whitespace.")
    if "\\" in value:
        raise ConfigurationError(f"{field} must not contain backslashes.")
    if "?" in value:
        raise ConfigurationError(f"{field} must not include a query string.")
    if "#" in value:
        raise ConfigurationError(f"{field} must not include a fragment.")

    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        parsed = None
        hostname = None
        port = None

    if parsed is None:
        raise ConfigurationError(f"{field} must be a valid HTTPS URL.")

    if parsed.scheme.casefold() != "https":
        raise ConfigurationError(f"{field} must use HTTPS.")
    if hostname is None:
        raise ConfigurationError(f"{field} must include a hostname.")
    if port is not None and port <= 0:
        raise ConfigurationError(f"{field} must be a valid HTTPS URL.")
    if parsed.username is not None or parsed.password is not None:
        raise ConfigurationError(f"{field} must not include credentials.")
    if parsed.path not in {"", "/"}:
        raise ConfigurationError(f"{field} must not include a path.")

    return urlunsplit(("https", parsed.netloc, "", "", ""))


def _validate_positive_number(value: float, field: str, maximum: float) -> None:
    if not math.isfinite(value) or value <= 0:
        raise ConfigurationError(f"{field} must be a positive finite number.")
    if value > maximum:
        raise ConfigurationError(f"{field} must not exceed {maximum:g}.")


def _contains_control_character(value: str) -> bool:
    return any(not character.isprintable() for character in value)


def _canonical_placeholder(value: str) -> str:
    return "".join(character for character in value.casefold() if character.isalnum())
