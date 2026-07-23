# Financial Methodology

## 1. Purpose and scope

This document is the authoritative methodology for how the Corporate Credit Risk & Financial Health Platform interprets reported financial facts and produces financial analysis. It defines analytical principles, period treatment, concept meaning, data-quality treatment, metric governance, and verification expectations.

The current methodology is limited to the foundation required for the Phase 1 Microsoft annual analysis: five normalized financial concepts and three metrics derived from SEC Company Facts. This scope statement does not claim that the analysis is implemented or that a roadmap phase is complete; `ROADMAP.md` alone owns that status.

Future methodology is limited to the subjects named in section 17 until separately researched, approved, documented, and placed in scope.

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

Restated facts retain their relationship to the earlier reported facts and filing
that introduced the restatement. A restated fact may be selected only when an
approved policy can establish its treatment from authoritative evidence. A
historical analysis uses only information filed by its cutoff and never applies a
later restatement retroactively.

### 4.8 Analysis cutoff and future filings

The analysis cutoff is the latest filing date permitted for the analysis under the
applicable policy. Facts first filed after it are excluded, even when they describe
an earlier reporting period. Filing date, reporting period, retrieval date, and
analysis cutoff remain distinct. No result may use a future filing or later
amendment through look-ahead.

When duplicate or conflicting facts remain equally eligible, the methodology returns a conflicting or otherwise unresolved outcome; response order is not a financial selection rule.

## 5. Financial concept definitions

Phase 1 supports only the following controlled concepts. Section 16 defines the
Microsoft annual source-tag mappings and selection rules. Their documentation does
not claim an implementation.

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

## 16. Phase 1 Microsoft Annual Fact-Selection Policy

### 16.1 Policy identity, analytical boundary, and authority

This section is the authoritative selection methodology for one narrow policy. Its
stable methodology identifier is:

```text
microsoft_annual_company_facts_v1
```

The only approved analytical entity is Microsoft Corporation. Its stable internal
analytical identifier for this narrow policy is `microsoft_corporation`, and its
associated SEC identity is canonical CIK `0000789019`. The CIK is the ten-digit
representation of the accepted repository value `789019`.

- A request must identify `microsoft_corporation` and CIK `0000789019`; its
  Company Facts payload must identify CIK `0000789019`.
- A payload for any other CIK is ineligible and produces an Invalid selection
  outcome. Facts from another legal entity must never be combined with Microsoft
  facts.
- `MSFT` is a descriptive ticker, not permanent identity.
- `MICROSOFT CORP`, `MICROSOFT CORPORATION`, and other entity-name text are
  descriptive. A name match cannot cure a CIK mismatch, and a harmless name
  variation cannot override a matching CIK.
- This approval does not create a reusable company registry or a generalized
  identity policy.

The policy selects entity-wide, consolidated annual facts represented by the SEC
Company Facts API and Microsoft annual statements. It maps a reported fact to one
of the five controlled concepts in section 5; it performs no metric calculation.
Nothing in this section claims that a selector, normalizer, or normalized fact is
implemented.

### 16.2 Authoritative evidence

The decisions below were verified on 2026-07-23 from repository contracts and
these primary sources:

- the [SEC EDGAR XBRL API documentation](https://www.sec.gov/search-filings/edgar-application-programming-interfaces),
  which describes Company Facts and Company Concept as standard-taxonomy,
  entity-wide facts aggregated across submissions;
- the [SEC EDGAR XBRL Guide](https://www.sec.gov/files/edgar/filer-information/specifications/xbrl-guide-2026-06-29.pdf),
  including fiscal-focus, period, unit, amendment-flag, and XBRL fact semantics;
- the [SEC Financial Statement Data Sets documentation](https://www.sec.gov/files/financial-statement-data-sets.pdf),
  which cautions that extracted as-filed data can contain redundancies,
  inconsistencies, and discrepancies;
- [Exchange Act Rule 12b-15](https://www.sec.gov/files/rules/final/33-8238.htm),
  under which an amendment sets out the complete text of each item amended rather
  than replacing every item in the original report;
- the SEC Office of the Chief Accountant's
  [restatement discussion](https://www.sec.gov/newsroom/speeches-statements/munter-statement-assessing-materiality-030922),
  which distinguishes reissuance and revision restatements;
- Microsoft's official
  [SEC submissions metadata](https://data.sec.gov/submissions/CIK0000789019.json)
  and the FY2025
  [10-K filing index](https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/0000950170-25-100235-index.html);
- official SEC Company Concept data for
  [`RevenueFromContractWithCustomerExcludingAssessedTax`](https://data.sec.gov/api/xbrl/companyconcept/CIK0000789019/us-gaap/RevenueFromContractWithCustomerExcludingAssessedTax.json),
  [`SalesRevenueNet`](https://data.sec.gov/api/xbrl/companyconcept/CIK0000789019/us-gaap/SalesRevenueNet.json),
  [`Revenues`](https://data.sec.gov/api/xbrl/companyconcept/CIK0000789019/us-gaap/Revenues.json),
  [`AssetsCurrent`](https://data.sec.gov/api/xbrl/companyconcept/CIK0000789019/us-gaap/AssetsCurrent.json),
  [`LiabilitiesCurrent`](https://data.sec.gov/api/xbrl/companyconcept/CIK0000789019/us-gaap/LiabilitiesCurrent.json),
  [`OperatingIncomeLoss`](https://data.sec.gov/api/xbrl/companyconcept/CIK0000789019/us-gaap/OperatingIncomeLoss.json),
  [`InterestExpenseNonoperating`](https://data.sec.gov/api/xbrl/companyconcept/CIK0000789019/us-gaap/InterestExpenseNonoperating.json),
  and
  [`InterestExpense`](https://data.sec.gov/api/xbrl/companyconcept/CIK0000789019/us-gaap/InterestExpense.json);
- Microsoft's filed FY2010
  [10-K](https://www.sec.gov/Archives/edgar/data/789019/000119312510171791/d10k.htm),
  FY2011
  [10-K](https://www.sec.gov/Archives/edgar/data/789019/000119312511200680/d10k.htm),
  FY2017
  [10-K](https://www.sec.gov/Archives/edgar/data/789019/000156459017014900/msft-10k_20170630.htm),
  FY2018
  [10-K](https://www.sec.gov/Archives/edgar/data/789019/000156459018019062/msft-10k_20180630.htm),
  FY2024
  [interest-expense XBRL report](https://www.sec.gov/Archives/edgar/data/789019/000095017024087843/R52.htm),
  and FY2025
  [interest-expense XBRL report](https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/R48.htm).

The research inspected only the narrow official submissions, filings, statement
reports, and individual Company Concept resources needed for the policy. It did
not use a broad taxonomy search or download or commit a full live Company Facts
payload.

### 16.3 Annual selection request

One request selects one normalized concept for one Microsoft fiscal year. It must
contain or reference all of the following context:

| Context | Phase 1 requirement |
|---|---|
| Approved company identity | Stable identifier `microsoft_corporation` with canonical SEC CIK `0000789019` |
| Normalized concept | Exactly one of `revenue`, `current_assets`, `current_liabilities`, `operating_income`, or `interest_expense` |
| Target fiscal year | The issuer fiscal-year focus expected in an ordinary current-year annual observation |
| Target fiscal-year start | Required for Revenue, Operating Income, and Interest Expense; absent or not applicable for Current Assets and Current Liabilities |
| Target fiscal-year end | Required for all five concepts |
| Analysis cutoff | A date without a time or timezone |
| Methodology version | Exactly `microsoft_annual_company_facts_v1` |

The target reporting period and analysis cutoff answer different questions. The
reporting period says what the fact represents; the cutoff says which filings were
available to the analysis. Phase 1 applies this inclusive date-only rule before
ranking:

```text
observation.filed <= analysis_cutoff
```

`filed` is the SEC Company Facts filing date. Retrieval time records when the raw
artifact was obtained and remains in provenance, but it neither establishes nor
replaces filing availability. A later-retrieved aggregate may support an
as-of-cutoff analysis only through observations whose `filed` dates satisfy the
rule.

Missing, contradictory, or inapplicable request fields are not inferred. A
duration request without its exact start, an instant request with a start, an
unsupported concept or version, or a different company identity produces the
explicit outcome defined in section 16.11.

### 16.4 Filing forms and amendments

Form comparison is exact and case-sensitive:

- `10-K` is the only ordinary eligible filing form.
- `10-K/A` is conditionally considered only as amendment evidence under this
  subsection. It is never an ordinary annual candidate and never wins because it
  is later in a response or has a later filing date.
- Every other form, including `10-Q`, `8-K`, registration statements, foreign
  annual forms, and transition-form variants, is ineligible.

An observation in a `10-K/A` filed after the cutoff is rejected before amendment
treatment. For an amendment to replace an original target fact safely, evidence
must establish all of the following:

1. the exact original 10-K accession that the 10-K/A amends;
2. the amendment's filing date is on or before the cutoff;
3. company, approved tag, unit, target fiscal context, and exact period match;
4. the filed amendment scope explicitly covers the financial-statement item or
   target fact; and
5. the filed amendment establishes the replacement value rather than merely
   repeating or supplementing disclosure.

Company Facts observations preserve accession, form, filed date, period, unit, and
value, but do not carry the original-amendment link or target-specific amendment
scope. An `/A` submission indicator also does not prove that its XBRL facts
changed. Consequently, this Company-Facts-only policy cannot establish a changed
target-fact supersession from a differing `10-K/A` observation alone.

The deterministic Phase 1 treatment is:

- If exactly one otherwise eligible original `10-K` observation exists and a
  cutoff-eligible `10-K/A` repeats the same approved tag, unit, period, fiscal
  context, and numeric value, the amendment does not supersede the original. The
  original remains the controlling candidate; the value-agreeing amendment is
  retained as a Rejected non-controlling candidate with reason
  `equivalent_duplicates`, and the Selected outcome carries that reason.
- If a `10-K/A` supplies a different value, supplies the only target observation,
  or cannot be related safely to exactly one original target fact, the outcome is
  Unsupported with reason `amendment_unresolved`. The selector must not choose
  either value.
- If a `10-K/A` omits the target fact, that absence neither deletes nor replaces
  an otherwise eligible original observation. Omission is not evidence of
  supersession.
- Original and amended accession numbers, forms, filing dates, values, and raw
  artifact lineage remain in provenance in every case.

Microsoft's official submissions history inspected for this policy contained no
`10-K/A` precedent. The rule is therefore deliberately prospective and rests on
SEC amendment semantics, not an invented Microsoft replacement history.

### 16.5 Later reporting and restatements

This policy distinguishes:

- an **amendment**, identified by form `10-K/A` and governed by section 16.4;
- a **later-reported prior-period fact**, which is an observation in a later
  `10-K` whose actual start/end or instant date describes the target period but
  whose `fy` ordinarily describes the later filing's fiscal focus;
- an **exact or equivalent duplicate**, governed by section 16.10; and
- a **conflicting observation**, whose value differs at equal ordinary
  eligibility.

A later-reported prior-period fact is not automatically a restatement and never
overwrites the original merely because it was filed later. Historical analysis
excludes it when `filed > analysis_cutoff`. When it is on or before a current
analysis cutoff, it is evaluated as potential restatement evidence even though its
`fy` or `fp` does not make it an ordinary current-year candidate.

For observations with an approved source tag, exact `USD` unit, eligible `10-K`
form, and exact target dates:

- a later comparative with the same numeric value is retained and rejected from
  ordinary selection for its fiscal-context mismatch; it does not displace or
  block an otherwise unique original fact;
- a later comparative with a different numeric value produces Unsupported with
  reason `restatement_unresolved`, whether it uses the same approved tag or
  another approved tag for that normalized concept; and
- an explicit filing-level error-correction or restatement indicator is
  insufficient by itself because Company Facts does not identify the target fact,
  correction relationship, or controlling value.

This treatment is supported by actual Microsoft history. The FY2018 10-K reports
that Topic 606 was adopted using the full retrospective method and reports
different FY2017 Revenue and Operating Income from the FY2017 10-K. Company Facts
also contains later comparative differences for FY2015 Current Assets and Current
Liabilities. These examples demonstrate why neither “original always wins” nor
“latest always wins” is safe.

The Phase 1 request does not choose between an as-originally-reported and a
latest-restated analytical view. Company Facts alone does not supply complete
target-specific restatement metadata, so differing later-period evidence remains
structured and unresolved rather than guessed.

### 16.6 Annual duration and point-in-time eligibility

Revenue, Operating Income, and Interest Expense are annual duration concepts. An
observation is ordinarily eligible only when all of these conditions hold:

- `start` is present and equals the requested target fiscal-year start;
- `end` equals the requested target fiscal-year end;
- `fy` equals the target fiscal year;
- `fp` is exactly `FY`;
- `form` is an eligible ordinary `10-K`;
- `filed` is on or before the inclusive analysis cutoff;
- the exact unit key is `USD`; and
- taxonomy and concept are an approved tag for the requested normalized concept.

Current Assets and Current Liabilities are annual point-in-time concepts. An
observation is ordinarily eligible only when:

- `start` is absent;
- `end` equals the requested target fiscal-year end;
- `fy` equals the target fiscal year;
- `fp` is exactly `FY`;
- `form` is an eligible ordinary `10-K`;
- `filed` is on or before the inclusive analysis cutoff;
- the exact unit key is `USD`; and
- taxonomy and concept are an approved tag for the requested normalized concept.

For both period types, every condition is necessary. `fy` and `fp` describe the
source filing's fiscal focus; actual `start` and `end` describe the fact period.
Neither substitutes for the other. A `frame` value is retained as raw provenance
but is never required, never ranks candidates, and never proves annuality or exact
dates.

Quarterly, discrete-quarter, year-to-date, transition, shortened, extended, and
mismatched-duration facts are ineligible. Observations at another instant date are
ineligible. The request carries Microsoft's actual issuer dates, so 52/53-week
years are handled by exact start/end comparison rather than a hard-coded 365-day
count. No duration is inferred from a frame, form, label, or nearby date.

### 16.7 Unit, currency, value, and scale

The only eligible Company Facts unit key for all five concepts is the exact,
case-sensitive key:

```text
USD
```

The parser preserves provider unit keys exactly; this methodology therefore does
not infer currency or accept aliases. `usd`, `USDm`, “US dollars,” `pure`,
`shares`, percentages, counts, per-share units, and every other key are
ineligible. Currency conversion and unit conversion are unsupported.

The SEC XBRL numeric fact represents the reported full value after applicable
inline transformations. A filing or display table may present figures in
millions, but selection retains the Company Facts `val` economic amount in `USD`.
Scaling or display formatting may change a later representation only when exact
and traceable; it must not change the selected economic value. The selection layer
does no display rounding, conversion, or reconstruction.

### 16.8 Ordered Microsoft source-tag mappings

Only taxonomy `us-gaap` and the exact concept identifiers below are approved.
Labels do not authorize a mapping. Priority is applied only after all observations
within a tag tier have been evaluated and resolved under sections 16.4–16.10.

| Normalized concept | Priority | Exact source tag | Microsoft-specific accounting interpretation and evidence | Limitations and fallback |
|---|---:|---|---|---|
| Revenue | 1 | `us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax` | Revenue from satisfying customer-contract performance obligations, excluding assessed tax. Microsoft used it for current-year consolidated annual Revenue from FY2018 through FY2025. | Not approved for periods or issuers merely because its label resembles revenue. Fallback is allowed only under the tier rule below. |
| Revenue | 2 | `us-gaap:SalesRevenueNet` | Net ordinary-course goods-and-services revenue. Microsoft used it for current-year consolidated annual Revenue from FY2011 through FY2017. | The taxonomy label is deprecated as of 2018-01-31; eligibility is a narrow Microsoft historical mapping. It cannot mask an unresolved priority-1 tier. |
| Revenue | 3 | `us-gaap:Revenues` | Microsoft's current-year consolidated annual top line in FY2010. | The taxonomy meaning is broader and can include investment or interest income for some entities. It is approved only as Microsoft's last historical fallback under exact request context. No further fallback exists. |
| Current Assets | 1 | `us-gaap:AssetsCurrent` | Total assets Microsoft classifies as current at fiscal year-end; observed consistently for current-year annual facts from FY2010 through FY2025. | Instant only. No reconstruction and no fallback tag are approved. |
| Current Liabilities | 1 | `us-gaap:LiabilitiesCurrent` | Total obligations Microsoft classifies as current at fiscal year-end; observed consistently for current-year annual facts from FY2010 through FY2025. | Instant only. No reconstruction and no fallback tag are approved. |
| Operating Income | 1 | `us-gaap:OperatingIncomeLoss` | Microsoft's consolidated result after operating revenue and operating expenses; observed consistently for current-year annual facts from FY2010 through FY2025. | Duration only. Net income, pretax income, segment profit, and non-GAAP measures are not fallbacks. |
| Interest Expense | 1 | `us-gaap:InterestExpenseNonoperating` | Interest expense classified as nonoperating. Microsoft used it for the explicit consolidated Interest Expense line in its FY2025 10-K. | Duration only. Its approval is Microsoft-specific and does not approve net interest or all nonoperating expense. Fallback follows the tier rule. |
| Interest Expense | 2 | `us-gaap:InterestExpense` | Cost of borrowed funds accounted for as interest expense. Microsoft used it for the explicit consolidated Interest Expense line through its FY2024 10-K. | The taxonomy concept can include operating and nonoperating interest; eligibility rests on Microsoft's filing-specific historical use. No further fallback exists. |

For each normalized concept, a tag tier is resolved before moving to the next:

1. If the tier produces one selected economic fact, that fact controls and all
   lower-tag observations are retained as rejected alternatives with
   `lower_priority_tag`.
2. If the tier produces Invalid, Unsupported, Ambiguous, or Conflicting for
   target-context evidence, fallback is blocked. A lower tag must not hide the
   problem.
3. Fallback is permitted only when the higher tier is absent or all of its
   observations fail ordinary eligibility for non-blocking reasons such as form,
   cutoff, fiscal context, or period mismatch and no differing later-period,
   amendment, invalid, or unsupported-unit evidence makes that tier unresolved.

The approved lists are exhaustive. In particular:

- `us-gaap:SalesRevenueGoodsNet` is goods-only and materially narrower than
  Microsoft's consolidated Revenue;
- `us-gaap:InvestmentIncomeNet` is income, not expense;
- `us-gaap:NonoperatingIncomeExpense` is a broader aggregate;
- `us-gaap:FinanceLeaseInterestExpense` is only a finance-lease component;
- `us-gaap:InterestPaid` is a cash-flow fact that can include capitalized
  interest; and
- net interest, combined income/expense, finance-cost, cash-paid, and
  component-reconstructed values are not Interest Expense.

No unlisted standard tag, custom Microsoft tag, label match, netted value, or
component sum may be substituted.

### 16.9 Deterministic candidate evaluation and rank

Candidate evaluation is independent of taxonomy-object order, unit-array order,
observation-array order, retrieval order, and incidental raw JSON position. It
uses this sequence:

1. Validate the request and approved Microsoft CIK; reject a payload-company
   mismatch.
2. Validate the normalized concept and methodology version, then identify only
   its ordered `us-gaap` source tags.
3. Evaluate exact unit-key eligibility.
4. Evaluate exact filing form.
5. Apply the inclusive filed-date cutoff.
6. Evaluate target `fy` and exact annual `fp = FY`.
7. Evaluate exact duration boundaries or instant boundary and absent start.
8. Classify amendments and potential later-period restatements, including
   target-date observations rejected from ordinary selection only by later
   filing fiscal context.
9. Within each tag tier, classify exact duplicates, equivalence, value agreement,
   conflicts, and uniqueness.
10. Apply concept-tag priority across already resolved tiers.

All criteria and rejection reasons are retained even when an earlier check is
already sufficient to reject an observation. This makes ordinary fallback and
target-period unresolved evidence auditable. Filed date is an availability filter,
not a “latest” rank. Accession number identifies lineage, not priority. Retrieval
time and `frame` never rank candidates.

### 16.10 Duplicate, equivalence, ambiguity, and conflict semantics

The evidence identity of an observation consists of its:

- source taxonomy and concept;
- exact unit key and numeric value;
- `start` presence/value and `end`;
- `fy` presence/value and `fp` presence/value;
- `form`, `filed`, and `accn`; and
- `frame` presence/value.

Each raw observation and raw-artifact reference is a **candidate occurrence**.
Two occurrences are **exact duplicate evidence** when every field above is equal.
Occurrences may come from repeated array entries or separately retrieved raw
artifacts. Exact duplicates form one candidate-fact identity for decision-making,
with every occurrence, occurrence evaluation, and raw-artifact reference retained.

Ordinary eligible observations are **equivalent evidence** when taxonomy,
concept, unit, numeric value, start/end, fiscal context, form, filed date, and
accession agree. A differing or absent `frame`, repeated occurrence, or retrieval
event does not change the economic fact. The special value-agreeing 10-K/10-K/A
treatment in section 16.4 may also support the same selected economic fact, but
the original 10-K remains the sole controlling observation and the different
forms, dates, and accessions remain explicit.

Equivalent candidate facts may form one resolved candidate group and therefore
produce Selected with reason `equivalent_duplicates`. Selected still means
exactly one selected economic fact. The selected group retains every equivalent
candidate identity and occurrence rather than choosing one by response or
retrieval order. In the special 10-K/10-K/A case, the ordinary 10-K candidate is
controlling and the amendment remains rejected supporting evidence.

Equal numeric values do not by themselves prove equivalence. Equally ranked
ordinary candidates with the same value but different filing/accession context
that the rules cannot relate produce Ambiguous with
`multiple_equal_candidates`. Equally ranked ordinary candidates with different
numeric values produce Conflicting with `conflicting_values`. Numeric comparison
uses the preserved Company Facts value in the exact `USD` unit; because Company
Facts omits full source rounding metadata, any unequal values remain unequal.

Amendment and later-period disagreements are classified first as
`amendment_unresolved` or `restatement_unresolved`, not as an ordinary conflict.
No disagreement is resolved by array order, newest retrieval, newest filing,
accession sorting, averaging, minimum, maximum, sign preference, or value size.

Tag priority resolves only already-resolved tiers. A selected higher-priority tag
rejects a lower-priority alternative even when values agree; a lower tag cannot
resolve an unresolved higher tier.

### 16.11 Selection statuses and reason codes

Selection uses exactly these controlled status identifiers:

| Label | Identifier | Boundary |
|---|---|---|
| Selected | `selected` | One eligible candidate or one resolved group of equivalent candidates represents exactly one selected economic fact. All candidate and occurrence lineage is retained. |
| Unavailable | `unavailable` | The request is valid and supported, but no candidate survives ordinary eligibility, and no relevant invalid, unsupported, amendment/restatement, ambiguity, or conflict condition blocks the result. |
| Ambiguous | `ambiguous` | Two or more equally ranked, same-value candidates remain plausible but cannot be proven equivalent or reduced to one controlling observation. |
| Conflicting | `conflicting` | Two or more equally ranked ordinary eligible candidates have different values and no approved rule resolves them. |
| Unsupported | `unsupported` | The request, unit, or required treatment lies outside this policy, including unresolved amendment or restatement replacement. |
| Invalid | `invalid` | The request, company evidence, or target-relevant candidate is malformed, contradictory, or violates a validity invariant. |

Unavailable is absence after supported filtering; Unsupported is present evidence
or requested treatment the policy does not authorize; Invalid is evidence or
context that cannot be interpreted consistently. Ambiguous candidates agree in
value but not provable identity; Conflicting candidates disagree in value.
Missing is never converted to zero, and non-Selected outcomes contain no selected
value.

These are the stable Phase 1 selection reason codes:

| Reason code | Meaning and ordinary outcome effect |
|---|---|
| `company_mismatch` | Request identity is not `microsoft_corporation`, its associated CIK is not `0000789019`, or payload CIK is not `0000789019`; Invalid. |
| `invalid_request_context` | Required request context is absent, contradictory, or wrong for the concept's period type; Invalid. |
| `invalid_candidate_evidence` | Target-relevant evidence violates a required semantic validity rule and cannot be evaluated safely; Invalid. |
| `concept_unsupported` | The requested normalized concept is outside the approved five; Unsupported. |
| `methodology_version_unsupported` | The request does not name `microsoft_annual_company_facts_v1`; Unsupported by this policy. |
| `no_approved_tag_present` | None of the requested concept's approved source tags is present; Unavailable. |
| `unsupported_unit` | Target-context monetary evidence uses a key other than exact `USD`; it is rejected and, when no resolved eligible tier exists, produces Unsupported. |
| `ineligible_filing_form` | The observation is not an ordinary `10-K` or conditional `10-K/A`; it is rejected and ordinarily contributes to Unavailable. |
| `filed_after_cutoff` | `filed` is later than the inclusive cutoff; the observation is rejected before selection. |
| `fiscal_year_mismatch` | `fy` does not equal the requested target fiscal year or is absent; the observation is not an ordinary candidate. |
| `fiscal_period_mismatch` | `fp` is not exact `FY` or is absent; the observation is not an ordinary candidate. |
| `duration_mismatch` | A duration start is absent or either boundary differs from the exact requested issuer dates; the observation is rejected. |
| `instant_date_mismatch` | An instant observation has a start or its end differs from the target fiscal-year end; the observation is rejected. |
| `amendment_unresolved` | Company Facts cannot prove target-fact supersession or relate changed/sole amendment evidence safely; Unsupported. |
| `restatement_unresolved` | A cutoff-eligible later filing reports a different value for the target dates and Company Facts cannot establish the controlling value; Unsupported. |
| `no_eligible_candidate` | Approved tags were present, but all observations were rejected by supported ordinary eligibility rules; Unavailable. |
| `unique_eligible_candidate` | Exactly one controlling ordinary observation remains in the selected tier; Selected. |
| `equivalent_duplicates` | Exact duplicates, approved equivalent candidates, or a value-agreeing non-controlling amendment support one economic fact with all lineage retained; Selected, and also the rejection reason for that amendment evidence. |
| `multiple_equal_candidates` | Equally ranked same-value candidates cannot be proven equivalent; Ambiguous. |
| `conflicting_values` | Equally ranked ordinary eligible candidates have unequal values; Conflicting. |
| `lower_priority_tag` | An otherwise usable lower-tag candidate is rejected because an already-resolved higher tag controls; informational within the final rationale. |

A candidate can retain multiple rejection reasons. For a candidate, an applicable
`amendment_unresolved` or `restatement_unresolved` classification takes precedence
over ordinary filter reasons because it governs whether target-period evidence
can be used. Otherwise, the first failed check in section 16.9 is the candidate's
primary reason; later failures remain contributing reasons.

The final outcome uses the first applicable reason in this complete linear order:

1. `company_mismatch`;
2. `invalid_request_context`;
3. `invalid_candidate_evidence`;
4. `concept_unsupported`;
5. `methodology_version_unsupported`;
6. `amendment_unresolved`;
7. `restatement_unresolved`;
8. `unsupported_unit`;
9. `conflicting_values`;
10. `multiple_equal_candidates`;
11. `equivalent_duplicates` when the selected tier grouped equivalent eligible
    candidates or retained a value-agreeing amendment;
12. `unique_eligible_candidate`;
13. `no_approved_tag_present` when no approved tag exists;
14. the shared ordinary primary rejection reason when every target-relevant
    candidate has that same primary reason; or
15. `no_eligible_candidate`.

This precedence is applied only to target-relevant evidence in the controlling
tier. A rejected unrelated observation does not override a uniquely resolved
higher-priority tier. Invalid, another blocking Unsupported condition, or
unresolved amendment/restatement treatment blocks fallback; ordinary equal-rank
disagreement is then Conflicting or Ambiguous; a resolved tier is Selected; and
an exhausted supported search is Unavailable. `lower_priority_tag` is never a
primary outcome reason. An unsupported unit blocks only when it is target-context
evidence in the controlling unresolved tier, not merely an unrelated observation.

### 16.12 Selection rationale and provenance

Every outcome, including Unavailable, must retain or reference:

- requested stable Microsoft identity `microsoft_corporation` and canonical CIK;
- normalized concept;
- target fiscal year, applicable target start, and target end;
- date-only analysis cutoff;
- methodology version `microsoft_annual_company_facts_v1`;
- every approved-tag candidate actually considered, including duplicates and
  candidates filed after cutoff;
- each candidate's taxonomy, exact concept, unit key, value, `accn`, `form`,
  `filed`, `fy`, `fp`, `start`, `end`, and `frame`, preserving absence;
- each eligibility check, acceptance or rejection, stable reason code, and source
  tag tier;
- the selected candidate or resolved candidate group and selected source tag when
  Selected;
- every rejected lower-priority or otherwise ineligible alternative;
- every unresolved candidate when non-Selected;
- amendment and later-period/restatement classification and the evidence retained
  for it; and
- the originating `SecRawArtifact` source, retrieval timestamp, content digest,
  and exact-payload provenance reference.

The selected normalized fact must remain traceable to the exact SEC observation
and raw artifact. Retrieval metadata does not become filing metadata. This
methodology does not prescribe database keys, persistence identifiers, serialized
field names, or a storage schema.

### 16.13 Methodology version governance

`microsoft_annual_company_facts_v1` is a stable repository-controlled semantic
identifier, not a display title. Reformatting prose without changing meaning does
not require a new identifier. A material change to any of the following does:

- approved tag membership or priority;
- company, form, unit, fiscal-context, duration, or instant eligibility;
- analysis-cutoff comparison or date semantics;
- amendment or restatement treatment;
- duplicate, equivalence, ambiguity, conflict, or fallback resolution; or
- the economic meaning of a selected concept.

A new version must be approved and documented before later code can emit outcomes
under the changed rules. Historical outputs retain the version that governed
their decision.

### 16.14 Explicit limitations

This policy is limited to:

- Microsoft Corporation, stable identifier `microsoft_corporation`, and canonical
  SEC CIK `0000789019`;
- SEC Company Facts standard-taxonomy, entity-wide evidence;
- consolidated annual `10-K` context, with `10-K/A` only under the conservative
  amendment rule;
- exact `USD` monetary facts;
- Revenue, Current Assets, Current Liabilities, Operating Income, and Interest
  Expense; and
- one requested fiscal year and date-only cutoff at a time.

It does not support:

- another company or a generalized company registry;
- segment, dimensional, subsidiary, unconsolidated, or custom-extension facts;
- quarterly, year-to-date, transition, trailing-twelve-month, or reconstructed
  annual facts;
- non-USD facts, unit aliases, currency conversion, or FX assumptions;
- totals reconstructed from components;
- net interest, combined finance costs, cash interest, or inferred source-tag
  equivalence;
- a broad amendment or restatement engine or a choice between original and
  latest-restated analytical views;
- inference from entity name, ticker, labels, `frame`, accession ordering, filing
  recency, retrieval time, response order, or JSON position;
- a guarantee that Company Facts alone resolves every filing ambiguity;
- metric calculation, risk analysis, persistence, API, or presentation behavior;
  or
- any claim that selection, normalization, or Phase 1 roadmap work is complete.

An unsupported future Microsoft tag or filing treatment requires a new approved
methodology version; it must not be absorbed by an undocumented fallback.

## 17. Future methodologies

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
