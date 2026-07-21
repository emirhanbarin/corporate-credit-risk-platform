# Product Requirements Document

## 1. Product

### Name

Corporate Credit Risk & Financial Health Platform

### Summary

The product is an explainable financial analytics platform for evaluating the
financial performance, credit risk, and stress resilience of publicly listed
companies using authoritative public data.

It is also a professional portfolio project demonstrating finance, credit-risk,
data-analysis, and software-engineering practice. Product behavior must remain
useful to an analyst even when portfolio presentation is a secondary goal.

## 2. Problem

Public-company financial data is available but difficult to turn into consistent,
decision-useful analysis:

- equivalent concepts can be reported under different source tags;
- facts can conflict across filings, amendments, scopes, and periods;
- missing values are often mistaken for zero;
- annual, quarterly, point-in-time, and duration data can be mixed incorrectly;
- ratios can ignore currency, unit, or denominator problems;
- risk outputs can conceal their inputs and rules; and
- attractive dashboards can obscure weak methodology and provenance.

The product must address these problems through controlled normalization,
documented calculations, explicit data-quality outcomes, traceable conclusions,
and reproducible analysis.

## 3. Users and audiences

### Product users

The primary product user is an analyst or learner who wants to examine a supported
public company and understand its financial condition, major credit-risk signals,
and data limitations.

Representative users include:

- finance and credit-risk analysts;
- financial-data and risk analysts;
- corporate-finance students; and
- developers studying explainable financial-data systems.

### Portfolio audience

Recruiters, interviewers, and reviewers are an important audience for the
repository and demonstration assets, but they are not substitutes for the product
user. Portfolio presentation must show credible analytical work rather than drive
financial or architecture decisions.

## 4. User outcomes

For a supported company, a user should be able to understand:

- which company and reporting period are being analyzed;
- which source facts were used and why they were selected;
- how revenue, profitability, liquidity, leverage, debt service, and cash flow have
  changed where supported;
- which inputs, formulas, and rules produced each metric or risk conclusion;
- which data is missing, invalid, inconsistent, ambiguous, or unsupported;
- which factors contribute most to the internal financial-health assessment;
- how the company compares with a documented peer group when peer analysis exists;
  and
- how explicit downside assumptions change supported analytical results when stress
  analysis exists.

## 5. Scope and milestones

### Product scope

The core product focuses on publicly listed United States companies that file with
the Securities and Exchange Commission. Initial analysis uses annual 10-K data.
Quarterly and trailing-twelve-month analysis are outside the initial scope.

Official public sources are preferred. SEC data is the initial company-financial
source. Federal Reserve Economic Data may support later approved macroeconomic
analysis.

### Milestone terms

- **Phase 0 Foundation** establishes governance, documentation, architecture,
  configuration, and quality foundations without production financial-analysis
  logic.
- **Phase 1 Microsoft Vertical Slice** delivers the first bounded end-to-end
  analytical workflow for Microsoft annual SEC data.
- **Portfolio-Ready Release** is the later release that satisfies the complete
  success criteria in section 12.

`ROADMAP.md` alone owns milestone sequencing, current phase, and progress.

## 6. Core product requirements

### 6.1 Company identity

The product must:

- use a stable internal company identity;
- resolve or associate source identifiers such as SEC CIK values;
- preserve company name and ticker as descriptive attributes; and
- avoid treating a ticker symbol as the only permanent identity.

### 6.2 Source ingestion and provenance

The product must:

- retrieve approved data from authoritative sources;
- comply with applicable source identification and access requirements;
- preserve retrieval context and source identity;
- isolate provider-specific behavior from financial analysis; and
- represent unavailable, malformed, or failed retrievals explicitly.

Every material analytical result must be traceable to relevant company, source,
concept, filing or series, reporting period, retrieval, unit, currency, and
amendment information where applicable.

### 6.3 Source-data forms

The product distinguishes:

- an **original provider payload**, received before project transformation;
- a **locally preserved raw response**, which is an immutable local copy of the
  payload with retrieval metadata and remains separate from processed data; and
- a **sanitized committed test fixture**, which is a reviewed, reduced or redacted
  representation for deterministic tests and is not described as the original
  payload.

Fixture origin and sanitization must be documented. Sanitization must retain the
behavior being tested. Secrets and personal provider-identification values must not
be committed.

### 6.4 Normalized financial facts

The product must map provider facts into controlled internal concepts while
preserving their source identity and selection rationale.

Selection must be deterministic. Duplicate, conflicting, amended, restated,
differently scoped, or otherwise ambiguous facts must not be resolved silently.
When a supported rule cannot select one eligible fact, the result must communicate
unavailability or ambiguity.

The controlled concept set may expand as approved metrics require it. Detailed
field definitions and selection semantics belong in the data-contract,
data-dictionary, and financial-methodology documents.

### 6.5 Financial analysis

Subject to approved methodology and roadmap phases, the product is intended to
support:

- growth and profitability;
- liquidity and working capital;
- leverage and debt-service capacity;
- operating and free cash flow; and
- multi-period trends.

Each metric must have a documented business meaning, formula, required inputs,
period and accounting-scope rules, currency and unit behavior, exceptional and
missing-data behavior, interpretation, limitations, and a manually verified
example.

### 6.6 Explainable financial-health analysis

The product may produce a deterministic internal Financial Health Score covering
approved dimensions such as liquidity, leverage, debt service, profitability,
cash-flow quality, and stability.

The user must be able to inspect the inputs, transformations or thresholds,
weights, contributions, data quality, completeness, and explanations. The score is
an internal analytical output and must not be presented as an official credit
rating.

### 6.7 Distress indicators and risk flags

Selected distress indicators may be added only with an exact documented variant,
required inputs, applicability, limitations, and missing-data behavior. Different
model variants must not be interchanged.

Risk flags must use explicit rules and expose the triggering metric, relevant
threshold, actual value, period, data quality, and explanation.

### 6.8 Stress analysis

Later approved versions may evaluate base and downside assumptions affecting
revenue, margins, financing costs, capital expenditure, working capital, cash flow,
coverage, leverage, and internal risk outcomes.

Assumptions, baseline period, scenario version, inputs, outputs, and limitations
must be visible and reproducible. Scenario results must not be represented as
forecasts.

### 6.9 Peer analysis

Peer comparison requires a documented selection methodology, source, minimum group
size, supported metrics, missing-data behavior, and disclosure of analyst judgment.
Supporting several unrelated companies does not make them one peer group.

When implemented, peer analysis may provide medians, percentiles, rankings, and
material-deviation indicators with traceable inputs.

### 6.10 Interfaces

Financial and risk logic must be reusable independently of any presentation layer.
Later approved interfaces may include a typed API, an interactive analytical
application, and a separate executive reporting deliverable.

Interfaces must consume curated analytical outputs, preserve data-quality states,
avoid duplicating formulas, and not expose secrets or raw internal errors. Specific
endpoint and page designs belong to later approved requirements and architecture.

## 7. Data quality requirements

The product must distinguish, where applicable:

- zero;
- missing;
- unavailable;
- invalid;
- not applicable;
- inconsistent;
- unsupported; and
- estimated, if estimation is later approved.

It must detect or prevent unsupported combinations of company, scope, period,
filing, currency, unit, and concept. Division by zero, duplicate and conflicting
facts, amendments, and incomplete inputs require deliberate outcomes rather than
accidental exceptions or silent coercion.

## 8. Explainability and reproducibility

Every material output should be traceable through:

1. provider and source fact;
2. normalized concept and selection rationale;
3. validated calculation inputs;
4. formula, rule, or scenario assumption;
5. result and data-quality status; and
6. interpretation or reason code.

Given the same versioned inputs and methodology, the product should reproduce the
same result. Historical analysis must avoid using information unavailable at the
applicable analysis cutoff.

## 9. Verification outcomes

Automated tests must provide confidence proportionate to financial and data risk.
They must cover normal and material exceptional behavior, including missing or
invalid inputs, denominator cases, boundary rules, mismatches, selection ambiguity,
and provider failures when applicable.

Financial examples require at least one independent manual verification. Normal
tests must use controlled fixtures or mocks and must not require live network
access. Defects should receive regression coverage when practical.

## 10. Security and privacy outcomes

The initial product uses public company and macroeconomic data only. The repository
must not expose credentials, access tokens, database passwords, private contact
details, private financial or company data, or production connection information.

External and user-provided inputs must be validated. Secrets must be supplied
through an approved configuration mechanism and must not appear in logs, fixtures,
or committed files.

## 11. Phase 1 Microsoft Vertical Slice acceptance

The Phase 1 Microsoft Vertical Slice is accepted when:

1. Microsoft is associated with a stable internal identifier and SEC CIK.
2. Annual SEC Company Facts data can be loaded from a documented sanitized fixture;
   optional live retrieval remains separate from default tests.
3. Any live response can be preserved locally as an immutable raw response without
   treating it as a committed fixture.
4. A narrow Microsoft-specific policy deterministically selects revenue, current
   assets, current liabilities, operating income, and interest expense.
5. Selection handles tag priority, annual period alignment, analysis cutoff,
   duplicates, amendments, restatements, conflicts, currency, unit, and ambiguity
   according to documented rules.
6. The system calculates revenue growth, current ratio, and interest coverage using
   approved methodology.
7. Missing, invalid, mismatched, zero-denominator, and ambiguous inputs produce
   explicit typed outcomes.
8. Results expose value or status, source period, provenance, and reason code
   through a minimal Python-facing interface.
9. Deterministic offline tests and manually verified calculation examples pass.
10. Methodology, mappings, contracts, fixture provenance, and limitations are
    synchronized with the implementation.

Phase 1 excludes peer analysis, FRED integration, PostgreSQL, an API, dashboards,
the full Financial Health Score, bulk ingestion, machine learning, and Power BI.

## 12. Portfolio-Ready Release criteria

The product is portfolio-ready when:

- a new user can reproduce supported setup and workflows from documented commands;
- supported companies and periods are explicit;
- financial calculations are tested, manually verified, and documented;
- source provenance and selection rationale are visible;
- missing, inconsistent, ambiguous, and unsupported data are explicit;
- the internal financial-health analysis is operational and explainable;
- approved distress indicators and risk flags expose their limitations;
- at least three documented stress scenarios are reproducible;
- peer conclusions use defensible documented peer groups;
- supported API and interactive workflows operate on reproducible sample data;
- executive reporting, if included, reconciles to curated analytical outputs;
- CI passes the documented checks;
- licensing and sample-data provenance are documented;
- the repository contains no secrets or inappropriate large data dumps;
- limitations are prominent; and
- an analyst or reviewer can understand the product without reading all source code.

## 13. Non-goals

The product does not:

- provide investment, lending, accounting, legal, or regulatory advice;
- recommend buying or selling securities;
- produce official credit ratings or replace professional underwriting;
- connect to brokerage accounts or execute trades;
- process private banking data in the initial scope;
- predict short-term stock prices;
- use black-box machine learning as the primary risk method;
- scrape a source when a suitable official interface is available;
- support every filing type, company, jurisdiction, or accounting standard;
- treat arbitrary supported companies as a valid peer group;
- require quarterly or trailing-twelve-month analysis initially;
- require mobile applications, complex orchestration, Kubernetes, or production
  cloud deployment before the local product is validated; or
- automate publication before correctness and reproducibility are established.

Potential expansions require product, methodology, architecture, and roadmap review
before entering scope.
