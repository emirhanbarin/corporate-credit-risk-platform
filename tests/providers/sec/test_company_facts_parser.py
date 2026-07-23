"""Tests for strict, deterministic SEC Company Facts parsing."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

import credit_risk_platform.providers as generic_providers
import credit_risk_platform.providers.sec as sec_providers
import credit_risk_platform.providers.sec.company_facts_parser as parser_module
from credit_risk_platform.providers.sec import (
    SecCik,
    SecCompanyFactConcept,
    SecCompanyFactObservation,
    SecCompanyFacts,
    SecCompanyFactsParseError,
    SecCompanyFactsParseReason,
    SecRawArtifact,
    SecSource,
    parse_company_facts,
)

_RETRIEVED_AT = datetime(2026, 7, 25, 12, 30, 45, 123456, tzinfo=timezone.utc)
_MICROSOFT_CIK = SecCik(789019)


def _observation(**overrides: object) -> dict[str, object]:
    result: dict[str, object] = {
        "val": 245122000000,
        "accn": "0000000000-24-000001",
        "form": "10-K",
        "filed": "2024-07-30",
        "end": "2024-06-30",
    }
    result.update(overrides)
    return result


def _concept(**overrides: object) -> dict[str, object]:
    result: dict[str, object] = {
        "label": "Revenues",
        "description": "Synthetic provider description.",
        "units": {"USD": [_observation()]},
    }
    result.update(overrides)
    return result


def _document(**overrides: object) -> dict[str, object]:
    result: dict[str, object] = {
        "cik": 789019,
        "entityName": "MICROSOFT CORPORATION",
        "facts": {"us-gaap": {"Revenues": _concept()}},
    }
    result.update(overrides)
    return result


def _body(document: object) -> bytes:
    return json.dumps(document, separators=(",", ":")).encode()


def _artifact(
    body: bytes,
    *,
    source: SecSource = SecSource.COMPANY_FACTS,
) -> SecRawArtifact:
    return SecRawArtifact(
        source=source,
        retrieved_at=_RETRIEVED_AT,
        body=body,
    )


def _parse(
    document: object,
    *,
    expected_cik: SecCik = _MICROSOFT_CIK,
) -> SecCompanyFacts:
    return parse_company_facts(
        _artifact(_body(document)),
        expected_cik=expected_cik,
    )


def _assert_body_error(
    body: bytes,
    reason: SecCompanyFactsParseReason,
    *,
    source: SecSource = SecSource.COMPANY_FACTS,
    expected_cik: SecCik = _MICROSOFT_CIK,
) -> SecCompanyFactsParseError:
    with pytest.raises(SecCompanyFactsParseError) as exception_info:
        parse_company_facts(
            _artifact(body, source=source),
            expected_cik=expected_cik,
        )
    error = exception_info.value
    assert error.reason is reason
    assert str(error) == "SEC Company Facts document is invalid."
    return error


@pytest.mark.parametrize(
    ("cik_value", "entity_name"),
    [
        (1, "ONE DIGIT ENTITY"),
        (789019, "MICROSOFT CORPORATION"),
        (9_999_999_999, "TEN DIGIT ENTITY"),
    ],
)
def test_parse_minimal_valid_document_and_canonical_cik(
    cik_value: int,
    entity_name: str,
) -> None:
    document = _parse(
        {
            "cik": cik_value,
            "entityName": entity_name,
            "facts": {},
        },
        expected_cik=SecCik(cik_value),
    )

    assert document.cik == SecCik(cik_value)
    assert str(document.cik) == f"{cik_value:010d}"
    assert document.entity_name == entity_name
    assert document.facts == {}


def test_parse_multiple_taxonomies_concepts_units_and_observations() -> None:
    duration = _observation(
        val=245122000000,
        fy=2024,
        fp="FY",
        frame="CY2023",
        start="2023-07-01",
    )
    prior = _observation(
        val=-1,
        accn="0000000000-23-000001",
        form="10-Q",
        filed="2023-07-31",
        end="2023-06-30",
    )
    instant = _observation(
        val=0,
        accn="0000000000-24-000002",
        form="8-K",
        filed="2024-08-01",
        end="2024-07-31",
    )
    document = _parse(
        _document(
            entityName="Microsoft Corporation, Inc.",
            facts={
                "us-gaap": {
                    "Revenues": _concept(
                        label="Revenue",
                        units={"USD": [duration, prior], "shares": []},
                    ),
                    "AssetsCurrent": _concept(
                        label="Current Assets",
                        description="",
                        units={"USD": [instant]},
                    ),
                },
                "custom-taxonomy": {
                    "CustomConcept": _concept(
                        label="Provider Custom Label",
                        units={},
                    )
                },
            },
        )
    )

    assert document.entity_name == "Microsoft Corporation, Inc."
    assert tuple(document.facts) == ("us-gaap", "custom-taxonomy")
    assert tuple(document.facts["us-gaap"]) == ("Revenues", "AssetsCurrent")
    revenues = document.facts["us-gaap"]["Revenues"]
    assert revenues.label == "Revenue"
    assert revenues.description == "Synthetic provider description."
    assert tuple(revenues.units) == ("USD", "shares")
    assert len(revenues.units["USD"]) == 2
    current_assets = document.facts["us-gaap"]["AssetsCurrent"]
    assert current_assets.description == ""
    assert document.facts["custom-taxonomy"]["CustomConcept"].units == {}

    parsed_duration = revenues.units["USD"][0]
    assert parsed_duration.val == Decimal("245122000000")
    assert parsed_duration.fy == 2024
    assert parsed_duration.fp == "FY"
    assert parsed_duration.frame == "CY2023"
    assert parsed_duration.start == date(2023, 7, 1)
    assert parsed_duration.end == date(2024, 6, 30)
    parsed_instant = current_assets.units["USD"][0]
    assert parsed_instant.start is None
    assert parsed_instant.fy is None
    assert parsed_instant.fp is None
    assert parsed_instant.frame is None


@pytest.mark.parametrize(
    ("encoded_value", "expected"),
    [
        ("0", Decimal("0")),
        ("-123", Decimal("-123")),
        ("0.125", Decimal("0.125")),
        (
            "1234567890123456789012345678901234567890",
            Decimal("1234567890123456789012345678901234567890"),
        ),
    ],
)
def test_numeric_values_are_preserved_exactly_as_decimal(
    encoded_value: str,
    expected: Decimal,
) -> None:
    body = (
        b'{"cik":789019,"entityName":"ENTITY","facts":{"us-gaap":'
        b'{"Concept":{"label":"Label","description":"","units":{"USD":'
        b'[{"val":'
        + encoded_value.encode()
        + b',"accn":"A","form":"FORM","filed":"2024-01-01",'
        b'"end":"2023-12-31"}]}}}}}'
    )

    document = parse_company_facts(
        _artifact(body),
        expected_cik=SecCik(789019),
    )

    value = document.facts["us-gaap"]["Concept"].units["USD"][0].val
    assert value == expected
    assert isinstance(value, Decimal)


def test_provenance_is_exact_originating_artifact_without_body_duplication() -> None:
    artifact = _artifact(_body(_document()))

    document = parse_company_facts(artifact, expected_cik=SecCik(789019))

    assert document.provenance is artifact
    assert document.provenance.body is artifact.body
    assert document.provenance.sha256 is artifact.sha256


def test_repeated_parsing_is_deterministic_and_does_not_mutate_artifact() -> None:
    artifact = _artifact(_body(_document()))
    original_body = artifact.body

    first = parse_company_facts(artifact, expected_cik=SecCik(789019))
    second = parse_company_facts(artifact, expected_cik=SecCik(789019))

    assert first == second
    assert first is not second
    assert first.provenance is artifact
    assert second.provenance is artifact
    assert artifact.body is original_body


def test_parsed_nested_collections_are_immutable_and_contracts_are_frozen() -> None:
    document = _parse(_document())
    concept = document.facts["us-gaap"]["Revenues"]
    observation = concept.units["USD"][0]

    assert isinstance(document, SecCompanyFacts)
    assert isinstance(concept, SecCompanyFactConcept)
    assert isinstance(observation, SecCompanyFactObservation)
    assert isinstance(concept.units["USD"], tuple)
    with pytest.raises(TypeError):
        document.facts["other"] = {}  # type: ignore[index]
    with pytest.raises(TypeError):
        document.facts["us-gaap"]["Other"] = concept  # type: ignore[index]
    with pytest.raises(TypeError):
        concept.units["shares"] = ()  # type: ignore[index]


def test_non_artifact_is_rejected_with_fixed_reason() -> None:
    marker = "INVALID_ARTIFACT_MARKER_2B3C"

    class _ArtifactLike:
        source = SecSource.COMPANY_FACTS
        body = marker.encode()

    with pytest.raises(SecCompanyFactsParseError) as exception_info:
        parse_company_facts(
            _ArtifactLike(),  # type: ignore[arg-type]
            expected_cik=SecCik(789019),
        )

    error = exception_info.value
    assert error.reason is SecCompanyFactsParseReason.INVALID_ARTIFACT
    _assert_safe_error(error, marker)


def test_reason_codes_have_stable_string_values() -> None:
    assert str(SecCompanyFactsParseReason.DUPLICATE_JSON_KEY) == "duplicate_json_key"
    assert len(set(SecCompanyFactsParseReason)) == 14


def test_wrong_artifact_source_is_rejected() -> None:
    _assert_body_error(
        _body(_document()),
        SecCompanyFactsParseReason.INVALID_SOURCE,
        source=SecSource.COMPANY_TICKERS,
    )


@pytest.mark.parametrize("expected_cik", [789019, "0000789019", True, None])
def test_non_cik_expected_identity_is_rejected(expected_cik: object) -> None:
    with pytest.raises(SecCompanyFactsParseError) as exception_info:
        parse_company_facts(
            _artifact(_body(_document())),
            expected_cik=expected_cik,  # type: ignore[arg-type]
        )

    assert (
        exception_info.value.reason is SecCompanyFactsParseReason.INVALID_EXPECTED_CIK
    )


def test_payload_cik_mismatch_fails_closed() -> None:
    _assert_body_error(
        _body(_document(cik=320193)),
        SecCompanyFactsParseReason.CIK_MISMATCH,
    )


@pytest.mark.parametrize(
    ("body", "reason"),
    [
        (b"", SecCompanyFactsParseReason.INVALID_JSON),
        (b" \t\r\n", SecCompanyFactsParseReason.INVALID_JSON),
        (b"\xff\xfe", SecCompanyFactsParseReason.INVALID_UTF8),
        (
            b'\xef\xbb\xbf{"cik":789019,"entityName":"ENTITY","facts":{}}',
            SecCompanyFactsParseReason.INVALID_UTF8,
        ),
        (b'{"cik":', SecCompanyFactsParseReason.INVALID_JSON),
        (b"{} {}", SecCompanyFactsParseReason.INVALID_JSON),
        (b"[]", SecCompanyFactsParseReason.INVALID_TOP_LEVEL),
        (b"null", SecCompanyFactsParseReason.INVALID_TOP_LEVEL),
        (b'"scalar"', SecCompanyFactsParseReason.INVALID_TOP_LEVEL),
        (b"NaN", SecCompanyFactsParseReason.INVALID_NUMBER),
        (b"Infinity", SecCompanyFactsParseReason.INVALID_NUMBER),
        (b"-Infinity", SecCompanyFactsParseReason.INVALID_NUMBER),
    ],
)
def test_encoding_json_and_top_level_failures(
    body: bytes,
    reason: SecCompanyFactsParseReason,
) -> None:
    _assert_body_error(body, reason)


@pytest.mark.parametrize(
    "body",
    [
        (b'{"cik":789019,"cik":789019,"entityName":"ENTITY","facts":{}}'),
        (b'{"cik":789019,"entityName":"ENTITY","facts":{"us-gaap":{},"us-gaap":{}}}'),
        (
            b'{"cik":789019,"entityName":"ENTITY","facts":{"us-gaap":'
            b'{"Concept":{},"Concept":{}}}}'
        ),
        (
            b'{"cik":789019,"entityName":"ENTITY","facts":{"us-gaap":'
            b'{"Concept":{"label":"A","label":"B",'
            b'"description":"","units":{}}}}}'
        ),
        (
            b'{"cik":789019,"entityName":"ENTITY","facts":{"us-gaap":'
            b'{"Concept":{"label":"A","description":"","units":'
            b'{"USD":[],"USD":[]}}}}}'
        ),
        (
            b'{"cik":789019,"entityName":"ENTITY","facts":{"us-gaap":'
            b'{"Concept":{"label":"A","description":"","units":{"USD":'
            b'[{"val":1,"val":2,"accn":"A","form":"F",'
            b'"filed":"2024-01-01","end":"2023-12-31"}]}}}}}'
        ),
    ],
)
def test_duplicate_keys_at_every_modeled_level_fail_closed(body: bytes) -> None:
    _assert_body_error(
        body,
        SecCompanyFactsParseReason.DUPLICATE_JSON_KEY,
    )


@pytest.mark.parametrize("missing", ["cik", "entityName", "facts"])
def test_missing_top_level_fields(missing: str) -> None:
    document = _document()
    del document[missing]

    _assert_body_error(
        _body(document),
        SecCompanyFactsParseReason.MISSING_FIELD,
    )


def test_unexpected_top_level_field() -> None:
    _assert_body_error(
        _body(_document(extra="value")),
        SecCompanyFactsParseReason.UNEXPECTED_FIELD,
    )


@pytest.mark.parametrize("value", [True, "789019", 789019.0, None, [], {}])
def test_cik_wrong_types(value: object) -> None:
    _assert_body_error(
        _body(_document(cik=value)),
        SecCompanyFactsParseReason.INVALID_FIELD_TYPE,
    )


@pytest.mark.parametrize("value", [0, -1, 10_000_000_000])
def test_cik_invalid_integer_values(value: int) -> None:
    _assert_body_error(
        _body(_document(cik=value)),
        SecCompanyFactsParseReason.INVALID_FIELD_VALUE,
    )


@pytest.mark.parametrize("value", [1, True, None, [], {}])
def test_entity_name_wrong_types(value: object) -> None:
    _assert_body_error(
        _body(_document(entityName=value)),
        SecCompanyFactsParseReason.INVALID_FIELD_TYPE,
    )


@pytest.mark.parametrize(
    "value",
    ["", " ", " ENTITY", "ENTITY ", "ENTITY\nNAME", "ENTITY\x00NAME"],
)
def test_entity_name_invalid_values(value: str) -> None:
    _assert_body_error(
        _body(_document(entityName=value)),
        SecCompanyFactsParseReason.INVALID_FIELD_VALUE,
    )


@pytest.mark.parametrize("value", [None, [], "facts", 1, True])
def test_facts_requires_mapping(value: object) -> None:
    _assert_body_error(
        _body(_document(facts=value)),
        SecCompanyFactsParseReason.INVALID_FIELD_TYPE,
    )


@pytest.mark.parametrize(
    "taxonomy",
    ["", " ", " us-gaap", "us-gaap ", "us\n-gaap", "us\x00-gaap"],
)
def test_invalid_taxonomy_identifier(taxonomy: str) -> None:
    _assert_body_error(
        _body(_document(facts={taxonomy: {}})),
        SecCompanyFactsParseReason.INVALID_FIELD_VALUE,
    )


def test_taxonomy_value_requires_concept_mapping() -> None:
    _assert_body_error(
        _body(_document(facts={"us-gaap": []})),
        SecCompanyFactsParseReason.INVALID_FIELD_TYPE,
    )


@pytest.mark.parametrize(
    "concept_name",
    ["", " ", " Revenues", "Revenues ", "Reve\nnues", "Reve\x00nues"],
)
def test_invalid_concept_identifier(concept_name: str) -> None:
    _assert_body_error(
        _body(_document(facts={"us-gaap": {concept_name: _concept()}})),
        SecCompanyFactsParseReason.INVALID_FIELD_VALUE,
    )


def test_concept_definition_requires_mapping() -> None:
    _assert_body_error(
        _body(_document(facts={"us-gaap": {"Revenues": []}})),
        SecCompanyFactsParseReason.INVALID_FIELD_TYPE,
    )


@pytest.mark.parametrize("missing", ["label", "description", "units"])
def test_missing_concept_fields(missing: str) -> None:
    concept = _concept()
    del concept[missing]

    _assert_body_error(
        _body(_document(facts={"us-gaap": {"Revenues": concept}})),
        SecCompanyFactsParseReason.MISSING_FIELD,
    )


def test_unexpected_concept_field() -> None:
    _assert_body_error(
        _body(
            _document(
                facts={"us-gaap": {"Revenues": _concept(providerExtension="value")}}
            )
        ),
        SecCompanyFactsParseReason.UNEXPECTED_FIELD,
    )


@pytest.mark.parametrize("value", [1, True, None, [], {}])
def test_label_wrong_types(value: object) -> None:
    _assert_body_error(
        _body(_document(facts={"us-gaap": {"Revenues": _concept(label=value)}})),
        SecCompanyFactsParseReason.INVALID_FIELD_TYPE,
    )


@pytest.mark.parametrize("value", ["", " ", " Label", "Label ", "Bad\nLabel"])
def test_label_invalid_values(value: str) -> None:
    _assert_body_error(
        _body(_document(facts={"us-gaap": {"Revenues": _concept(label=value)}})),
        SecCompanyFactsParseReason.INVALID_FIELD_VALUE,
    )


@pytest.mark.parametrize("value", [1, True, None, [], {}])
def test_description_wrong_types(value: object) -> None:
    _assert_body_error(
        _body(_document(facts={"us-gaap": {"Revenues": _concept(description=value)}})),
        SecCompanyFactsParseReason.INVALID_FIELD_TYPE,
    )


def test_description_preserves_whitespace_but_rejects_controls() -> None:
    preserved = " Provider description with surrounding spaces "
    document = _parse(
        _document(facts={"us-gaap": {"Revenues": _concept(description=preserved)}})
    )
    assert document.facts["us-gaap"]["Revenues"].description == preserved

    _assert_body_error(
        _body(
            _document(
                facts={
                    "us-gaap": {"Revenues": _concept(description="Bad\nDescription")}
                }
            )
        ),
        SecCompanyFactsParseReason.INVALID_FIELD_VALUE,
    )


@pytest.mark.parametrize("value", [None, [], "units", 1, True])
def test_units_requires_mapping(value: object) -> None:
    _assert_body_error(
        _body(_document(facts={"us-gaap": {"Revenues": _concept(units=value)}})),
        SecCompanyFactsParseReason.INVALID_FIELD_TYPE,
    )


@pytest.mark.parametrize(
    "unit",
    ["", " ", " USD", "USD ", "US\nD", "US\x00D"],
)
def test_invalid_unit_identifier(unit: str) -> None:
    _assert_body_error(
        _body(_document(facts={"us-gaap": {"Revenues": _concept(units={unit: []})}})),
        SecCompanyFactsParseReason.INVALID_FIELD_VALUE,
    )


def test_unit_observations_require_array() -> None:
    _assert_body_error(
        _body(_document(facts={"us-gaap": {"Revenues": _concept(units={"USD": {}})}})),
        SecCompanyFactsParseReason.INVALID_FIELD_TYPE,
    )


def test_observation_requires_object() -> None:
    _assert_body_error(
        _body(_document(facts={"us-gaap": {"Revenues": _concept(units={"USD": [1]})}})),
        SecCompanyFactsParseReason.INVALID_FIELD_TYPE,
    )


@pytest.mark.parametrize("missing", ["val", "accn", "form", "filed", "end"])
def test_missing_required_observation_fields(missing: str) -> None:
    observation = _observation()
    del observation[missing]

    _assert_body_error(
        _body(
            _document(
                facts={"us-gaap": {"Revenues": _concept(units={"USD": [observation]})}}
            )
        ),
        SecCompanyFactsParseReason.MISSING_FIELD,
    )


def test_unexpected_observation_field() -> None:
    _assert_body_error(
        _body(
            _document(
                facts={
                    "us-gaap": {
                        "Revenues": _concept(
                            units={"USD": [_observation(providerExtension="value")]}
                        )
                    }
                }
            )
        ),
        SecCompanyFactsParseReason.UNEXPECTED_FIELD,
    )


@pytest.mark.parametrize("value", [True, "1", None, {}, []])
def test_invalid_numeric_values(value: object) -> None:
    _assert_body_error(
        _body(
            _document(
                facts={
                    "us-gaap": {
                        "Revenues": _concept(units={"USD": [_observation(val=value)]})
                    }
                }
            )
        ),
        SecCompanyFactsParseReason.INVALID_NUMBER,
    )


@pytest.mark.parametrize(
    "constant",
    ["NaN", "Infinity", "-Infinity", "1e9999999999999999999"],
)
def test_unsupported_observation_numbers(constant: str) -> None:
    body = (
        b'{"cik":789019,"entityName":"ENTITY","facts":{"us-gaap":'
        b'{"Concept":{"label":"Label","description":"","units":{"USD":'
        b'[{"val":'
        + constant.encode()
        + b',"accn":"A","form":"FORM","filed":"2024-01-01",'
        b'"end":"2023-12-31"}]}}}}}'
    )
    _assert_body_error(body, SecCompanyFactsParseReason.INVALID_NUMBER)


@pytest.mark.parametrize("field", ["accn", "form"])
@pytest.mark.parametrize("value", [1, True, None, [], {}])
def test_required_observation_string_wrong_types(
    field: str,
    value: object,
) -> None:
    _assert_observation_error(
        _observation(**{field: value}),
        SecCompanyFactsParseReason.INVALID_FIELD_TYPE,
    )


@pytest.mark.parametrize("field", ["accn", "form"])
@pytest.mark.parametrize("value", ["", " ", " VALUE", "VALUE ", "BAD\nVALUE"])
def test_required_observation_string_invalid_values(
    field: str,
    value: str,
) -> None:
    _assert_observation_error(
        _observation(**{field: value}),
        SecCompanyFactsParseReason.INVALID_FIELD_VALUE,
    )


@pytest.mark.parametrize("value", [True, "2024", 2024.0, None, [], {}])
def test_optional_fiscal_year_wrong_types(value: object) -> None:
    _assert_observation_error(
        _observation(fy=value),
        SecCompanyFactsParseReason.INVALID_FIELD_TYPE,
    )


@pytest.mark.parametrize("field", ["fp", "frame"])
@pytest.mark.parametrize("value", [1, True, None, [], {}])
def test_optional_string_wrong_types(field: str, value: object) -> None:
    _assert_observation_error(
        _observation(**{field: value}),
        SecCompanyFactsParseReason.INVALID_FIELD_TYPE,
    )


@pytest.mark.parametrize("field", ["fp", "frame"])
@pytest.mark.parametrize("value", ["", " ", " VALUE", "VALUE ", "BAD\nVALUE"])
def test_optional_string_invalid_values(field: str, value: str) -> None:
    _assert_observation_error(
        _observation(**{field: value}),
        SecCompanyFactsParseReason.INVALID_FIELD_VALUE,
    )


@pytest.mark.parametrize("field", ["filed", "end", "start"])
@pytest.mark.parametrize(
    "value",
    [
        "2024-02-30",
        "2024-01-01T00:00:00",
        "2024-01",
        " 2024-01-01",
        "2024-01-01 ",
        20240101,
        None,
    ],
)
def test_invalid_observation_dates(field: str, value: object) -> None:
    _assert_observation_error(
        _observation(**{field: value}),
        SecCompanyFactsParseReason.INVALID_DATE,
    )


def test_period_semantics_are_not_inferred_or_rejected() -> None:
    observation = _observation(
        start="2025-01-01",
        end="2024-01-01",
        fy=-500,
        fp="NONSTANDARD",
        form="OTHER",
        frame="CUSTOM",
    )

    parsed = _parse_observation_document(observation)

    assert parsed.start == date(2025, 1, 1)
    assert parsed.end == date(2024, 1, 1)
    assert parsed.fy == -500
    assert parsed.fp == "NONSTANDARD"
    assert parsed.form == "OTHER"
    assert parsed.frame == "CUSTOM"


def test_safe_error_excludes_raw_body_fragments_and_has_stable_reason() -> None:
    marker = "RAW_PROVIDER_MARKER_3C4D"
    error = _assert_body_error(
        f'{{"{marker}":'.encode(),
        SecCompanyFactsParseReason.INVALID_JSON,
    )

    _assert_safe_error(error, marker)
    assert error.args == ("SEC Company Facts document is invalid.",)
    assert not hasattr(error, "artifact")
    assert not hasattr(error, "body")
    assert not hasattr(error, "url")
    assert not hasattr(error, "headers")


def test_contract_representations_exclude_provider_controlled_markers() -> None:
    marker = "PROVIDER_REPR_MARKER_4D5E"
    document = _parse(
        _document(
            entityName=marker,
            facts={
                marker: {
                    marker: _concept(
                        label=marker,
                        description=marker,
                        units={
                            marker: [
                                _observation(
                                    accn=marker,
                                    form=marker,
                                    fp=marker,
                                    frame=marker,
                                )
                            ]
                        },
                    )
                }
            },
        )
    )

    assert marker not in repr(document)
    assert marker not in repr(document.facts[marker][marker])
    assert marker not in repr(document.facts[marker][marker].units[marker][0])


def test_public_exports_are_sec_specific_and_helpers_are_private() -> None:
    expected = {
        "SecCompanyFacts": SecCompanyFacts,
        "SecCompanyFactConcept": SecCompanyFactConcept,
        "SecCompanyFactObservation": SecCompanyFactObservation,
        "SecCompanyFactsParseError": SecCompanyFactsParseError,
        "SecCompanyFactsParseReason": SecCompanyFactsParseReason,
        "parse_company_facts": parse_company_facts,
    }
    for name, value in expected.items():
        assert getattr(sec_providers, name) is value
        assert name in sec_providers.__all__
        assert name not in generic_providers.__all__
        assert not hasattr(generic_providers, name)

    for name in (
        "_decode_json",
        "_object_from_pairs",
        "_parse_observation",
        "_validate_exact_fields",
    ):
        assert name not in sec_providers.__all__
        assert not hasattr(sec_providers, name)
        assert hasattr(parser_module, name)


def _assert_observation_error(
    observation: dict[str, object],
    reason: SecCompanyFactsParseReason,
) -> None:
    _assert_body_error(
        _body(
            _document(
                facts={"us-gaap": {"Revenues": _concept(units={"USD": [observation]})}}
            )
        ),
        reason,
    )


def _parse_observation_document(
    observation: dict[str, object],
) -> SecCompanyFactObservation:
    document = _parse(
        _document(
            facts={"us-gaap": {"Revenues": _concept(units={"USD": [observation]})}}
        )
    )
    return document.facts["us-gaap"]["Revenues"].units["USD"][0]


def _assert_safe_error(
    error: SecCompanyFactsParseError,
    marker: str,
) -> None:
    assert marker not in str(error)
    assert marker not in repr(error)
