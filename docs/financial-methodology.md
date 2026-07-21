# Financial Methodology

## 1. Purpose and scope

This document is the authoritative methodology for how the Corporate Credit Risk & Financial Health Platform interprets reported financial facts and produces financial analysis. It defines analytical principles, period treatment, concept meaning, data-quality treatment, metric governance, and verification expectations.

The current methodology is limited to the foundation required for the Phase 1 Microsoft annual analysis: five normalized financial concepts and three metrics derived from SEC Company Facts. This scope statement does not claim that the analysis is implemented or that a roadmap phase is complete; `ROADMAP.md` alone owns that status.

Future methodology is limited to the subjects named in section 16 until separately researched, approved, documented, and placed in scope.

This document does not define:

- product scope or acceptance criteria;
- software architecture or implementation;
- APIs, schemas, database design, or user-interface behavior;
- provider transport or raw-file storage procedures; or
- phase sequencing or progress.

The product, architecture, data, risk, and roadmap documents remain authoritative for those subjects. This methodology is framework-independent.

## 2. Design philosophy

Financial analysis follows these principles:

- **Explainability before complexity.** A simpler defensible method is preferred to a more elaborate method that cannot be clearly explained.
- **Deterministic before intelligent.** The same eligible facts, methodology version, and analysis cutoff must produce the same analytical outcome.
- **Financial correctness over feature count.** Unsupported conclusions are not accepted merely to increase coverage.
- **Conservative data handling.** Uncertainty, ambiguity, and incompatibility are surfaced rather than resolved through optimism or convenience.
- **Reproducibility.** Periods, inputs, decisions, and limitations are recorded so another analyst can repeat the analysis.
- **Traceability.** Every conclusion remains connected to its reported facts and filing context.
- **No silent assumptions.** A required assumption is explicit, justified, and approved, or the result is unavailable.
- **No hidden transformations.** Selection, normalization, scaling, and analytical treatment are visible and reviewable.

Financial analysis should be explainable enough that another analyst can reproduce every conclusion from the original source filings.

## 3. Accounting policy

The platform analyzes reported public financial information. It does not reinterpret accounting standards or replace the accounting judgments made by the reporting company and its auditors.

The methodology supports reported facts within an approved reporting scope. It
does not:

- create accounting entries or management adjustments;
- restate, recast, or repair a filing;
- convert non-GAAP measures into GAAP measures;
- infer an undisclosed accounting classification;
- reconcile IFRS and US GAAP; or
- assert that economically similar labels are accounting-equivalent without an approved concept mapping.

Reported does not mean automatically usable. A reported fact must still satisfy the approved company, concept, filing, period, scope, currency, unit, and cutoff rules. When a filing does not support the required analytical concept, the outcome is explicit rather than reconstructed through an undocumented adjustment.

## 4. Reporting period methodology

### 4.1 Annual reporting

Phase 1 uses annual facts from eligible annual SEC filings. Duration facts must represent the supported fiscal year, and point-in-time facts must represent its fiscal year-end. Annual values are not created by summing quarterly values unless a future approved methodology expressly permits that treatment.

### 4.2 Quarterly reporting

Quarterly and trailing-twelve-month analysis are not part of the current methodology. Quarterly facts are not substituted for annual facts, combined with annual facts, or annualized through an implicit assumption. A future quarterly methodology must address discrete-quarter and year-to-date reporting separately.

### 4.3 Point-in-time facts

Point-in-time facts describe a balance at a specific date. They are eligible only when that date matches the required fiscal period boundary under the approved selection policy. They are not treated as flows or assigned to a different date for convenience.

### 4.4 Duration facts

Duration facts describe activity over a stated start and end date. Both dates and the fiscal context must support the required annual period. Facts covering different durations are incompatible unless an approved methodology explicitly defines a comparison.

### 4.5 Fiscal-year alignment

The issuer's fiscal year, not the calendar year label alone, controls alignment. Comparisons use periods with compatible fiscal scope and duration. Fiscal year-end changes, 52/53-week years, transition periods, and other non-comparable periods are identified rather than silently treated as ordinary adjacent years.

### 4.6 Amendments

Amended filings do not silently overwrite earlier facts. The original and amended filing context remains traceable. Selection follows the approved amendment policy and the analysis cutoff; an amendment filed after that cutoff is unavailable to that historical analysis.

### 4.7 Restatements

Restated facts retain their relationship to the earlier reported facts and filing that introduced the restatement. For a current analysis, an eligible restated fact may be selected under the approved policy. A historical analysis uses only information filed by its cutoff and never applies a later restatement retroactively without explicit labeling as a revised historical view.

### 4.8 Analysis cutoff and future filings

The analysis cutoff is the latest filing date or observation time available to the analysis. Facts first disclosed after it are excluded, even when they describe an earlier reporting period. Filing date, reporting period, and retrieval date remain distinct. No result may use a future filing or later amendment through look-ahead.

When duplicate or conflicting facts remain equally eligible, the methodology returns a conflicting or otherwise unresolved outcome; response order is not a financial selection rule.

## 5. Financial concept definitions

Phase 1 supports only the following controlled concepts. Exact source-tag mappings and selection rules require later approved additions to this document and the data documentation before implementation.

### 5.1 Revenue

**Business meaning:** the reported top-line amount arising from the company's ordinary activities for the fiscal period.

**Accounting scope:** a consolidated annual duration fact for the supported company and fiscal year. It is not cash receipts, gross billings, segment revenue, or a non-GAAP measure unless an approved mapping explicitly establishes the reported consolidated concept.

### 5.2 Current Assets

**Business meaning:** assets the reporting company classifies as current at the reporting date.

**Accounting scope:** a consolidated point-in-time fact at fiscal year-end. The platform does not reclassify non-current assets or construct a current-assets total from incomplete components without an approved methodology.

### 5.3 Current Liabilities

**Business meaning:** obligations the reporting company classifies as current at the reporting date.

**Accounting scope:** a consolidated point-in-time fact at the same fiscal year-end and scope as Current Assets. The platform does not reclassify long-term obligations or construct a total from incomplete components without approval.

### 5.4 Operating Income

**Business meaning:** the reported result from operations after operating costs and expenses for the fiscal period, before items outside the reported operating subtotal.

**Accounting scope:** a consolidated annual duration fact. Net income, pretax income, segment profit, and non-GAAP operating measures are not substitutes.

### 5.5 Interest Expense

**Business meaning:** the reported cost of interest for the fiscal period within the approved concept definition.

**Accounting scope:** a consolidated annual duration fact compatible with Operating Income. A combined, netted, or broader finance-cost amount is not treated as Interest Expense unless the approved mapping and limitations explicitly support that treatment.

## 6. Currency and unit policy

Each fact retains its reported currency, unit, and scale. Values are comparable only when those attributes and their accounting scopes are compatible.

- Currency translation is not part of Phase 1 methodology.
- Monetary values in different currencies are not combined or compared as if equivalent.
- Scaling may place compatible values on a common magnitude only when the original scale and transformation remain traceable.
- Normalization preserves economic meaning; it does not convert monetary amounts into shares, percentages, counts, or other dimensions.
- Unsupported or unclear units produce an unsupported or invalid outcome rather than a guessed conversion.

Incompatible values are never silently combined. Display formatting must not alter the value used for analysis or obscure its original currency, unit, or scale.

## 7. Data quality philosophy

Data quality describes whether facts and analytical results are fit for their stated purpose. It is not a cosmetic confidence score.

- **Complete:** all required eligible inputs are present, compatible, and sufficiently supported for the stated result.
- **Partial:** some useful supported information exists, but non-blocking inputs or context are absent; the limitation accompanies the result.
- **Missing:** a required fact is not present in the eligible source data.
- **Invalid:** a fact is present but fails an applicable validity rule.
- **Unsupported:** the available fact, unit, scope, period, or treatment is outside the approved methodology.
- **Conflicting:** multiple eligible facts disagree and the approved policy cannot resolve them uniquely.
- **Not Applicable:** the concept or metric does not apply to the company, period, or analytical situation under the approved methodology.

An unresolved ambiguity is reported explicitly and is not treated as Complete. Exact status and reason-code vocabularies belong to the data contracts; their meaning must remain consistent with these methodological distinctions.

Future estimation is not implemented. The platform never estimates missing financial facts unless an explicitly documented estimation methodology has been approved. Any future estimate must remain distinguishable from a reported fact.

Zero is a reported numeric value, not a data-quality status and not a replacement for Missing, Unsupported, or Not Applicable.

## 8. Financial materiality

Not every missing or impaired value has equal analytical impact. Materiality is assessed relative to the conclusion being produced, not only by the size of a number.

A missing required input is calculation-blocking: no numeric result is published. A missing non-required item may allow a result while reducing completeness or limiting interpretation. A provenance gap can be material even when the numeric value appears plausible because the conclusion cannot be audited.

Materiality does not authorize invention, estimation, or silent substitution. Metric specifications identify which inputs are required and which limitations permit a partial result; no universal quantitative materiality threshold is defined here.

## 9. Metric lifecycle

```text
Source Fact
    ↓
Validation
    ↓
Normalization
    ↓
Calculation
    ↓
Verification
    ↓
Publication
```

1. **Source Fact:** identify the reported fact and preserve its company, concept,
   filing, period, currency, unit, and retrieval provenance.
2. **Validation:** establish that the fact is readable and eligible for further
   methodological evaluation; do not repair it through assumption.
3. **Normalization:** map an eligible source fact to a controlled concept and
   record why it was selected or why selection failed.
4. **Calculation:** apply the approved metric specification only to compatible,
   validated normalized inputs; preserve exceptional outcomes.
5. **Verification:** compare normal and exceptional cases with documented expected
   behavior, including an independently checked manual example.
6. **Publication:** present the result, data-quality status, provenance,
   interpretation, and limitations without recalculation or concealment.

No stage may silently correct a failure from an earlier stage.

## 10. Metric specification standard

Every metric proposed for approval must define:

- **Name:** stable, unambiguous analytical name.
- **Business meaning:** the question the metric is intended to answer.
- **Formula:** the exact mathematical relationship and sign convention.
- **Inputs:** controlled concepts and whether each is required.
- **Period rules:** compatible dates, durations, alignment, and cutoff treatment.
- **Currency rules:** permitted currencies and any approved translation treatment.
- **Unit rules:** required dimensions, scale handling, and incompatibilities.
- **Data-quality requirements:** blocking and non-blocking input states.
- **Edge cases:** zero or negative values, mismatches, conflicts, and boundaries.
- **Interpretation:** what supported values can and cannot indicate.
- **Limitations:** applicability, comparability, accounting, and data constraints.

This is a specification template, not approval of any formula. Each implemented
metric also requires a versioned definition, provenance expectations, explicit
exceptional behavior, and at least one independently verified manual example.

## 11. Phase 1 metrics

Phase 1 is limited to these metrics. This section defines objectives and inputs,
not formulas.

### 11.1 Revenue Growth

**Business objective:** describe the direction and relative change in reported
annual revenue between compatible fiscal years.

**Required inputs:** Revenue for the current and prior comparable annual periods,
with compatible company, scope, currency, unit, and cutoff treatment.

**Interpretation:** indicates top-line expansion or contraction. It does not by
itself explain profitability, cash generation, credit quality, organic growth, or
the effect of acquisitions, disposals, currency movements, and fiscal-year changes.

### 11.2 Current Ratio

**Business objective:** assess balance-sheet coverage of reported current
liabilities by reported current assets at a fiscal year-end.

**Required inputs:** Current Assets and Current Liabilities for the same company,
date, consolidated scope, currency, and compatible monetary unit.

**Interpretation:** provides a point-in-time liquidity indicator. It does not prove
asset liquidity, liability timing, funding access, or the quality of working
capital. Zero or otherwise invalid liability inputs receive explicit treatment.

### 11.3 Interest Coverage

**Business objective:** assess the relationship between reported operating
performance and reported interest cost for a compatible annual period.

**Required inputs:** Operating Income and Interest Expense for the same company,
fiscal period, consolidated scope, currency, and compatible monetary unit.

**Interpretation:** indicates operating capacity relative to interest cost under
the approved definition. It is not a cash-flow measure or assurance of debt-service
capacity. Zero, negative, netted, missing, or unsupported inputs require explicit
outcomes and limitations.

## 12. Financial integrity rules

Financial analysis must never:

- treat Missing, Unsupported, or Not Applicable as zero;
- mix annual and quarterly values;
- mix point-in-time and duration facts as though they describe the same basis;
- mix different companies, fiscal periods, accounting scopes, or filing contexts;
- combine incompatible currencies, units, or scales;
- use facts from filings after the analysis cutoff;
- ignore amendments, restatements, or filing availability;
- ignore or sever provenance;
- silently overwrite, rank, average, or select conflicting facts;
- substitute a nearby accounting concept without approved mapping;
- publish a numeric result when a required input is unusable; or
- describe an internal analytical output as an official credit rating.

## 13. Explainability requirements

Every published metric should preserve or make accessible:

- source provider and filing identity;
- company and reporting period;
- normalized input concepts and values;
- source-fact provenance and selection rationale;
- applicable methodology version;
- data-quality and completeness status;
- exceptional reason or limitation; and
- interpretation that does not exceed the metric's stated purpose.

An analyst must be able to move backward from the published conclusion to each
input and its reported source, and forward from each source fact through every
methodological decision. Contradictory or negative evidence is not hidden.

## 14. Validation philosophy

Validation is deterministic: a stated rule produces the same outcome for the same
facts, context, methodology version, and cutoff. It covers normal and exceptional
financial behavior without treating test success as proof of economic truth.

- **Manual examples** independently verify each approved metric using traceable
  inputs and documented expected outcomes.
- **Regression testing** preserves behavior after a defect or ambiguity is found.
- **Accounting sanity checks** identify impossible or suspect combinations without
  silently rewriting reported facts.
- **Boundary testing** covers zero and negative values, period edges, cutoffs,
  incompatible currencies or units, conflicts, and denominator conditions.

Validation must also cover missing, partial, invalid, unsupported, conflicting, and
not-applicable cases as relevant. A failed check yields an explicit outcome and
reason; it does not trigger an undocumented fallback.

## 15. Known methodology limitations

The platform does not currently provide:

- investment or trading advice;
- accounting advice or accounting-policy determinations;
- audit opinions or assurance;
- fraud detection;
- official credit ratings;
- forecasts or management projections;
- probability-of-default estimates; or
- valuation models.

The initial methodology is narrow, relies on public reported information, and does not correct errors or omissions in source filings. Metric interpretation must be read with the disclosed data quality, period basis, accounting scope, and company context.

## 16. Future methodologies

The following are future methodology subjects only; none is defined, approved, or
implemented by this document:

- **Altman Z-Score:** an explicitly selected variant with documented population,
  inputs, applicability, interpretation, and limitations.
- **Piotroski F-Score:** a defined criterion set with period-comparison rules,
  missing-input behavior, applicability, and limitations.
- **Internal Financial Health Score:** a transparent, deterministic framework with
  approved components, transformations, weights, thresholds, completeness rules,
  contributions, and explanations; it is not an official credit rating.
- **Stress Testing:** reproducible, versioned scenarios with explicit baselines,
  assumptions, affected inputs, outputs, and limitations; results are not
  forecasts.

Each requires separate research, approval, detailed methodology, verification, and
roadmap authorization before implementation. No formula, threshold, weight, model
variant, or scenario assumption is established here.
