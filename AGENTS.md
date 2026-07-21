# Repository Instructions for Coding Agents

## 1. Mission and priorities

This repository develops an explainable Corporate Credit Risk & Financial Health
Platform for publicly listed companies.

Prioritize, in order:

1. Financial correctness
2. Data provenance
3. Explainability
4. Reproducibility
5. Testability
6. Clear documentation
7. Small, reviewable changes

Do not trade these priorities for feature volume, visual polish, or unnecessary
technical complexity.

## 2. Scope

These instructions apply throughout the repository unless a more specific
`AGENTS.md` exists below the file being changed.

Before changing anything:

1. Read the task and relevant authoritative documentation.
2. Inspect the existing implementation, tests, callers, schemas, and configuration.
3. Confirm the allowed scope and stopping condition.
4. Make the smallest coherent change that satisfies the task.

Do not perform unrelated cleanup, refactoring, renaming, dependency changes, or
architectural redesign. If a required decision is missing or conflicts with an
authoritative document, stop and report it rather than inventing policy.

## 3. Document authority and ownership

Documents own different kinds of decisions:

1. `AGENTS.md` governs agent behavior.
2. `docs/product-requirements.md` governs product scope and acceptance.
3. `docs/architecture.md` and accepted records in `docs/adr/` govern technical
   architecture and durable technology decisions.
4. `docs/financial-methodology.md`, `docs/data-contracts.md`,
   `docs/data-dictionary.md`, and `docs/risk-model.md` govern financial and data
   semantics within their respective subjects.
5. `ROADMAP.md` alone governs sequencing, dependencies, the active phase, and
   progress.
6. An approved execution plan governs one bounded implementation task and may not
   override the documents above it.

When documents conflict, follow the document that owns the subject. Escalate a
conflict that cannot be resolved by ownership. Do not copy volatile phase status
into other documents.

## 4. Technology governance

Until architecture documentation or an accepted ADR establishes or supersedes a
choice, this section is the sole authoritative interim technology direction:

- Python 3.12
- PostgreSQL for production-like persistence
- FastAPI for a later API layer
- Streamlit for a later interactive application
- SQLAlchemy and Pydantic where approved contracts require them
- pytest, Ruff, mypy, and GitHub Actions for quality automation
- Power BI as a separate later reporting deliverable

This direction does not mean that any dependency is installed or that any command
works. Add a dependency only when an approved task establishes a concrete need.
Do not treat pandas, NumPy, machine-learning libraries, orchestration platforms, or
cloud services as approved by implication. Durable stack decisions and changes
must be recorded in architecture documentation or an ADR as appropriate.

## 5. Architecture boundaries

Keep these responsibilities separate:

1. External source access
2. Original and locally preserved raw data
3. Validation and normalization
4. Financial metric calculation
5. Risk and scenario analysis
6. Persistence and application services
7. API and presentation

Required boundaries:

- Source clients do not calculate financial metrics.
- Provider payloads do not flow directly to analytical presentation.
- Source-specific parsing stays outside provider-independent domain logic.
- Financial calculations are deterministic and side-effect free where practical.
- Database, API, and presentation objects do not enter pure business rules.
- User interfaces do not own formulas, thresholds, weights, or source selection.
- Risk logic consumes validated normalized inputs, not raw provider payloads.
- Presentation does not reinterpret missing, invalid, or contradictory results.

## 6. Financial correctness

- Never fabricate financial values, company facts, provenance, formulas,
  benchmarks, thresholds, or research results.
- Never silently convert missing or unavailable data to zero.
- Distinguish zero, missing, unavailable, invalid, not applicable, inconsistent,
  unsupported, and estimated values when those states apply.
- Do not silently combine different companies, accounting scopes, periods, filing
  forms, currencies, or units.
- Do not mix annual and quarterly values or point-in-time and duration facts without
  explicit methodology.
- Preserve reporting period, filing or observation date, and retrieval date as
  distinct concepts.
- Do not introduce look-ahead bias into historical analysis.
- Handle zero denominators and unsupported mismatches explicitly.
- Do not change formulas, thresholds, weights, stable identifiers, schemas, APIs,
  or stored formats without approved scope and synchronized documentation.

Every implemented metric must have an authoritative definition covering its
business meaning, formula, inputs, period and scope rules, currency and unit rules,
missing and exceptional behavior, interpretation, limitations, and at least one
manually verified example. The detailed definition belongs in
`docs/financial-methodology.md`.

Internal analytical categories are not official credit ratings. Distress models
must identify the exact variant and applicable population and must not be described
as guaranteed predictions.

## 7. Provenance, raw data, and normalization

Prefer authoritative public sources and preserve sufficient metadata to trace a
result to its provider, company, concept, filing or series, period, retrieval,
currency, unit, and applicable amendment state.

Use these terms precisely:

- **Original provider payload:** the response received before transformation.
- **Locally preserved raw response:** an immutable local copy of the original
  payload with retrieval metadata, stored separately from normalized and calculated
  data.
- **Sanitized committed test fixture:** a reviewed copy that may be reduced or
  redacted for deterministic tests. It is not the original payload.

Never edit a preserved raw response to make processing succeed. A fixture must
preserve the behavior under test and record its source and sanitization. Do not
commit secrets, personal provider-identification details, or unreviewed large data
dumps.

Normalization and fact selection must be deterministic, documented, and
explainable. Do not silently choose among duplicate, conflicting, amended,
restated, differently tagged, differently scoped, or differently periodized facts.
Represent unresolved ambiguity as a structured data-quality outcome.

## 8. Explainability

Every material analytical conclusion must remain traceable through:

1. source fact and provenance;
2. normalized concept and selection rationale;
3. formula or rule and validated inputs;
4. calculated result and data-quality status; and
5. interpretation or reason code.

Risk scores and stress scenarios must be deterministic, versioned when appropriate,
explicit about missing inputs and assumptions, and reproducible. Do not hide
negative or contradictory signals or present scenario results as forecasts.

## 9. Testing and validation

Add or update tests in proportion to the risk of the change.

- Financial logic requires normal, missing, invalid, denominator, period, unit,
  currency, boundary, and manually verified cases as applicable.
- Ingestion and normalization require deterministic success, failure, malformed,
  ambiguity, and provenance cases as applicable.
- Risk logic requires component, weight, threshold, missing-input, explanation,
  and reproducibility tests as applicable.
- Bug fixes should include a regression test when practical.
- Default tests must not require live network access. Keep optional live checks
  explicit and separate.
- Do not weaken or remove tests merely to obtain a passing result.

Run only commands supported by the repository and relevant to the task. Report
every command actually run and whether it passed, failed, or could not be run. Do
not claim validation that did not occur.

## 10. Security and external access

Treat external data, serialized files, paths, identifiers, parameters, and user
input as untrusted.

Never commit or expose credentials, tokens, passwords, private email addresses,
private financial or company data, environment files, or production connection
strings. Use documented environment-variable names and non-secret placeholders.

External clients must use explicit timeouts, bounded retry behavior, provider
identification, and applicable access limits. Prefer an official API to scraping.
Do not log secrets or complete sensitive environment values.

## 11. Planning and scope control

Use `PLANS.md` for work that is risky, cross-cutting, financially sensitive,
contract-changing, or too large for a short task. An execution plan cannot broaden
the roadmap phase or product scope.

During implementation:

- follow only the approved scope;
- preserve existing user changes;
- avoid premature abstractions and unrelated formatting;
- add tests and documentation with the behavior they cover;
- stop at the approved stopping condition; and
- report unexpected architecture, methodology, or contract decisions before
  continuing.

## 12. Git safety

- Inspect status and the final diff before completion.
- Do not stage or discard unrelated user changes.
- Do not rewrite history or force-push.
- Do not commit, push, merge, tag, publish, or create releases unless explicitly
  requested.
- Do not commit caches, virtual environments, local databases, secrets, generated
  artifacts, or large raw payloads without explicit review.

## 13. Reviews and completion

When asked to review, do not edit unless requested. Inspect the actual diff and
relevant surrounding code and documentation. Report concrete findings in severity
order with file and line references where possible, prioritizing financial
correctness, data integrity, provenance, security, regressions, scope, and missing
tests.

At completion, report the outcome, files changed, important assumptions or contract
effects, tests and validation results, documentation updates, remaining limitations,
and confirmation that the requested scope and stopping condition were respected.
