# System Architecture

## 1. Purpose and scope

This document defines technical boundaries and dependency rules for the Corporate Credit Risk & Financial Health Platform. It constrains implementation; it does not claim that the described components already exist.

The repository currently contains foundation documentation and minimal Python package scaffolding. `ROADMAP.md` remains authoritative for phase status and progress.

The architecture supports incremental delivery from the Phase 1 Microsoft vertical slice toward later approved capabilities while protecting financial correctness, provenance, explainability, and reproducibility.

It does not define product acceptance, financial formulas, concept mappings, thresholds, score weights, detailed fields, serialized contracts, or interface designs. Those belong to the authoritative documents linked in section 19.

## 2. Architectural style and rationale

The platform uses a **modular monolith**: one Python codebase with explicit modules and enforced inward dependency direction.

This style keeps the initial workflow simple to run and test, avoids premature distributed-system failure modes, and lets pure financial logic evolve separately from infrastructure. It also preserves replaceable boundaries for later storage and interfaces without sacrificing end-to-end provenance.

Modules are responsibility boundaries, not merely folders. They interact through explicit domain types, application contracts, or ports. Convenience must not collapse ingestion, normalization, calculation, and presentation into one module.

Splitting the system into services requires a later approved need and an Architecture Decision Record (ADR). The default remains a modular monolith.

## 3. High-level system context

```text
SEC Company Facts / sanitized fixtures
                  |
                  v
      source and raw-data adapters
                  |
                  v
 validation -> normalization -> financial domain
                  |                    |
                  v                    v
       application services -> curated results
                                      |
                         future adapters only
                    persistence / API / presentation
```

In Phase 1, the only external source boundary is SEC Company Facts. A sanitized local fixture supplies the default offline path. Optional live retrieval uses the same downstream flow but remains separate from default tests.

Provider payloads never flow directly to calculation, risk logic, an API, or a dashboard.

## 4. Layer responsibilities

### 4.1 External source clients

Clients own provider-specific access: requests, compliant identification, timeouts, bounded retries, response capture, and transport-failure mapping. They return payloads and retrieval context. They never select facts, normalize concepts, calculate ratios, or interpret results.

### 4.2 Raw response preservation

The raw-data adapter preserves a live original payload plus retrieval metadata as an immutable local response. It owns safe naming, atomic writes, integrity metadata, and separation from processed outputs. It never validates financial meaning or rewrites payloads.

### 4.3 Validation

Validation checks supported shape, required metadata, primitive types, and basic invariants. It returns explicit success or structured failure without selecting accounting concepts or silently coercing absent, malformed, or unsupported data.

### 4.4 Financial fact normalization

Normalization maps validated provider facts to controlled, provider-independent concepts. It applies approved fact-selection policy and retains source facts, selection rationale, period, filing, unit, currency, and retrieval provenance.

Ambiguity, conflict, or no eligible fact produces a structured outcome. Incidental provider response order is never a selection rule.

### 4.5 Financial metric calculation

Calculators consume validated normalized facts and return deterministic typed results. They are side-effect free where practical and expose input references, status, reason code, source period, and provenance links.

They do not use HTTP, parse SEC payloads, read configuration, persist records, or format presentation output.

### 4.6 Risk and scenario analysis

When approved, these modules consume validated domain inputs and calculated metrics. They own deterministic analytical rules, versioned assumptions, contributions, and explanations—not source selection or presentation. They are future boundaries outside Phase 1.

### 4.7 Persistence

Persistence adapters implement application-owned ports. They may translate storage representations but never decide financial meaning, repair invalid records, or calculate results. Phase 1 has no production-like persistence implementation.

### 4.8 Application services

Application services coordinate use cases: obtain input, request preservation, validate, normalize, calculate, and assemble a curated result. They own sequencing, not financial formulas, provider parsing, or fact-selection policy.

The Phase 1 typed Python-facing interface belongs here and returns analytical outcomes rather than transport, database, or presentation objects.

### 4.9 API and presentation

Future API and presentation adapters translate curated application results. They preserve data quality, provenance, limitations, and structured errors. They never calculate formulas, apply thresholds, choose facts, reinterpret missing values, or conceal contradictory outcomes.

## 5. Dependency direction and forbidden dependencies

Dependencies point inward:

```text
presentation/API/persistence/source adapters
                    -> application services
                    -> domain and domain contracts
```

Validation and normalization may depend on provider-independent domain contracts. Provider parsing may depend on transport-neutral ingestion contracts. The domain uses only the Python standard library unless a later approved decision establishes a narrow dependency.

Forbidden dependencies include:

- domain logic importing HTTP clients, database drivers, SQLAlchemy, FastAPI, or Streamlit;
- calculators importing SEC schemas, filesystem adapters, or configuration;
- source clients importing calculators, risk rules, or presentation models;
- normalization importing API, dashboard, or persistence implementations;
- application services embedding formulas, thresholds, or selection policy;
- persistence models entering pure business rules; and
- dashboards or reports calculating, correcting, or inferring financial values.

Circular imports across architecture modules are prohibited. Shared types must have a clear owner rather than a generic dumping ground.

## 6. Proposed Python package structure

This target structure is not the current repository state:

```text
src/credit_risk_platform/
  domain/
    company.py              # stable identity and source identifiers
    provenance.py           # trace references and lineage
    data_quality.py         # statuses and reason-code concepts
    financial_facts.py      # normalized fact domain types
    metrics.py              # pure financial calculations
    risk.py                 # future risk boundary
    scenarios.py            # future scenario boundary
  ingestion/
    contracts.py            # transport-neutral source outcomes
    sec_company_facts.py    # SEC-specific client and parsing
  raw_data/
    contracts.py            # preservation metadata and port
    local_store.py          # local immutable-response adapter
  validation/
    provider_payloads.py    # structural validation
  normalization/
    company_facts.py        # provider facts to controlled concepts
    selection.py            # deterministic selection policy
  application/
    ports.py                # infrastructure-facing protocols
    services.py             # use-case orchestration
    results.py              # curated Python-facing results
  persistence/              # future adapters only
  interfaces/
    api/                    # future API adapter only
    presentation/           # future UI/reporting adapters only
```

Tests should mirror these boundaries. Exact names and contract shapes require approval in implementation plans and data-contract documents; responsibility and dependency direction are the binding decisions.

## 7. Phase 1 data flow

1. An application service receives Microsoft identity, an analysis cutoff, and a sanitized fixture reference or optional live request.
2. The fixture loader reads a reviewed fixture, or the SEC client retrieves an original Company Facts payload with retrieval context.
3. For live retrieval only, the service asks the raw-data port to preserve an immutable local response before transformation.
4. Validation checks the envelope and required structures; unsafe input returns a typed failure.
5. SEC-specific parsing exposes candidate source facts without interpreting or calculating them.
6. Normalization applies approved Microsoft-specific eligibility and selection rules to the five Phase 1 concepts.
7. Each outcome retains source provenance and rationale or explicitly explains why a value is unavailable.
8. Pure calculators consume only compatible normalized facts for the three Phase 1 metrics.
9. The service returns typed results with value or status, source period, reason code, and provenance references.
10. The Python-facing caller receives curated results; no database, API, dashboard, or report participates.

The same versioned fixture, policy, inputs, and cutoff must reproduce the same outcomes. Default operation and tests require no live network access.

## 8. Core domain concepts

- `CompanyIdentity`: stable internal identity and source identifiers; ticker and name are descriptive rather than sole identity.
- `ReportingPeriod`: annual duration or point-in-time context, distinct from filing, observation, retrieval, and analysis-cutoff dates.
- `SourceFact`: immutable provider fact with SEC identity and provenance.
- `NormalizedFact`: controlled concept, selected fact, rationale, scope, unit, currency, period, and quality status.
- `MetricResult`: value-or-status outcome with inputs, period, reason code, methodology identifier, and provenance references.
- `DataQualityStatus`: explicit missing, unavailable, invalid, not applicable, inconsistent, unsupported, and ambiguous states where relevant.
- `ProvenanceReference`: lineage from a result to retrieval and source facts without infrastructure objects entering the domain.

Zero is a numeric value, never a synonym for missing or unavailable. Estimated values require explicit future approval and labeling. Detailed risk and scenario concepts remain future methodology decisions.

## 9. Source-data form distinctions

**Original provider payload:** the response received before project transformation. It exists at the source boundary in provider-specific form.

**Locally preserved raw response:** an immutable local copy of the original payload plus retrieval metadata. It stays separate from normalized and calculated data, is never edited to make processing succeed, and is not assumed Git-safe.

**Sanitized committed test fixture:** a reviewed copy that may be reduced or redacted for deterministic tests. It records origin and sanitization, preserves the behavior under test, contains no secrets or personal provider-identification data, and is never represented as the original payload.

These forms use separate paths and metadata. A fixture never overwrites or masquerades as a preserved live response.

## 10. Configuration boundaries

Configuration supplies operational choices such as the separate SEC data and
hosted-files base authorities, provider-identification value, timeout, bounded
retry settings, raw-data path, fixture path, and logging level when implemented.

Formulas, mappings, eligibility rules, thresholds, weights, supported scopes, and
missing-data behavior are versioned methodology or domain decisions, not
environment variables or UI controls.

Outer layers load and validate configuration once, then pass it explicitly to
adapters or application assembly. Domain modules do not read the environment.
Secrets and sensitive values never enter logs or committed files.

## 11. Error-handling approach

Expected failures are typed at the layer that understands them:

- source access: timeout, rate limit, unavailable, or malformed response;
- raw preservation: safe, actionable storage failure;
- validation: structural or invariant violation;
- normalization: missing, unsupported, inconsistent, or ambiguous fact;
- calculation: invalid input, mismatch, or denominator condition; and
- future interfaces: safe translation of curated failures.

Exceptions are for programming defects or unrecoverable infrastructure conditions
and are mapped at an application boundary. Broad exceptions must not become zero,
`None`, or a successful empty result.

Outcomes carry stable reason codes, safe context, and sufficient provenance. Logs
support diagnosis but are not financial semantics.

## 12. Testing architecture

Default tests are deterministic and offline, using sanitized fixtures, small
synthetic cases, and fakes for ports.

- Source-client tests cover requests, timeout, bounded retry, malformed response,
  and provider-failure mapping with mocks.
- Raw-data tests cover immutability, metadata, path safety, and write failures.
- Validation tests cover accepted and rejected payload structures.
- Normalization tests cover eligibility, deterministic selection, cutoff, periods,
  duplicates, conflicts, amendments, restatements, and provenance.
- Metric tests cover approved examples and applicable normal, missing, invalid,
  mismatch, unit, currency, period, boundary, and denominator cases.
- Application tests cover orchestration and typed result assembly.
- Architecture tests or static checks should prevent forbidden imports once the
  package structure exists.

Optional live SEC checks are separately invoked and never required by default.
Financial examples require independent manual verification under the methodology.

## 13. Persistence boundary

Phase 1 uses no PostgreSQL, SQLAlchemy, migration framework, or production-like
persistence. Fixture loading and immutable local raw preservation are file adapters,
not an analytical database design.

Later persistence must implement application-owned ports and retain enough
identity, version, quality, and provenance data to reproduce results. Raw,
normalized, and calculated representations remain distinguishable.

Schemas, transactions, migrations, retention, and query models remain undecided.
Persistence requires approved contracts, an execution plan, and an ADR where the
choice is durable.

## 14. API and presentation boundary

Phase 1 exposes only a minimal typed Python-facing result. FastAPI, Streamlit,
Power BI, and dashboards are not current components.

Future interfaces consume curated application results. They may render, filter,
paginate, and explain; they must not:

- calculate financial formulas or implement selection, thresholds, or weights;
- substitute zero for missing values;
- query provider payloads as an analytical shortcut; or
- suppress provenance, data-quality states, or material limitations.

The dashboard is a view and interaction layer, never a calculation engine. Any
later Power BI deliverable must reconcile to curated Python-calculated outputs.

## 15. Security and data-integrity considerations

Provider responses, fixtures, paths, identifiers, configuration, and future user
input are untrusted. Outer layers validate identifiers and paths, bound payloads
where appropriate, and avoid unsafe deserialization.

The SEC client must use explicit timeouts, bounded retries, compliant
identification, and access limits. Credentials, private contact data, environment
files, and production connection strings must not be committed or logged.

Raw writes must prevent overwrite, path traversal, partial-file publication, and
confusion between raw and processed data. Integrity metadata should make accidental
change detectable when preservation is implemented.

Lineage retains company, concept, filing, period, unit, currency, retrieval, and
amendment context as applicable. Unsupported combinations fail explicitly rather
than being silently merged or coerced.

## 16. Future evolution

Future capabilities enter through these boundaries only after roadmap, contract,
and methodology approval:

- generalized multi-company normalization and persistence;
- broader financial metrics and trends;
- explainable risk, distress, and scenario modules;
- FRED or other approved official-source adapters;
- peer and sector analysis;
- a typed API and interactive application;
- PostgreSQL-backed persistence adapters; and
- separate Power BI reporting over curated results.

FastAPI, Streamlit, SQLAlchemy, PostgreSQL, FRED, and Power BI are future
integration choices, not installed or operational components. Docker,
orchestration, and machine learning are outside the current implementation; any
later use requires explicit product, architecture, dependency, and roadmap
approval.

## 17. Known limitations

- Production modules and contracts do not yet exist, so exact types and adapter
  APIs remain to be approved.
- Phase 1 is limited to Microsoft annual SEC Company Facts, five normalized
  concepts, and three metrics; its selection policy is not multi-company policy.
- Default operation depends on a sanitized fixture; live SEC availability is not
  guaranteed.
- No analytical persistence, API, dashboard, risk score, stress analysis, peer
  comparison, macro integration, or reporting system is present.
- Retention, migrations, deployment, observability, and performance targets remain
  deferred until an approved use case requires them.

## 18. Architecture decision summary

| Decision | Status and consequence |
|---|---|
| Modular monolith | Adopted; explicit modules deploy together by default. |
| Framework-independent domain | Adopted; financial logic has no infrastructure or UI dependencies. |
| Inward dependency direction | Adopted; adapters depend on application/domain contracts. |
| Phase 1 source | SEC Company Facts and sanitized local fixtures only. |
| Phase 1 interface | Minimal typed Python-facing result only. |
| Provenance | Required from source fact through calculated result. |
| Data quality | Typed states; zero differs from missing or unavailable. |
| Raw preservation | Immutable local copies; fixtures are separate reviewed artifacts. |
| Persistence | Future boundary; no Phase 1 database. |
| API and presentation | Future adapters; never formula or selection owners. |
| Risk and scenarios | Future domain boundaries, not Phase 1 behavior. |
| Distributed services | Deferred; require evidence and an approved ADR. |

## 19. Related authoritative documents

- [`../AGENTS.md`](../AGENTS.md) — repository behavior, priorities, and ownership.
- [`product-requirements.md`](product-requirements.md) — product scope and acceptance.
- [`../ROADMAP.md`](../ROADMAP.md) — sequence, active phase, and progress.
- [`../PLANS.md`](../PLANS.md) — bounded execution-plan requirements.
- [`financial-methodology.md`](financial-methodology.md) — definitions, formulas,
  selection methodology, and limitations.
- [`data-contracts.md`](data-contracts.md) and
  [`data-dictionary.md`](data-dictionary.md) — contracts and field meanings.
- [`risk-model.md`](risk-model.md) — future risk methodology and explanations.
- [`adr/`](adr/) — accepted durable architecture decisions.

Where documents overlap, the ownership and precedence rules in `AGENTS.md` apply.
