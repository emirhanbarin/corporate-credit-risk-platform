"""Immutable provider-specific contracts for validated SEC Company Facts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from types import MappingProxyType

from credit_risk_platform.providers.sec.raw_artifact import SecRawArtifact
from credit_risk_platform.providers.sec.ticker_mapping import SecCik


@dataclass(frozen=True, slots=True)
class SecCompanyFactObservation:
    """One structurally validated raw SEC Company Facts observation."""

    val: Decimal = field(repr=False)
    accn: str = field(repr=False)
    form: str = field(repr=False)
    filed: date = field(repr=False)
    end: date = field(repr=False)
    fy: int | None = field(default=None, repr=False)
    fp: str | None = field(default=None, repr=False)
    frame: str | None = field(default=None, repr=False)
    start: date | None = field(default=None, repr=False)


@dataclass(frozen=True, slots=True)
class SecCompanyFactConcept:
    """One provider taxonomy concept and its immutable unit observations."""

    label: str = field(repr=False)
    description: str = field(repr=False)
    units: Mapping[str, tuple[SecCompanyFactObservation, ...]] = field(repr=False)

    def __post_init__(self) -> None:
        copied = {
            unit: tuple(observations) for unit, observations in self.units.items()
        }
        object.__setattr__(self, "units", MappingProxyType(copied))


@dataclass(frozen=True, slots=True)
class SecCompanyFacts:
    """One validated SEC Company Facts document with exact raw provenance."""

    cik: SecCik
    entity_name: str = field(repr=False)
    facts: Mapping[str, Mapping[str, SecCompanyFactConcept]] = field(repr=False)
    provenance: SecRawArtifact = field(repr=False)

    def __post_init__(self) -> None:
        copied = {
            taxonomy: MappingProxyType(dict(concepts))
            for taxonomy, concepts in self.facts.items()
        }
        object.__setattr__(self, "facts", MappingProxyType(copied))
