# Project Roadmap

This is the sole source of project sequencing, dependencies, active phase,
progress, and phase exit criteria. Other documents may describe milestone meaning
but must not maintain competing status lists.

## Status legend

- `[ ]` Not started
- `[-]` In progress
- `[x]` Completed
- `[!]` Blocked or awaiting a decision

## Milestone definitions

- **Phase 0 Foundation:** repository governance, baseline product and technical
  documentation, Python project configuration, local quality tooling, and GitHub
  foundation. No production financial-analysis logic belongs in this phase.
- **Phase 1 Microsoft Vertical Slice:** the first bounded end-to-end analytical
  workflow using Microsoft annual SEC data, narrow deterministic fact selection,
  three initial metrics, and a minimal Python-facing result interface.
- **Portfolio-Ready Release:** the later release that satisfies the product-level
  analysis, explainability, reproducibility, interface, and presentation criteria
  in `docs/product-requirements.md`.

## Active phase

**Phase 0 — Foundation**

Foundation documentation and repository scaffolding exist. Production analysis
code has not been implemented. Empty or placeholder configuration and methodology
files do not count as completed deliverables.

---

# Phase 0 — Foundation

## 0.1 Local repository

- [x] Create the local project directory and initialize Git
- [x] Set the default branch to `main`
- [x] Confirm Python 3.12 and create a local virtual environment
- [x] Create the initial repository structure
- [x] Add an initial `.gitignore`

## 0.2 Foundational documentation

- [x] Define the product scope and milestone acceptance criteria
- [x] Create a concise newcomer-facing README
- [x] Establish the roadmap and milestone terminology
- [x] Establish permanent repository-wide agent rules
- [x] Establish the execution-plan standard
- [x] Define document ownership and authority
- [x] Distinguish provider payloads, preserved raw responses, and test fixtures
- [ ] Define the initial system architecture and data flow
- [ ] Define the financial-methodology framework
- [ ] Define raw, normalized, and analytical data contracts
- [ ] Define the initial data dictionary
- [ ] Define the explainable risk-model framework
- [ ] Define ADR conventions
- [ ] Define the changelog convention
- [ ] Select and document the project license

## 0.3 Python project configuration

- [ ] Configure `pyproject.toml` and package metadata
- [ ] Approve only dependencies required for Phase 0 tooling
- [ ] Configure Ruff
- [ ] Configure mypy
- [ ] Configure pytest and coverage
- [ ] Add an initial package smoke test
- [ ] Verify editable local installation
- [ ] Document and verify supported local commands

No setup or quality command is considered supported until configuration exists and
the command has been run successfully.

## 0.4 GitHub foundation

- [ ] Create and connect the GitHub repository
- [ ] Add issue and pull-request templates
- [ ] Add continuous integration for supported checks
- [ ] Add appropriate repository security safeguards
- [ ] Configure branch protection when useful
- [ ] Verify CI from the connected repository

## Phase 0 exit criteria

Phase 0 is complete when:

- foundational documents exist, have clear ownership, and are internally consistent;
- architecture, methodology, and initial contracts are sufficient to constrain
  Phase 1 safely;
- the Python package can be installed using documented instructions;
- documented lint, format, type, test, and coverage commands pass;
- CI runs the supported checks;
- the repository is connected to GitHub with basic collaboration templates;
- technology dependencies are justified and recorded; and
- no production financial-analysis logic has been implemented prematurely.

---

# Phase 1 — Microsoft Vertical Slice

Phase 1 begins only after Phase 0 exit criteria are met. It analyzes Microsoft
Corporation using annual SEC Company Facts data and a controlled offline fixture.

## 1.1 Approved scope and contracts

- [ ] Create an approved issue and execution plan
- [ ] Define Microsoft’s stable internal identifier and CIK resolution behavior
- [ ] Define typed contracts for provider, raw, normalized, and metric results
- [ ] Define the five required normalized concepts: revenue, current assets,
  current liabilities, operating income, and interest expense
- [ ] Define calculation and data-quality statuses and reason codes
- [ ] Define fixture provenance and sanitization records
- [ ] Confirm acceptance criteria and the Phase 1 stopping condition

## 1.2 Narrow deterministic fact-selection policy

This policy is a prerequisite for Phase 1 normalization and metric calculation. It
is limited to Microsoft annual data and must be documented in the methodology and
data contracts before normalizer implementation.

- [ ] Restrict eligible facts to the approved Microsoft identifier, consolidated
  annual reporting scope, approved 10-K filing forms, and supported USD units
- [ ] Define concept-specific ordered XBRL tag mappings for the five concepts
- [ ] Define exact annual duration and point-in-time period matching
- [ ] Define filing-date and analysis-cutoff rules that prevent look-ahead bias
- [ ] Define treatment of duplicates, amendments, restatements, and conflicting facts
- [ ] Require deterministic selection rationale and retained source provenance
- [ ] Return an explicit unavailable or ambiguous result when no unique eligible
  fact can be selected; never resolve ambiguity by incidental response order
- [ ] Add focused tests for every selection and ambiguity rule

The broader reusable policy for multiple companies, alternative tags, and wider
filing variation remains a Phase 2 deliverable.

## 1.3 SEC Company Facts access

- [ ] Implement a provider-specific client with compliant identification
- [ ] Add explicit timeout and bounded retry behavior
- [ ] Validate responses and represent provider failures deliberately
- [ ] Preserve retrieval source and timestamp
- [ ] Keep default tests offline with a sanitized committed fixture
- [ ] Keep any live integration check optional and separate

## 1.4 Raw responses and fixtures

- [ ] Preserve original provider payloads as immutable local raw responses when
  live retrieval is performed
- [ ] Keep locally preserved raw responses separate from normalized data
- [ ] Commit only a reviewed sanitized fixture needed for deterministic tests
- [ ] Record fixture origin, retrieval context, and sanitization
- [ ] Ensure secrets and personal provider-identification values are absent

## 1.5 Normalization and initial metrics

- [ ] Implement normalization only after the Phase 1 fact-selection policy is
  approved and tested
- [ ] Preserve company, concept, source tag, filing, period, unit, currency,
  accession, amendment, selection rationale, and retrieval provenance
- [ ] Implement revenue growth
- [ ] Implement current ratio
- [ ] Implement interest coverage
- [ ] Document each formula, input, period rule, exceptional behavior,
  interpretation, limitation, and manually verified example
- [ ] Add deterministic tests for normal, missing, invalid, zero-denominator,
  mismatch, and boundary behavior as applicable

## 1.6 Minimal result interface

- [ ] Expose typed results through a minimal Python-facing interface
- [ ] Include value, status, source period, provenance reference, and reason code
- [ ] Avoid API, dashboard, database, peer, FRED, risk-score, and bulk-company work

## Phase 1 exit criteria

Phase 1 is complete when:

- Microsoft annual facts can be loaded from a controlled fixture and optionally
  retrieved through the isolated SEC client;
- the narrow fact-selection policy is documented, deterministic, and tested;
- the five required concepts are normalized with provenance;
- revenue growth, current ratio, and interest coverage are documented and tested;
- missing, invalid, mismatched, and ambiguous data are explicit;
- default tests require no live network access;
- typed metric results are available through the minimal interface; and
- the approved plan and stopping condition were respected.

---

# Phase 2 — Reusable Financial Data Foundation

Goal: generalize the vertical slice into reusable company, normalization,
fact-selection, and persistence foundations.

- [ ] Define a stable company registry and identifier model
- [ ] Expand normalized concepts required by later metrics
- [ ] Generalize fact selection across companies, tags, amendments, periods, scopes,
  currencies, units, and restatements
- [ ] Add cross-company ambiguity and reconciliation tests
- [ ] Design persistence boundaries and migrations only after approval
- [ ] Keep persistence separate from calculation logic

Exit: reusable contracts support multiple companies, selection remains deterministic,
and provenance is queryable without weakening Phase 1 behavior.

# Phase 3 — Financial Statement Analysis

Goal: implement the documented metric set and multi-period trends.

- [ ] Add approved growth, profitability, liquidity, leverage, debt-service, and
  cash-flow metrics
- [ ] Add data-quality-aware multi-period trend analysis
- [ ] Document and manually verify every formula
- [ ] Enforce scope, period, currency, unit, and exceptional-value behavior

Exit: core metrics and trends are reproducible, tested, documented, and traceable.

# Phase 4 — Explainable Financial Health Score

Goal: create a deterministic internal analytical score without implying an official
credit rating.

- [ ] Approve components, transformations, weights, thresholds, and missing-input
  behavior
- [ ] Expose contributions, completeness, data quality, and reason codes
- [ ] Validate boundaries, reproducibility, monotonicity where expected, and
  limitations

Exit: every score contribution is explainable and traceable to normalized inputs.

# Phase 5 — Distress Indicators and Risk Flags

Goal: add selected distress models and deterministic analytical flags.

- [ ] Select and document applicable Altman and Piotroski variants
- [ ] Implement criterion-level tests and explanations
- [ ] Add approved liquidity, leverage, coverage, cash-flow, trend, and data-quality
  flags

Exit: models and flags are tested, traceable, and explicit about applicability.

# Phase 6 — Macroeconomic Data and Stress Testing

Goal: add reproducible, versioned scenarios using approved company and macroeconomic
inputs.

- [ ] Integrate only required official macroeconomic series
- [ ] Define scenario contracts, assumptions, baseline preservation, and limitations
- [ ] Implement downside, sensitivity, and breakeven analysis as approved
- [ ] Explain changes in metrics, score components, categories, and flags

Exit: baseline and stressed results are comparable, reproducible, and not presented
as forecasts.

# Phase 7 — Peer and Sector Analysis

Goal: compare companies within documented and defensible peer groups.

- [ ] Define peer-selection criteria, data sources, minimum group size, and analyst
  judgment disclosures before choosing companies
- [ ] Expand company support according to that methodology
- [ ] Add peer medians, percentiles, rankings, and material-deviation analysis
- [ ] Add reproducible SQL analytics where they serve the approved analysis

Exit: every peer group and relative conclusion is documented and reproducible.
Supporting several unrelated companies alone does not satisfy this phase.

# Phase 8 — API

Goal: expose approved analytical outputs through a typed application API.

- [ ] Add the API only after domain contracts are stable
- [ ] Define versioned requests, responses, validation, and structured errors
- [ ] Add endpoint tests without duplicating business logic

Exit: supported analytical workflows are available through documented typed
contracts and safe error behavior.

# Phase 9 — Interactive Dashboard

Goal: provide an analyst-facing interface over curated application outputs.

- [ ] Define user workflows before page structure
- [ ] Present analysis, provenance, data quality, limitations, and unavailable states
- [ ] Keep formulas, thresholds, and provider parsing outside the interface

Exit: supported workflows are interactive, reproducible, and explainable.

# Phase 10 — Executive Reporting

Goal: create a separate Power BI deliverable over curated analytical data.

- [ ] Define the analytical model, measures, refresh expectations, and reconciliation
- [ ] Build executive views consistent with Python-calculated results
- [ ] Document decisions and provide suitable demonstration assets

Exit: reporting is reconciled, documented, and suitable for portfolio presentation.

# Phase 11 — Portfolio-Ready Release

Goal: satisfy the portfolio-ready product criteria and publish a reproducible,
reviewed demonstration.

- [ ] Audit financial correctness, provenance, security, dependencies, tests, and
  documentation consistency
- [ ] Reproduce setup and supported workflows from a clean environment
- [ ] Add final diagrams, screenshots, known limitations, and demonstration guidance
- [ ] Verify CI, licensing, sample-data provenance, and repository hygiene
- [ ] Prepare concise recruiter and technical walkthroughs

Exit: every Portfolio-Ready Release criterion in `docs/product-requirements.md` is
met and evidenced.

## Deferred beyond the portfolio-ready release

- Quarterly and trailing-twelve-month analysis
- Additional jurisdictions and accounting standards
- Automated schedulers and complex orchestration
- Cloud and Kubernetes deployment
- Black-box primary risk models
- Probability-of-default and rating-transition research
- Bond-spread and portfolio-level credit analysis
- Monte Carlo simulation
- Mobile, brokerage, and trading functionality

Deferred work requires fresh product, methodology, architecture, and roadmap review.
