"""Tests for immutable SEC Company Facts provider contracts."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from credit_risk_platform.providers.sec import (
    SecCik,
    SecCompanyFactConcept,
    SecCompanyFactObservation,
    SecCompanyFacts,
    SecRawArtifact,
    SecSource,
)


def _artifact() -> SecRawArtifact:
    return SecRawArtifact(
        source=SecSource.COMPANY_FACTS,
        retrieved_at=datetime(2026, 7, 25, tzinfo=timezone.utc),
        body=b'{"synthetic":true}',
    )


def _observation() -> SecCompanyFactObservation:
    return SecCompanyFactObservation(
        val=Decimal("245122000000"),
        accn="0000000000-24-000001",
        fy=2024,
        fp="FY",
        form="10-K",
        filed=date(2024, 7, 30),
        frame="CY2023",
        start=date(2023, 7, 1),
        end=date(2024, 6, 30),
    )


def test_observation_preserves_typed_provider_fields() -> None:
    observation = _observation()

    assert observation.val == Decimal("245122000000")
    assert observation.accn == "0000000000-24-000001"
    assert observation.fy == 2024
    assert observation.fp == "FY"
    assert observation.form == "10-K"
    assert observation.filed == date(2024, 7, 30)
    assert observation.frame == "CY2023"
    assert observation.start == date(2023, 7, 1)
    assert observation.end == date(2024, 6, 30)


def test_observation_is_frozen_slotted_and_repr_safe() -> None:
    observation = _observation()

    assert not hasattr(observation, "__dict__")
    assert repr(observation) == "SecCompanyFactObservation()"
    with pytest.raises(FrozenInstanceError):
        observation.val = Decimal("0")  # type: ignore[misc]


def test_concept_defensively_freezes_units_and_observation_sequences() -> None:
    observation = _observation()
    source_observations = [observation]
    source_units = {"USD": source_observations}

    concept = SecCompanyFactConcept(
        label="Revenues",
        description="Synthetic description",
        units=source_units,  # type: ignore[arg-type]
    )
    source_observations.clear()
    source_units["shares"] = []

    assert concept.units == {"USD": (observation,)}
    assert isinstance(concept.units["USD"], tuple)
    with pytest.raises(TypeError):
        concept.units["USD"] = ()  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        concept.label = "Changed"  # type: ignore[misc]
    assert not hasattr(concept, "__dict__")
    assert repr(concept) == "SecCompanyFactConcept()"


def test_document_defensively_freezes_both_fact_mapping_dimensions() -> None:
    concept = SecCompanyFactConcept(
        label="Revenues",
        description="",
        units={"USD": (_observation(),)},
    )
    source_concepts = {"Revenues": concept}
    source_facts = {"us-gaap": source_concepts}
    provenance = _artifact()

    document = SecCompanyFacts(
        cik=SecCik(789019),
        entity_name="MICROSOFT CORPORATION",
        facts=source_facts,
        provenance=provenance,
    )
    source_concepts.clear()
    source_facts["dei"] = {}

    assert document.facts == {"us-gaap": {"Revenues": concept}}
    assert document.provenance is provenance
    with pytest.raises(TypeError):
        document.facts["dei"] = {}  # type: ignore[index]
    with pytest.raises(TypeError):
        document.facts["us-gaap"]["Assets"] = concept  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        document.entity_name = "Changed"  # type: ignore[misc]
    assert not hasattr(document, "__dict__")


def test_document_repr_excludes_provider_text_nested_facts_and_raw_provenance() -> None:
    marker = "PROVIDER_TEXT_MARKER_1A2B"
    document = SecCompanyFacts(
        cik=SecCik(789019),
        entity_name=marker,
        facts={
            "taxonomy-marker": {
                "concept-marker": SecCompanyFactConcept(
                    label=marker,
                    description=marker,
                    units={},
                )
            }
        },
        provenance=SecRawArtifact(
            source=SecSource.COMPANY_FACTS,
            retrieved_at=datetime(2026, 7, 25, tzinfo=timezone.utc),
            body=marker.encode(),
        ),
    )

    representation = repr(document)
    assert representation == "SecCompanyFacts(cik=SecCik(value='0000789019'))"
    assert marker not in representation
    assert "taxonomy-marker" not in representation
    assert "concept-marker" not in representation
