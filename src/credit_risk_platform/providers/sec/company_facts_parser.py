"""Strict parsing of raw SEC Company Facts artifacts into provider contracts."""

from __future__ import annotations

import json
import re
import unicodedata
from datetime import date
from decimal import Decimal, DecimalException
from enum import Enum
from types import MappingProxyType
from typing import NoReturn, cast

from credit_risk_platform.providers.sec.company_facts_models import (
    SecCompanyFactConcept,
    SecCompanyFactObservation,
    SecCompanyFacts,
)
from credit_risk_platform.providers.sec.raw_artifact import (
    SecRawArtifact,
    SecSource,
)
from credit_risk_platform.providers.sec.ticker_mapping import SecCik

_TOP_LEVEL_FIELDS = frozenset({"cik", "entityName", "facts"})
_CONCEPT_FIELDS = frozenset({"label", "description", "units"})
_OBSERVATION_REQUIRED_FIELDS = frozenset({"val", "accn", "form", "filed", "end"})
_OBSERVATION_OPTIONAL_FIELDS = frozenset({"fy", "fp", "frame", "start"})
_OBSERVATION_FIELDS = _OBSERVATION_REQUIRED_FIELDS | _OBSERVATION_OPTIONAL_FIELDS
_ISO_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
_UTF8_BOM = b"\xef\xbb\xbf"


class SecCompanyFactsParseReason(str, Enum):
    """Stable machine-readable reasons for Company Facts parsing failure."""

    INVALID_ARTIFACT = "invalid_artifact"
    INVALID_SOURCE = "invalid_source"
    INVALID_EXPECTED_CIK = "invalid_expected_cik"
    INVALID_UTF8 = "invalid_utf8"
    INVALID_JSON = "invalid_json"
    DUPLICATE_JSON_KEY = "duplicate_json_key"
    INVALID_TOP_LEVEL = "invalid_top_level"
    MISSING_FIELD = "missing_field"
    UNEXPECTED_FIELD = "unexpected_field"
    INVALID_FIELD_TYPE = "invalid_field_type"
    INVALID_FIELD_VALUE = "invalid_field_value"
    CIK_MISMATCH = "cik_mismatch"
    INVALID_DATE = "invalid_date"
    INVALID_NUMBER = "invalid_number"

    def __str__(self) -> str:
        return self.value


class SecCompanyFactsParseError(ValueError):
    """Safe failure raised for an invalid SEC Company Facts artifact."""

    __slots__ = ("_reason",)
    _message = "SEC Company Facts document is invalid."

    def __init__(self, reason: SecCompanyFactsParseReason) -> None:
        super().__init__(self._message)
        self._reason = reason

    @property
    def reason(self) -> SecCompanyFactsParseReason:
        """Return the stable machine-readable failure reason."""
        return self._reason


def parse_company_facts(
    artifact: SecRawArtifact,
    *,
    expected_cik: SecCik,
) -> SecCompanyFacts:
    """Parse exact Company Facts bytes without selection or normalization."""
    if not isinstance(artifact, SecRawArtifact):
        _fail(SecCompanyFactsParseReason.INVALID_ARTIFACT)
    if artifact.source is not SecSource.COMPANY_FACTS:
        _fail(SecCompanyFactsParseReason.INVALID_SOURCE)
    if not isinstance(expected_cik, SecCik):
        _fail(SecCompanyFactsParseReason.INVALID_EXPECTED_CIK)

    decoded = _decode_json(artifact.body)
    if isinstance(decoded, SecCompanyFactsParseReason):
        _fail(decoded)
    if not isinstance(decoded, dict):
        _fail(SecCompanyFactsParseReason.INVALID_TOP_LEVEL)

    document = cast(dict[str, object], decoded)
    _validate_exact_fields(document, _TOP_LEVEL_FIELDS, _TOP_LEVEL_FIELDS)

    cik = _parse_cik(document["cik"])
    if cik != expected_cik:
        _fail(SecCompanyFactsParseReason.CIK_MISMATCH)

    entity_name = _parse_required_text(document["entityName"])
    facts = _parse_facts(document["facts"])
    return SecCompanyFacts(
        cik=cik,
        entity_name=entity_name,
        facts=facts,
        provenance=artifact,
    )


def _decode_json(body: bytes) -> object | SecCompanyFactsParseReason:
    if body.startswith(_UTF8_BOM):
        return SecCompanyFactsParseReason.INVALID_UTF8
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError:
        return SecCompanyFactsParseReason.INVALID_UTF8

    try:
        decoded: object = json.loads(
            text,
            object_pairs_hook=_object_from_pairs,
            parse_float=Decimal,
            parse_constant=_reject_non_finite_constant,
        )
        return decoded
    except _DuplicateJsonKeyError:
        return SecCompanyFactsParseReason.DUPLICATE_JSON_KEY
    except _InvalidNumberError:
        return SecCompanyFactsParseReason.INVALID_NUMBER
    except DecimalException:
        return SecCompanyFactsParseReason.INVALID_NUMBER
    except (json.JSONDecodeError, RecursionError):
        return SecCompanyFactsParseReason.INVALID_JSON


def _object_from_pairs(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJsonKeyError
        result[key] = value
    return result


def _reject_non_finite_constant(_value: str) -> NoReturn:
    raise _InvalidNumberError


def _parse_cik(value: object) -> SecCik:
    if isinstance(value, bool) or not isinstance(value, int):
        _fail(SecCompanyFactsParseReason.INVALID_FIELD_TYPE)
    try:
        parsed = SecCik(value)
    except ValueError:
        parsed = None
    if parsed is None:
        _fail(SecCompanyFactsParseReason.INVALID_FIELD_VALUE)
    return parsed


def _parse_facts(
    value: object,
) -> MappingProxyType[str, MappingProxyType[str, SecCompanyFactConcept]]:
    if not isinstance(value, dict):
        _fail(SecCompanyFactsParseReason.INVALID_FIELD_TYPE)

    source_facts = cast(dict[str, object], value)
    facts: dict[str, MappingProxyType[str, SecCompanyFactConcept]] = {}
    for taxonomy, concepts_value in source_facts.items():
        _validate_identifier(taxonomy)
        if not isinstance(concepts_value, dict):
            _fail(SecCompanyFactsParseReason.INVALID_FIELD_TYPE)

        source_concepts = cast(dict[str, object], concepts_value)
        concepts: dict[str, SecCompanyFactConcept] = {}
        for concept_name, concept_value in source_concepts.items():
            _validate_identifier(concept_name)
            concepts[concept_name] = _parse_concept(concept_value)
        facts[taxonomy] = MappingProxyType(concepts)

    return MappingProxyType(facts)


def _parse_concept(value: object) -> SecCompanyFactConcept:
    if not isinstance(value, dict):
        _fail(SecCompanyFactsParseReason.INVALID_FIELD_TYPE)
    concept = cast(dict[str, object], value)
    _validate_exact_fields(concept, _CONCEPT_FIELDS, _CONCEPT_FIELDS)

    label = _parse_required_text(concept["label"])
    description = _parse_description(concept["description"])
    units_value = concept["units"]
    if not isinstance(units_value, dict):
        _fail(SecCompanyFactsParseReason.INVALID_FIELD_TYPE)

    source_units = cast(dict[str, object], units_value)
    units: dict[str, tuple[SecCompanyFactObservation, ...]] = {}
    for unit, observations_value in source_units.items():
        _validate_identifier(unit)
        if not isinstance(observations_value, list):
            _fail(SecCompanyFactsParseReason.INVALID_FIELD_TYPE)
        units[unit] = tuple(
            _parse_observation(observation) for observation in observations_value
        )

    return SecCompanyFactConcept(
        label=label,
        description=description,
        units=units,
    )


def _parse_observation(value: object) -> SecCompanyFactObservation:
    if not isinstance(value, dict):
        _fail(SecCompanyFactsParseReason.INVALID_FIELD_TYPE)
    observation = cast(dict[str, object], value)
    _validate_exact_fields(
        observation,
        _OBSERVATION_REQUIRED_FIELDS,
        _OBSERVATION_FIELDS,
    )

    return SecCompanyFactObservation(
        val=_parse_number(observation["val"]),
        accn=_parse_required_text(observation["accn"]),
        form=_parse_required_text(observation["form"]),
        filed=_parse_date(observation["filed"]),
        end=_parse_date(observation["end"]),
        fy=(_parse_fiscal_year(observation["fy"]) if "fy" in observation else None),
        fp=(_parse_required_text(observation["fp"]) if "fp" in observation else None),
        frame=(
            _parse_required_text(observation["frame"])
            if "frame" in observation
            else None
        ),
        start=(_parse_date(observation["start"]) if "start" in observation else None),
    )


def _parse_number(value: object) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, Decimal)):
        _fail(SecCompanyFactsParseReason.INVALID_NUMBER)
    return Decimal(value)


def _parse_fiscal_year(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        _fail(SecCompanyFactsParseReason.INVALID_FIELD_TYPE)
    return value


def _parse_date(value: object) -> date:
    if not isinstance(value, str):
        _fail(SecCompanyFactsParseReason.INVALID_DATE)
    if _ISO_DATE.fullmatch(value) is None:
        _fail(SecCompanyFactsParseReason.INVALID_DATE)
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        parsed = None
    if parsed is None:
        _fail(SecCompanyFactsParseReason.INVALID_DATE)
    return parsed


def _parse_required_text(value: object) -> str:
    if not isinstance(value, str):
        _fail(SecCompanyFactsParseReason.INVALID_FIELD_TYPE)
    if (
        not value
        or value.strip() != value
        or any(_is_control(character) for character in value)
    ):
        _fail(SecCompanyFactsParseReason.INVALID_FIELD_VALUE)
    return value


def _parse_description(value: object) -> str:
    if not isinstance(value, str):
        _fail(SecCompanyFactsParseReason.INVALID_FIELD_TYPE)
    if any(_is_control(character) for character in value):
        _fail(SecCompanyFactsParseReason.INVALID_FIELD_VALUE)
    return value


def _validate_identifier(value: str) -> None:
    if (
        not value
        or value.strip() != value
        or any(_is_control(character) for character in value)
    ):
        _fail(SecCompanyFactsParseReason.INVALID_FIELD_VALUE)


def _validate_exact_fields(
    value: dict[str, object],
    required: frozenset[str],
    allowed: frozenset[str],
) -> None:
    keys = value.keys()
    if not required.issubset(keys):
        _fail(SecCompanyFactsParseReason.MISSING_FIELD)
    if not keys <= allowed:
        _fail(SecCompanyFactsParseReason.UNEXPECTED_FIELD)


def _is_control(character: str) -> bool:
    return unicodedata.category(character) == "Cc"


def _fail(reason: SecCompanyFactsParseReason) -> NoReturn:
    raise SecCompanyFactsParseError(reason)


class _DuplicateJsonKeyError(ValueError):
    __slots__ = ()


class _InvalidNumberError(ValueError):
    __slots__ = ()
