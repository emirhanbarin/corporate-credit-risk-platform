# Data Contracts

## 1. Purpose and scope

This document defines semantic contracts and invariants between platform data stages. They make transformations reviewable, reproducible, traceable, and technology-independent.

They cover provider evidence, validated records, normalized facts, selection outcomes, metric inputs, and metric results for live retrieval and offline fixtures.

This document governs data-stage contracts and invariants. It does not define:

- Python types, class names, or implementation details;
- database tables, files, or serialized formats;
- API requests, responses, or endpoints;
- financial formulas, source-tag mappings, or selection algorithms;
- risk thresholds, weights, or models; or
- user-interface behavior.

Product scope, architecture, financial semantics, sequence, and bounded execution remain owned by their authoritative documents. Nothing here claims implementation.

## 2. Contract design principles

- **Explicit semantics:** Every field and status must have one documented meaning appropriate to its stage.
- **Provenance preservation:** A transformation must retain enough lineage to reconstruct inputs and decisions.
- **Immutable source evidence:** Original and preserved evidence must not be rewritten to make processing succeed.
- **Deterministic transformations:** The same evidence, versions, and cutoff must produce the same outcome.
- **Missing is not zero:** Absence, unavailability, invalidity, and inapplicability must not be numeric zero.
- **Validation before normalization:** Unsafe provider records must not enter normalization as accepted facts.
- **No silent coercion:** Types, dates, units, currencies, scales, periods, scopes, and concepts must not be guessed.
- **Forward-compatible evolution:** Additions should preserve meaning; incompatible changes require versioning.
- **Provider isolation:** Provider details should remain outside provider-independent contracts where practical.

No stage may conceal, reinterpret, or silently repair an earlier-stage failure.

## 3. Data-stage overview

The conceptual evidence-to-result sequence is:

```text
Original provider payload
  -> Locally preserved raw response
  -> Sanitized committed fixture
  -> Validated provider record
  -> Fact-selection outcome
  -> Normalized financial fact
  -> Metric input set
  -> Metric result
```

The sequence names distinct forms; not every runtime path must materialize each one. Live retrieval should preserve a raw response before transformation. Offline processing may validate a faithful sanitized fixture.

The sanitized fixture is a reviewed test artifact, not the canonical original or a substitute for preserved live evidence. It must not be represented as the original response.

## 4. Original provider payload

The original provider payload is received before project transformation. It must be byte-for-byte original when transport bytes matter; otherwise it must preserve provider semantics without normalization or correction.

Its retrieval context must identify, as applicable:

- provider and source location or resource identity;
- request target and non-secret request parameters;
- response status and content characteristics;
- retrieval timestamp; and
- provider identification context without retaining secrets or private details.

The payload should be captured before parsing changes its form. It must be immutable evidence; editing, reformatting, value repair, or record removal is prohibited.

Original payloads must not be committed merely because they were retrieved. Secrets, personal details, private data, and unreviewed large responses must not enter version control.

## 5. Locally preserved raw response

A locally preserved raw response is an immutable copy of the original payload. A retrieval, content, integrity, and safe-identity metadata wrapper must not alter the evidence.

Provenance should identify provider, resource, retrieval timestamp, and relationship to the original. Response status, media type, encoding, and integrity digest should be retained when available.

Local preservation supports auditability, repeatable investigation, and separation from
processed data. It is not an analytical record and must not be edited to satisfy tests.

A preserved response differs from a fixture and is not assumed reduced, anonymized, Git-reviewed, or stable test input. Preservation must prevent overwrite or undetected mutation where practical.

## 6. Sanitized committed fixture

A sanitized committed fixture supports deterministic offline tests. It is a reviewed representation of provider evidence and must never be labeled the canonical original.

Sanitization may remove unrelated records, secrets, private contact details, unstable
transport metadata, or unnecessary volume. It may anonymize personal identification details.

Sanitization must preserve values, relationships, ordering, duplicates, conflicts, amendments, periods, units, and other material details. Values must not be edited merely to pass tests.

Fixture provenance must record or reference:

- provider and source resource;
- source company and retrieval context;
- retrieval date or timestamp when safely retainable;
- the relationship to the source evidence;
- what was removed, reduced, redacted, or anonymized; and
- which behavior the fixture is intended to preserve.

Sanitization notes must prevent the fixture from being mistaken for complete evidence.

## 7. Validated provider record

A validated provider record represents one source fact after shape, presence, and consistency checks. Validation does not approve a normalized concept, select candidates, or establish metric eligibility.

The record must retain these semantics when applicable:

- provider identifier;
- provider company identifier;
- source concept;
- reported value;
- original unit;
- currency for monetary facts;
- period start and period end for duration facts;
- instant date for point-in-time facts;
- fiscal year and fiscal period;
- filing form and filing date;
- accession number when available;
- amendment or restatement indicators when available;
- retrieval timestamp; and
- original source tag.

Absent conditional fields must differ from valid empty values. Provider meanings must remain visible. Malformed, inconsistent, or unsupported records require explicit failure.

## 8. Normalized financial fact

A normalized financial fact is a provider-independent fact mapped to one controlled concept. It is a reported fact, not a calculation, estimate, adjustment, or reconstructed value.

It must include or reference:

- stable company identifier;
- normalized concept identifier;
- reported value;
- normalized unit representation and original unit lineage;
- currency where applicable;
- period type: duration or point in time;
- applicable period boundaries or instant date;
- fiscal context;
- source provenance;
- selection status and rationale reference; and
- data-quality status.

Normalization may standardize identifiers and scale, but must not change meaning, substitute a concept, change scope, translate currency, shift dates, or construct a total without approved methodology.

## 9. Phase 1 annual fact-selection contracts

These logical contracts carry the Microsoft policy defined in
[`financial-methodology.md`, section 16](financial-methodology.md#16-phase-1-microsoft-annual-fact-selection-policy).
They establish semantics and invariants only. They do not define Python names,
serialized field names, persistence, APIs, or an implemented selector.

### 9.1 Annual fact-selection request

One request addresses one normalized concept and one Microsoft fiscal year. It
must include or reference:

- stable Microsoft analytical identifier `microsoft_corporation` and canonical
  SEC CIK `0000789019`;
- one normalized concept identifier: `revenue`, `current_assets`,
  `current_liabilities`, `operating_income`, or `interest_expense`;
- target fiscal year;
- exact target fiscal-year start for Revenue, Operating Income, and Interest
  Expense, and no applicable start for Current Assets or Current Liabilities;
- exact target fiscal-year end;
- a date-only analysis cutoff; and
- methodology version `microsoft_annual_company_facts_v1`.

The request must be self-consistent with the concept's duration or instant period
type. The canonical CIK is the exact provider-identity boundary, while
`microsoft_corporation` preserves the platform analytical identity. This narrow
identifier does not define a general company-identifier format or registry.

### 9.2 Candidate evaluation

One candidate occurrence represents one preserved SEC Company Facts observation
and its originating raw artifact. Exact duplicate occurrences form one evaluated
candidate-fact identity without losing occurrence-level evidence. An evaluated
candidate must include or reference:

- its request;
- taxonomy and exact provider concept identifier;
- every underlying occurrence and raw observation fields `val`, `accn`, `form`,
  `filed`, `end`, and optional `fy`, `fp`, `frame`, and `start`, preserving field
  absence;
- the exact provider unit key;
- one candidate disposition: `eligible`, `rejected`, `unresolved`, or `invalid`;
- every applicable stable reason code and one primary reason when not eligible;
- source-tag priority and same-tag ranking tier;
- every eligibility-check result, including checks that did not determine the
  primary rejection;
- amendment, later-period, and restatement classification; and
- the originating `SecRawArtifact` provenance reference.

`eligible` means the candidate passes every ordinary rule; eligible candidates
may still participate in a final Ambiguous or Conflicting outcome. `rejected`
means a documented filter, lower tag, or value-agreeing non-controlling amendment
deterministically excludes the candidate without making it uninterpretable.
`unresolved` is reserved for amendment or restatement evidence whose controlling
treatment cannot be established. `invalid` means the target-relevant evidence
cannot be interpreted consistently.

Candidate rank is not response position. Its only concept preference is the
integer source-tag priority defined by the methodology, applied after all
observations in that tag tier are resolved. Within a tag tier, eligibility,
equivalence, amendment/restatement treatment, value agreement, and uniqueness
determine disposition; filing recency, accession sorting, retrieval time,
`frame`, and JSON order are not rank fields.

The exact Phase 1 selection reason-code set, used across request validation,
candidate evaluation, and the final outcome, is:

```text
company_mismatch
invalid_request_context
invalid_candidate_evidence
concept_unsupported
methodology_version_unsupported
no_approved_tag_present
unsupported_unit
ineligible_filing_form
filed_after_cutoff
fiscal_year_mismatch
fiscal_period_mismatch
duration_mismatch
instant_date_mismatch
amendment_unresolved
restatement_unresolved
no_eligible_candidate
unique_eligible_candidate
equivalent_duplicates
multiple_equal_candidates
conflicting_values
lower_priority_tag
```

The owning meanings and outcome effects are defined in
[`financial-methodology.md`, section 16.11](financial-methodology.md#1611-selection-statuses-and-reason-codes).
Display wording must not redefine these identifiers.

### 9.3 Selection outcome

Fact selection produces one structured outcome rather than an unexplained value
or absence. Its controlled status is exactly one of:

- **Selected** (`selected`): one eligible candidate or one resolved group of
  equivalent candidates represents exactly one selected economic fact.
- **Unavailable** (`unavailable`): supported filtering leaves no eligible
  candidate and no blocking unresolved or invalid evidence.
- **Ambiguous** (`ambiguous`): equally ranked, same-value candidates cannot be
  proven equivalent or reduced to one controlling candidate.
- **Conflicting** (`conflicting`): equally ranked ordinary eligible candidates
  have unequal values.
- **Unsupported** (`unsupported`): the requested concept, version, unit, or
  required treatment is outside the policy, including unresolved amendment or
  restatement treatment.
- **Invalid** (`invalid`): the request, company evidence, or target-relevant
  candidate violates a validity invariant.

Every outcome must include or reference:

- the complete request;
- controlled status, primary reason code, and all material contributing reasons;
- the selected candidate or resolved group of equivalent candidates, and the
  selected source tag, only when Selected;
- all evaluated candidate facts and all candidate occurrences, including exact
  duplicates and observations rejected by cutoff;
- all rejected alternatives and their eligibility results and reasons;
- the unresolved candidate set when applicable;
- deterministic selection rationale and source-tag priority treatment;
- equivalent-evidence lineage when applicable;
- amendment and restatement treatment; and
- provenance through every candidate to the originating raw artifact.

### 9.4 Selection invariants

- Selected contains exactly one selected economic fact represented by one
  eligible candidate or one resolved group of equivalent candidates. Every group
  member must be eligible, be in the evaluated set, and use the selected source
  tag.
- Equivalent duplicates may support Selected only when they collapse under the
  methodology. Exact duplicates form one candidate-fact identity; other approved
  equivalents form one selected candidate group. Every occurrence, filing
  identity, eligibility decision, and raw-artifact reference is retained.
- A value-agreeing `10-K/A` is not a selected-group member. It remains a Rejected
  candidate associated as supporting amendment evidence with reason
  `equivalent_duplicates`; the ordinary `10-K` candidate controls.
- A non-Selected outcome has no selected candidate or candidate group, selected
  source tag, or fabricated selected value.
- Every outcome retains all evaluated evidence, including rejected alternatives
  and unresolved candidates. A selected value must not sever rejected or
  contradictory lineage.
- The inclusive rule
  `observation.filed <= analysis_cutoff` is applied before candidate selection.
  Retrieval time is never substituted for filing date.
- Provider response order, JSON position, retrieval order, and `frame` are never
  part of ranking.
- A lower-priority tag is considered only after the higher tier is resolved.
  Invalid, unsupported, ambiguous, conflicting, amendment-unresolved, or
  restatement-unresolved target evidence at a higher tier blocks fallback.
- Unresolved conflicts remain explicit. They are never resolved by latest filing,
  latest retrieval, accession order, averaging, extrema, or value size.
- Original and amended or later-period accessions, forms, filed dates, values,
  and treatment remain in provenance.
- Candidate and final primary reason codes follow the deterministic precedence in
  the methodology; all other applicable reasons remain contributing reasons.
- Selection performs no currency conversion, reconstruction, metric calculation,
  persistence, or presentation reinterpretation.

## 10. Metric input set

A metric input set is the evaluated collection of normalized facts offered to one metric
for one company and target period. It records usable, blocking, and limiting outcomes.

It must include or reference:

- stable metric identifier;
- required normalized concept identifiers;
- stable company identifier;
- target reporting period;
- source periods for each input;
- compatibility status across company, scope, period, unit, and currency;
- completeness status; and
- provenance references for every supplied fact and selection outcome.

Input assembly must not substitute a period or concept. The set must remain inspectable
even when calculation is blocked.

## 11. Metric result

A metric result is the outcome of applying one approved methodology to one evaluated input
set. It must include or reference:

- metric identifier;
- numeric value when available;
- result status;
- stable company identifier;
- reporting period;
- metric input and normalized-fact references;
- formula or methodology version reference;
- data-quality and completeness status;
- reason codes for exceptional or limited outcomes;
- bounded interpretation; and
- end-to-end provenance.

A result may contain a value only when inputs and methodology permit calculation.
Unavailable, invalid, unsupported, conflicting, or not applicable results must not
fabricate one. Zero is valid only when valid inputs genuinely produce zero.

## 12. Data-quality statuses

The controlled data-quality vocabulary is:

- **Complete:** all required eligible data and lineage are present, compatible, and sufficient.
- **Partial:** useful supported data exists, but non-blocking context is absent and disclosed.
- **Missing:** a required or expected fact is absent from eligible evidence.
- **Invalid:** present data violates an applicable validity or consistency rule.
- **Unsupported:** available data or required treatment is outside approved scope or methodology.
- **Conflicting:** eligible evidence disagrees and the approved policy cannot resolve it.
- **Not applicable:** the concept or metric does not apply under approved methodology.

Fact-level status describes one source or normalized fact. Selection-level status
uses exactly `selected`, `unavailable`, `ambiguous`, `conflicting`, `unsupported`,
or `invalid` under section 9. Metric-level status describes calculation and
input-set fitness. These levels must not be collapsed merely because labels
overlap.

## 13. Provenance contract

Minimum lineage must permit traversal in both directions through:

```text
Metric result
  -> metric input set
  -> normalized financial fact
  -> fact-selection outcome
  -> validated provider record
  -> locally preserved raw response or documented fixture evidence
  -> original provider source
```

Lineage must identify the company, concepts, source tags, filings, periods, currency, units,
retrieval, selection, methodology version, and cutoff. References must be stable within the
contract version and must not rely only on display labels or logs.

Fixture provenance must disclose sanitization and must not imply an unmodified committed
original. Live provenance must keep source, retrieval, and preserved response auditable.

## 14. Identifier policy

- **Stable company identifiers** must identify the same legal analytical entity over time.
- **Ticker symbols** are descriptive, time-varying, and must not be the permanent identity.
- **Provider identifiers** must be paired with their provider to prevent collisions.
- **Normalized concept identifiers** must be stable and provider-independent.
- **Metric identifiers** must be stable and not reused for a materially different calculation.
- **Reason codes** must be stable semantic identifiers; display text must not change meaning.
- **Methodology versions** must identify the exact approved selection and calculation rules.

Global identifier formats and registry mechanics remain deferred. The Phase 1
selection request nevertheless must use stable analytical identifier
`microsoft_corporation` and exact canonical SEC CIK `0000789019`; that narrow
requirement does not establish a reusable registry.

## 15. Time semantics

- **Retrieval timestamp:** when the platform received the provider response.
- **Filing date:** when the filing became filed or available under approved source semantics.
- **Reporting-period start/end:** the duration covered by a flow fact.
- **Instant date:** the date represented by a point-in-time fact.
- **Analysis cutoff:** the latest filing date permitted for an analysis.
- **Publication or calculation timestamp:** when the platform produced or published a result.

These times are not interchangeable. Retrieval does not redefine filing or
reporting dates; calculation does not alter the cutoff; and later retrieval must
not introduce filings unavailable at a historical cutoff. For
`microsoft_annual_company_facts_v1`, the cutoff is date-only and inclusive:
`observation.filed <= analysis_cutoff`. Other future policies must define their
own date or timestamp semantics explicitly.

## 16. Currency and unit semantics

Every fact must preserve its original unit, currency where applicable, and scale. A
normalized representation may clarify dimension and scale but must retain the original and
the transformation in provenance.

Inputs may be combined only when currency, dimension, scale, and scope are compatible.
Scaling may change representation, not economic value, and must be deterministic and
reversible or exactly explainable.

Phase 1 does not support currency conversion. No stage may translate currency, assume one,
or equate different currencies silently. Unapproved conversion is unsupported or invalid.

For `microsoft_annual_company_facts_v1`, the only eligible provider unit key is
exact, case-sensitive `USD` for all five concepts. Unit aliases and other
dimensions are not normalized into eligibility.

## 17. Contract evolution

Backward-compatible additions may introduce optional semantics or controlled values only
when consumers preserve prior meaning and unknown values fail safely. Required fields,
identifier reassignment, meaning changes, status reinterpretation, lineage loss, or an
incompatible serialized representation are breaking changes.

Breaking changes require approval, a new contract version, impact analysis, and a migration
or compatibility plan. Deprecation must identify the replacement, consumers, support window,
and removal condition; deprecated meanings must not be repurposed.

Contracts, methodology, architecture, data dictionary, tests, and consumer documentation
must remain synchronized. Durable technical or architecture changes require an ADR.

Exact version storage, negotiation, and migration mechanics remain deferred.

## 18. Validation expectations

Semantic validation must be deterministic and stage-appropriate. It must evaluate:

- presence of required fields and explicit treatment of conditional fields;
- primitive value readability without lossy coercion;
- internal agreement among period type, dates, and fiscal context;
- company, filing, accession, amendment, and restatement consistency;
- currency, unit dimension, and scale compatibility;
- provenance completeness and resolvable lineage;
- supported concept, source, form, period, and scope boundaries; and
- explicit outcomes for malformed, missing, invalid, ambiguous, conflicting, and unsupported data.

Fixtures must produce deterministic offline outcomes and preserve claimed cases. Validation
success satisfies the contract; it does not prove accounting truth or metric eligibility.

## 19. Phase 1 boundaries

Phase 1 contract scope is limited to:

- Microsoft Corporation under stable identifier `microsoft_corporation` and
  canonical SEC CIK `0000789019`;
- annual SEC Company Facts and ordinary `10-K` context, with `10-K/A` considered
  only under the documented conservative amendment rule;
- five concepts: Revenue, Current Assets, Current Liabilities, Operating Income, and Interest Expense;
- methodology version `microsoft_annual_company_facts_v1`;
- three metric results: Revenue Growth, Current Ratio, and Interest Coverage;
- reviewed sanitized fixtures for deterministic offline processing by default; and
- optional, isolated live SEC retrieval with local raw-response preservation.

Phase 1 does not support other companies, generalized selection, quarterly or
trailing-twelve-month facts, currency conversion, estimates, other jurisdictions or
standards, production persistence, APIs, dashboards, peers, macro data, risk models, stress
scenarios, bulk ingestion, machine learning, or Power BI.

These are contract constraints, not claims of implementation. `ROADMAP.md` governs status.

## 20. Known limitations and deferred decisions

The following remain unresolved and require approval by the document owner:

- exact serialized formats and field encodings;
- reason-code vocabularies and result-status mappings outside the Phase 1
  Microsoft selection contract;
- exact serialized representations of candidate and selection metadata;
- stable company-identifier formats and registry mechanics outside the approved
  `microsoft_corporation` identifier;
- persistence schemas, retention, and migrations;
- API serialization and compatibility behavior;
- contract-version storage and negotiation mechanics;
- raw-response integrity and storage formats; and
- cross-company generalization and reconciliation policy.

Implementation must not invent these decisions. Applicable roadmap, methodology, plan,
architecture, or data-dictionary work must approve them first.

## 21. Related documents

- [`../AGENTS.md`](../AGENTS.md) — behavior, priorities, ownership, and precedence.
- [`product-requirements.md`](product-requirements.md) — scope, acceptance, and quality outcomes.
- [`architecture.md`](architecture.md) and [`adr/`](adr/) — boundaries and durable decisions.
- [`financial-methodology.md`](financial-methodology.md) — financial concepts and methodology.
- [`data-dictionary.md`](data-dictionary.md) — detailed field meanings when approved.
- [`risk-model.md`](risk-model.md) — future risk semantics when approved.
- [`../ROADMAP.md`](../ROADMAP.md) — sequence, dependencies, status, and progress.
- [`../PLANS.md`](../PLANS.md) — requirements for one bounded execution plan.

When documents overlap, the ownership and precedence rules in `AGENTS.md` apply.
