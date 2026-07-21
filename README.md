# Corporate Credit Risk & Financial Health Platform

An explainable financial analytics platform for evaluating the financial
performance, credit risk, and stress resilience of publicly listed companies.

> **Current state:** Foundation documentation and repository scaffolding exist, but
> no production financial-analysis application has been implemented. `ROADMAP.md`
> is the sole source of phase status and progress.

## Why this project exists

Public-company financial data is available, but reliable analysis requires more
than displaying reported values. Source tags vary, reporting periods can be
misaligned, missing values can be mistaken for zero, and risk conclusions can be
presented without an auditable explanation.

This project is intended to demonstrate a disciplined approach to those problems:

- preserve source provenance;
- normalize financial facts explicitly;
- validate periods, currencies, units, and accounting scope;
- calculate documented and tested financial metrics;
- produce explainable analytical risk outputs; and
- make limitations and unavailable results visible.

The project is also a professional portfolio artifact for finance, credit-risk,
risk-analysis, and financial-data roles.

## Milestones

The project uses three distinct milestone terms:

- **Phase 0 Foundation** establishes documentation, architecture, project
  configuration, quality tooling, and repository governance. It contains no
  production financial-analysis logic.
- **Phase 1 Microsoft Vertical Slice** is the first bounded end-to-end analysis.
  It will use annual Microsoft SEC data, a narrow deterministic fact-selection
  policy, three initial metrics, and a minimal Python-facing result interface.
- **Portfolio-Ready Release** is the later release at which the broader analysis,
  explainability, interfaces, reproducibility, and presentation criteria in the
  product requirements are satisfied.

These milestones are not interchangeable. See `ROADMAP.md` for sequence, status,
dependencies, and exit criteria.

## Planned product direction

Subject to phase approval and documented architecture decisions, the platform is
expected to grow toward:

- SEC financial-data ingestion and controlled raw-data preservation;
- normalized annual financial facts and tested financial metrics;
- explainable financial-health scoring and deterministic risk flags;
- macroeconomic scenario and stress analysis;
- documented peer comparison using defensible peer groups;
- a reusable Python domain layer, API, and interactive analytical interface; and
- a separate executive reporting deliverable.

Planned capabilities are not current functionality.

## Data handling terminology

The project distinguishes three forms of source data:

- **Original provider payload:** the response received from an external provider,
  before project transformation.
- **Locally preserved raw response:** an immutable local copy of that payload plus
  retrieval metadata. It remains separate from normalized and calculated data and
  is not assumed to be suitable for committing to Git.
- **Sanitized committed test fixture:** a reviewed, reduced or redacted copy used
  for deterministic tests. It must retain the behavior under test and document its
  origin and sanitization, but it is not represented as the original payload.

## Technology direction

Technology adoption is phase- and task-gated. The authoritative interim direction
and dependency safeguards are in `AGENTS.md`; architecture documents and
Architecture Decision Records govern durable technical choices as they are made.
Nothing in this README implies that a dependency is installed or operational.

## Current repository state

The repository currently contains foundational documentation, directory
scaffolding, and placeholder project files. No SEC client, normalization pipeline,
financial metric engine, risk score, API, database workflow, dashboard, or Power BI
logic is implemented.

No setup, test, lint, type-check, application-start, or database command is
documented here as working until the corresponding Phase 0 configuration is
complete and verified.

## Documentation map

| Document | Responsibility |
|---|---|
| `AGENTS.md` | Permanent repository-wide rules for coding agents |
| `docs/product-requirements.md` | Product scope, outcomes, acceptance, and non-goals |
| `docs/architecture.md` and `docs/adr/` | Technical boundaries and durable decisions |
| `docs/financial-methodology.md` | Financial definitions, formulas, assumptions, and limitations |
| `docs/data-contracts.md` and `docs/data-dictionary.md` | Data semantics, contracts, and field meanings |
| `docs/risk-model.md` | Risk methodology, thresholds, explanations, and limitations |
| `ROADMAP.md` | Sequence, dependencies, current phase, progress, and exit criteria |
| `PLANS.md` | Policy and template for one bounded execution plan |

When documents overlap, the document assigned to that subject is authoritative.
`AGENTS.md` contains the full ownership and precedence rule.

## Development principles

- Financial correctness over feature volume
- Explainability over black-box output
- Provenance over convenience
- Reproducibility over undocumented manual work
- Small, reviewable changes over broad implementation
- Official public sources over avoidable scraping
- Explicit limitations over overstated conclusions

## Roadmap

The active phase and all progress markers are maintained only in `ROADMAP.md`.
Future documents should link to that status rather than reproduce it.

## Disclaimer

This project is for educational, analytical, and portfolio purposes. It does not
provide investment advice, buy or sell recommendations, official credit ratings,
lending decisions, professional accounting advice, or legal or regulatory
conclusions.

Analytical outputs will depend on the quality, availability, interpretation, and
normalization of public source data.

## License

A project license has not yet been selected. That work is tracked in `ROADMAP.md`.
