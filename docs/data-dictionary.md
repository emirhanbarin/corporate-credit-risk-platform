# Data Dictionary

## 1. Purpose and scope

This document is the authoritative business and semantic dictionary for controlled terms used by the Corporate Credit Risk & Financial Health Platform. A shared vocabulary is required so source evidence, financial facts, validation outcomes, and analytical results retain the same meaning across stages and future interfaces.

It defines field meanings, identifiers, statuses, financial concepts, timestamps, provenance terms, and metric terms. Current definitions constrain future implementation but do not claim that implementation exists.

This document does not define Python classes or types, database tables or columns, API schemas, financial formulas, source-tag mappings, risk thresholds, or user-interface behavior. Data-stage structure belongs to [`data-contracts.md`](data-contracts.md); financial-analysis rules belong to [`financial-methodology.md`](financial-methodology.md).

## 2. Dictionary principles

- **One term, one meaning:** A controlled term must not carry different meanings across stages without an explicit qualifier.
- **Explicit business definitions:** Definitions must describe financial or data meaning, not merely a storage representation.
- **Provider-independent naming:** Controlled analytical names should not embed provider tags or response shapes.
- **Stable identifiers:** An identifier must retain its assigned meaning across labels, providers, and presentation changes.
- **Provenance preservation:** Defined terms must support traceability to the evidence and decisions they describe.
- **No silent semantic changes:** A meaning must not change without documented compatibility and version review.
- **Missing is not zero:** Missing, unavailable, invalid, unsupported, and not applicable are not numeric zero.
- **No implementation claim:** A current definition establishes vocabulary, not evidence that code or persisted data exists.
- **Deliberate evolution:** Controlled vocabularies should expand only through approved, documented changes.

## 3. Naming conventions

- **Human-readable label:** A concise English display name in title case where appropriate, such as `Current Assets`. Labels may improve for clarity without changing identity.
- **Stable machine identifier:** A provider-independent semantic identifier whose assigned meaning must not be reused.
- **Identifier style:** Controlled identifiers should use lowercase `snake_case`; exact serialized field names remain deferred.
- **Concept name:** A concept identifier must name one accounting concept, not a collection. Established accounting labels may be grammatically plural, as in `current_assets`.
- **Metric identifier:** A stable lowercase `snake_case` name for one approved analytical measure, such as `current_ratio`.
- **Status identifier:** A lowercase `snake_case` name for one controlled outcome meaning, such as `not_applicable`.
- **Reason code:** A stable lowercase `snake_case` identifier for a specific exceptional or limiting reason.
- **Version identifier:** A stable reference to one approved semantic definition set. Its exact format is deferred.

Names must be unambiguous in context. Labels must not replace stable identifiers, and provider tags must not become normalized concept identifiers by convenience.

## 4. Company identity terms

- **Company:** The legal reporting entity whose financial information is analyzed, within an approved accounting scope.
- **Stable company identifier:** The platform-controlled identity that must continue to identify the same analytical entity over time. Its exact format is deferred.
- **Ticker symbol:** An exchange-facing trading symbol associated with a security or issuer. It may change or be reused and must not be the permanent primary company identifier.
- **Legal company name:** The formal issuer name associated with the company for the relevant time and source context; it is descriptive, not necessarily immutable.
- **Provider company identifier:** A provider-assigned identifier for a company, meaningful only with its provider namespace.
- **SEC CIK:** The Central Index Key assigned by the SEC to a filer. It is an SEC provider identifier and must be associated with, not substituted for, the stable company identifier.
- **Industry:** A narrower business-activity classification assigned under a named classification system and version. No classification taxonomy is approved here.
- **Sector:** A broader business-activity grouping assigned under a named classification system and version. It must not be inferred from an undocumented label.

## 5. Provider and source terms

- **Provider:** The organization that makes source data available, such as the SEC.
- **Source system:** The provider-operated system or dataset from which evidence is obtained.
- **Source endpoint:** The specific provider resource or access location requested; it does not define analytical meaning.
- **Original provider payload:** The provider response received before project transformation, byte-for-byte original when transport bytes matter or otherwise semantically original.
- **Locally preserved raw response:** An immutable local copy of an original payload plus retrieval metadata, kept separate from processed data.
- **Sanitized committed fixture:** A reviewed, reduced or redacted test artifact that preserves the behavior under test. It is not the canonical original payload.
- **Retrieval event:** One attempt or completed act of obtaining a provider resource with its request and outcome context.
- **Retrieval timestamp:** The time the platform received the provider response; it is not a filing or reporting date.
- **Source concept:** The provider's semantic concept before mapping to a normalized financial concept.
- **Original source tag:** The exact provider tag or label attached to a source fact, retained for provenance.
- **Validated provider record:** A provider-facing source-fact representation that passed applicable shape and basic consistency checks; validation does not imply selection or metric eligibility.

## 6. Filing and reporting terms

- **Filing:** A submission made available by a reporting entity through the SEC, with its own form, accession, and filing context.
- **Filing form:** The provider designation for the filing type, such as an annual or quarterly filing form.
- **Annual filing:** A filing covering the issuer's annual reporting obligations; Phase 1 eligibility will be limited by an approved 10-K policy before implementation.
- **Quarterly filing:** A filing covering an interim quarterly reporting context. It is outside Phase 1 analysis.
- **Accession number:** The SEC-assigned identifier for a specific filing submission, retained when available.
- **Filing date:** The date the filing became filed or available under approved source semantics.
- **Reporting date:** The date the financial information represents, expressed by a period end or instant date as applicable; it is not the filing date.
- **Fiscal year:** The issuer-defined annual accounting period, which may differ from the calendar year.
- **Fiscal period:** The provider or filing designation for the reporting context, interpreted only with fiscal year and period dates.
- **Amendment:** A later filing that modifies or supplements an earlier filing; it must not silently overwrite prior evidence.
- **Restatement:** A later reporting of revised facts for an earlier period; both earlier and revised contexts must remain traceable.
- **Analysis cutoff:** The latest filing date or observation time permitted for an analysis. Evidence first available after it must be excluded.

Filing date, reporting date, retrieval timestamp, and analysis cutoff describe different events and must not be substituted for one another.

## 7. Period terms

- **Reporting period:** The fiscal time context represented by a fact or result.
- **Period type:** The controlled distinction between a duration and an instant context.
- **Duration fact:** A fact measuring activity over a period bounded by a start and end date.
- **Instant fact:** A fact measuring a position at one date.
- **Period start:** The inclusive or source-defined beginning date of a duration fact, interpreted under approved source semantics.
- **Period end:** The ending date of a duration fact; it does not by itself prove annual comparability.
- **Instant date:** The date represented by an instant fact, normally the applicable reporting boundary.
- **Comparable period:** A period sufficiently aligned in company, scope, duration, fiscal context, currency, unit, and cutoff treatment under approved methodology.
- **Prior period:** The earlier comparable period required by an analysis; it is not merely the previous record in response order.
- **Target period:** The reporting period for which a fact set or metric result is requested.

## 8. Financial value terms

- **Reported value:** The numeric or explicitly nonnumeric value reported by the source, before analytical calculation.
- **Normalized value:** A reported value expressed through an approved normalized unit or scale representation without changing economic meaning.
- **Currency:** The monetary denomination of a fact. It must be explicit where applicable and must not be silently converted.
- **Unit:** The measurement dimension reported for a value, such as currency, shares, or a dimensionless measure.
- **Scale:** The magnitude convention applied to a value, such as units or millions; changing scale must preserve value and provenance.
- **Sign convention:** The documented meaning of positive and negative values for a concept. Provider-specific sign rules remain deferred.
- **Monetary fact:** A fact measured in a stated currency and compatible monetary unit.
- **Ratio:** A quotient-type analytical value; it is not a percentage unless methodology explicitly defines it as one.
- **Percentage:** A relative value expressed per hundred under an approved methodology.
- **Count:** A nonmonetary number of discrete items.
- **Shares:** A count of equity units under a stated share basis; it is not a monetary amount.
- **Dimensionless value:** A value whose compatible units cancel or that otherwise has no physical or monetary dimension.

Normalization must not change economic meaning, accounting scope, concept identity, currency, reporting period, or sign convention.

## 9. Phase 1 normalized financial concepts

Only the following normalized concepts are approved for Phase 1. Exact SEC XBRL tag mappings and formulas are not defined here.

| Canonical identifier | Label | Business definition | Period type | Expected economic meaning | Important limitations |
|---|---|---|---|---|---|
| `revenue` | Revenue | Reported top-line amount from ordinary activities for the fiscal period. | Duration | Consolidated annual activity for the supported company. | Not cash receipts, gross billings, segment revenue, or an unapproved non-GAAP measure. |
| `current_assets` | Current Assets | Assets the reporting company classifies as current at the reporting date. | Instant | Consolidated current-asset position at fiscal year-end. | Must not be reconstructed from incomplete components or include reclassified non-current assets. |
| `current_liabilities` | Current Liabilities | Obligations the reporting company classifies as current at the reporting date. | Instant | Consolidated current-liability position at the same fiscal year-end as Current Assets. | Must not be reconstructed from incomplete components or include reclassified long-term obligations. |
| `operating_income` | Operating Income | Reported result from operations after operating costs and expenses and before items outside the operating subtotal. | Duration | Consolidated annual operating performance. | Net income, pretax income, segment profit, and unapproved non-GAAP measures are not substitutes. |
| `interest_expense` | Interest Expense | Reported cost of interest for the fiscal period within the approved concept definition. | Duration | Consolidated annual interest cost compatible with Operating Income. | Netted or broader finance cost is unsupported unless an approved mapping explicitly permits it. |

## 10. Normalization and selection terms

- **Normalized financial fact:** A provider-independent reported fact mapped to one controlled concept with period, unit, currency, quality, selection, and provenance context.
- **Candidate fact:** A validated provider fact considered by an approved selection policy for a requested concept and context.
- **Selected fact:** The unique eligible candidate chosen under the approved policy; response order alone must never select it.
- **Rejected candidate:** A considered fact not selected for a documented eligibility or priority reason.
- **Selection rationale:** The deterministic explanation of candidates, rules, rejections, and final outcome.
- **Selection status:** The controlled outcome of fact selection, distinct from general data quality.
- **Ambiguity:** A state in which more than one candidate remains plausible and policy cannot select uniquely, whether or not values disagree.
- **Conflict:** A state in which eligible evidence disagrees materially and approved policy cannot resolve it.
- **Unsupported source fact:** A source fact requiring an unapproved concept, scope, form, period, unit, currency, or treatment.
- **Normalized concept identifier:** The stable provider-independent identifier assigned to one approved financial concept.

## 11. Metric terms

- **Metric:** An approved analytical measure derived from compatible normalized facts under documented methodology.
- **Metric identifier:** The stable provider-independent identifier for one metric definition.
- **Metric input set:** The evaluated collection of normalized facts, compatibility outcomes, completeness, and provenance supplied to one metric.
- **Metric result:** The value-or-status outcome of applying one methodology version to one metric input set.
- **Metric value:** The numeric result when required inputs and methodology permit calculation; exceptional outcomes must not fabricate one.
- **Methodology version:** The stable reference to the exact approved selection and calculation rules used.
- **Calculation timestamp:** The time the platform produced a metric result; it is distinct from source and filing times.
- **Interpretation:** A bounded explanation of what a supported result may indicate and what it does not establish.
- **Reason code:** A stable machine-readable identifier explaining an exceptional, unavailable, or limited outcome.
- **Input reference:** A stable link from an input-set entry to its normalized fact and selection evidence.
- **Result provenance:** The lineage linking a metric result through inputs and transformations to source evidence.

## 12. Phase 1 metrics

Only these metric terms are approved for Phase 1. Their formulas and exceptional calculation rules remain owned by financial methodology.

| Canonical identifier | Label | Analytical purpose | Required normalized concepts | Output category | Reporting-period context | Limitations |
|---|---|---|---|---|---|---|
| `revenue_growth` | Revenue Growth | Describe direction and relative change in reported annual revenue. | Revenue for current and prior comparable annual periods. | Relative-change percentage. | Two compatible annual duration periods. | Does not explain profitability, cash generation, credit quality, organic growth, acquisitions, disposals, currency effects, or fiscal-year changes. |
| `current_ratio` | Current Ratio | Assess balance-sheet coverage of current liabilities by current assets. | Current Assets and Current Liabilities. | Dimensionless ratio. | One common fiscal-year-end instant. | Does not prove asset liquidity, liability timing, funding access, or working-capital quality. |
| `interest_coverage` | Interest Coverage | Assess operating performance relative to reported interest cost. | Operating Income and Interest Expense. | Dimensionless ratio. | One compatible annual duration period. | Is not a cash-flow measure or assurance of debt-service capacity; zero, negative, netted, missing, or unsupported inputs require explicit outcomes. |

## 13. Data-quality vocabulary

- **Complete:** All required eligible data and lineage are present, compatible, and sufficient for the stated purpose.
- **Partial:** Useful supported data exists, but non-critical information or context is absent and the limitation is disclosed.
- **Missing:** A required or expected fact is absent from eligible evidence; this is not zero.
- **Unavailable:** A stage cannot provide a usable fact or result for the requested context; the reason must be explicit.
- **Invalid:** Present data violates an applicable validity or consistency rule.
- **Unsupported:** Available data or required treatment is outside approved scope or methodology.
- **Conflicting:** Eligible evidence disagrees materially and approved policy cannot resolve it.
- **Ambiguous:** Candidate evaluation cannot identify one unique eligible fact; candidates need not have different values.
- **Not applicable:** The concept or metric does not apply under approved methodology.

Status applicability is stage-specific:

| Level | Applicable controlled meanings |
|---|---|
| Source-record | `complete`, `partial`, `invalid`, or `unsupported`; `missing` or `unavailable` describes the absent-record or retrieval outcome, not a present record. |
| Normalized-fact | `complete`, `partial`, `missing`, `invalid`, `unsupported`, or `not_applicable`, with selection context retained. |
| Selection | `selected`, `unavailable`, `ambiguous`, `conflicting`, `unsupported`, or `invalid`; selection status is not interchangeable with data-quality status. |
| Metric-input | `complete`, `partial`, `missing`, `unavailable`, `invalid`, `unsupported`, `conflicting`, `ambiguous`, or `not_applicable` as relevant to the assembled set. |
| Metric-result | `complete`, `partial`, `unavailable`, `invalid`, `unsupported`, `conflicting`, `ambiguous`, or `not_applicable`; only permitted outcomes may carry a value. |

## 14. Completeness terms

- **Completeness:** Whether all information required for a stated fact, input set, result, and its provenance is present and usable.
- **Complete result:** A result supported by all required compatible inputs and sufficient lineage.
- **Partial result:** A permitted result with useful supported output but a disclosed non-critical omission or limitation.
- **Unavailable result:** A value-less outcome indicating that a usable result cannot be produced for an explicit reason.
- **Required input:** A normalized concept that must be usable for the metric to produce a numeric result.
- **Optional input:** An approved non-blocking input that may add context but whose absence does not invalidate calculation.
- **Critical missing input:** An absent required input that blocks a numeric result.
- **Non-critical missing input:** An absent optional input that may reduce completeness but does not by itself block an otherwise supported result.

Completeness is not a confidence score and must not be presented as one.

## 15. Provenance and lineage terms

- **Provenance:** The source identity and contextual evidence explaining where data came from and how it was obtained.
- **Lineage:** The ordered relationships connecting evidence, transformations, decisions, inputs, and outputs.
- **Provenance reference:** A stable link to lineage evidence within the applicable contract context.
- **Source evidence:** The provider payload, preserved response or documented fixture, and source records supporting a fact.
- **Transformation step:** One deterministic validation, normalization, selection, or calculation operation with its version and outcome.
- **Candidate set:** All source facts actually considered for one selection request.
- **Selection evidence:** Candidate set, eligibility decisions, rejected alternatives, rationale, cutoff, and amendment/restatement treatment.
- **Calculation evidence:** Metric input set, compatibility outcomes, methodology version, reason codes, and calculation outcome.
- **Publication evidence:** The result identity, calculation timestamp, published representation, and limitations needed to show what was made available, if publication is later implemented.

Expected lineage must support traversal in both directions:

```text
Metric result
  -> metric input set
  -> normalized financial fact
  -> validated provider record
  -> locally preserved raw response or documented fixture evidence
  -> original provider source
```

## 16. Validation terms

- **Validation:** Deterministic evaluation of data against rules appropriate to its stage; success does not prove economic truth.
- **Schema validation:** Evaluation of required structure, field presence, and readable primitive representation without silent coercion.
- **Semantic validation:** Evaluation of meaning and internal consistency, including company, concept, filing, dates, scope, unit, and currency.
- **Compatibility validation:** Evaluation of whether facts may be selected, compared, or combined for a stated purpose.
- **Period compatibility:** Alignment of period type, dates, fiscal context, duration, and approved cutoff treatment.
- **Currency compatibility:** Agreement of currencies or use of an explicitly approved conversion policy; Phase 1 has no conversion policy.
- **Unit compatibility:** Agreement of measurement dimension and approved scale treatment.
- **Provenance completeness:** Presence of sufficient lineage to identify source evidence and material transformations.
- **Validation failure:** A blocking rule violation that must produce an explicit unsuccessful outcome.
- **Validation warning:** A non-blocking, documented limitation that may reduce completeness but must not silently change meaning.

## 17. Controlled reason-code principles

Reason codes must be stable, machine-readable, human-explainable, documented, and version-aware. They should be non-overlapping where practical and must identify one primary exceptional or limiting reason. Multiple material reasons may be retained when the contract permits them.

A reason code must not replace detailed provenance, validation evidence, selection rationale, or interpretation. Display wording may elaborate on a code but must not redefine it.

Illustrative categories include:

- `missing_input`
- `period_mismatch`
- `currency_mismatch`
- `unit_mismatch`
- `ambiguous_fact`
- `conflicting_fact`
- `unsupported_source`
- `zero_denominator`
- `invalid_value`

These examples do not finalize the complete vocabulary, precedence, combinations, or serialized representation.

## 18. Versioning terms

- **Contract version:** The identifier for one approved set of data-stage structures and invariants.
- **Methodology version:** The identifier for one approved set of financial selection and calculation rules.
- **Dictionary version:** The identifier for one approved set of controlled terms and meanings.
- **Breaking semantic change:** A change that removes, reassigns, narrows incompatibly, or materially alters an existing meaning or required interpretation.
- **Backward-compatible addition:** A new optional term or controlled value that preserves existing meanings and permits older consumers to fail safely.
- **Deprecated term:** A supported term scheduled for replacement or removal; it must not be repurposed during deprecation.
- **Migration note:** Documentation of affected meanings, consumers, replacement, compatibility treatment, and transition expectations.

Exact version formats, storage, and negotiation mechanics remain deferred.

## 19. Phase 1 boundaries

Current Phase 1 dictionary scope is limited to:

- Microsoft Corporation under an approved stable company identity;
- annual SEC Company Facts and eligible annual 10-K context;
- Revenue, Current Assets, Current Liabilities, Operating Income, and Interest Expense;
- Revenue Growth, Current Ratio, and Interest Coverage;
- sanitized committed fixtures for deterministic offline processing by default; and
- optional isolated live SEC retrieval with local raw-response preservation.

Cross-company concept generalization, quarterly and trailing-twelve-month analysis, persistence schemas, API schemas, dashboards, risk models, stress testing, peer analysis, and currency conversion remain outside Phase 1. These definitions constrain future work but do not claim that Phase 1 has begun or that the terms are implemented. [`../ROADMAP.md`](../ROADMAP.md) alone governs status.

## 20. Known limitations and deferred decisions

The following remain unresolved and must not be invented implicitly:

- exact stable company, provenance, and other identifier formats;
- exact reason-code vocabulary, precedence, and combinations;
- exact SEC source-tag mappings and priorities;
- exact sign conventions for provider-specific facts;
- exact serialized field names and field encodings;
- exact enum representations;
- exact contract, methodology, and dictionary version formats; and
- future cross-company concept extensions and classification taxonomies.

Each decision requires approval by its owning methodology, contract, dictionary, architecture, roadmap, or execution-plan process before dependent implementation.

## 21. Related documents

- [`../AGENTS.md`](../AGENTS.md) — agent behavior, priorities, document ownership, and precedence.
- [`product-requirements.md`](product-requirements.md) — product scope and acceptance.
- [`architecture.md`](architecture.md) and [`adr/`](adr/) — technical boundaries and durable decisions.
- [`financial-methodology.md`](financial-methodology.md) — financial concepts, period treatment, metric semantics, and limitations.
- [`data-contracts.md`](data-contracts.md) — data stages, invariants, statuses, and evolution rules.
- [`risk-model.md`](risk-model.md) — future risk terminology when approved.
- [`../ROADMAP.md`](../ROADMAP.md) — sequencing, dependencies, current phase, and progress.
- [`../PLANS.md`](../PLANS.md) — requirements for bounded execution plans.

When documents overlap, the ownership and precedence rules in `AGENTS.md` apply.
