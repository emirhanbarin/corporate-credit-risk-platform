# Specify the Phase 1 Microsoft Annual Fact-Selection Policy

Status: Completed
Owner: Repository maintainers
Created: 2026-07-23
Updated: 2026-07-23
Target phase: Phase 1 — Microsoft Vertical Slice, section 1.2
Related issue/ADR: None

## Objective

Establish a complete, deterministic, auditable, Microsoft-specific methodology
and synchronized logical data contracts for selecting annual SEC Company Facts
observations for Revenue, Current Assets, Current Liabilities, Operating Income,
and Interest Expense. The completed documentation must let a later implementation
apply the policy without inventing financial semantics and must not claim that
selection or normalization exists in code.

## Current state

The task began from clean, synchronized `main` at accepted commit
`82113420e72c1a8e50ff12dd47f98151fa339acc`. The unchanged baseline suite passed
with 991 tests.

Repository inspection covered the governing documents, project configuration,
SEC ticker mapping, Company Facts retrieval and raw-artifact boundaries, Company
Facts provider models and parser, public exports, and relevant tests. The accepted
provider boundary:

- represents a CIK as exactly ten decimal digits and resolves the Microsoft test
  record to `0000789019`;
- requires an expected CIK when parsing and rejects a payload CIK mismatch;
- preserves exact taxonomy, concept, and unit keys plus `val`, `accn`, `form`,
  `filed`, `end`, and optional `fy`, `fp`, `frame`, and `start` fields;
- retains the exact originating `SecRawArtifact`; and
- deliberately performs no financial selection, normalization, period
  interpretation, amendment treatment, restatement treatment, or metric
  calculation.

The package contains no approved normalization or fact-selection implementation
and no Company Facts fixture. Existing methodology and contracts require an
explicit policy but defer exact Microsoft tag mappings, candidate ranking, and
reason-code semantics. `ROADMAP.md` keeps every Phase 1 item unchecked and will
remain unchanged.

## In scope

- Create and maintain this bounded execution plan.
- Research only primary SEC, Microsoft filing, SEC Company Facts, and official
  US GAAP taxonomy evidence needed for the narrow policy.
- Add the authoritative Microsoft annual selection policy to
  `docs/financial-methodology.md`.
- Synchronize only the necessary request, candidate-evaluation, outcome,
  invariant, status, and reason-code semantics in `docs/data-contracts.md`.
- Add only the minimum controlled policy terms to `docs/data-dictionary.md`.
- Validate internal consistency and the unchanged repository quality suite.
- Commit and push only the four expected documentation files after all stop
  conditions have been cleared.

## Out of scope

- Python contracts, enums, selectors, normalizers, metrics, provider changes, raw
  storage changes, fixtures, tests, dashboards, configuration, dependencies, or
  other implementation.
- Any company other than Microsoft Corporation or any reusable company registry.
- Quarterly, trailing-twelve-month, segment, non-USD, ordinary non-`10-K`,
  reconstructed, converted, or cross-company selection. `10-K/A` remains only
  conditional amendment evidence.
- Broad amendment or restatement resolution beyond evidence available in SEC
  Company Facts.
- Metric formulas, risk logic, persistence, APIs, presentation, or roadmap status
  changes.
- An ADR; this task makes financial-methodology and logical-contract decisions,
  not a durable technical architecture decision.

## Implementation approach

1. Verify the guarded Git baseline and unchanged test count, stopping if the
   repository is dirty, unsynchronized, or not on `main`.
2. Inspect all governing documents, accepted provider/parser contracts, public
   exports, callers, and relevant tests; confirm that selection is not
   implemented.
3. Record this plan before external methodology research.
4. Consult only authoritative SEC/XBRL materials, Microsoft SEC filings and
   Company Facts evidence, and official US GAAP taxonomy definitions. Record
   concise source references and stop if any required mapping would require a
   guess.
5. Define the Microsoft-only identity, request context, exact filing/cutoff/unit
   and period eligibility, ordered tag mappings, amendment/restatement policy,
   deterministic candidate order, duplicate/conflict rules, outcomes, reason
   codes, provenance, versioning, and limitations in the financial methodology.
6. Synchronize logical request, candidate-evaluation, and selection-outcome
   contracts and invariants without prescribing Python names, persistence, or
   serialization.
7. Add concise controlled definitions to the data dictionary without duplicating
   the methodology.
8. Manually cross-check all five concepts, the methodology identifier, status and
   reason semantics, tag order, period-type boundaries, amendment/cutoff
   treatment, implementation claims, roadmap claims, and external evidence.
9. Run every required repository validation, review the complete and staged
   diffs, mark this plan Completed with actual results, and use the guarded
   commit/fetch/push workflow.

## Testing and validation

No tests or implementation files will change. Validation must include:

- a manual five-concept, tag-order, methodology-version, outcome/reason,
  amendment/cutoff, duration/instant, provenance, limitation, implementation-
  claim, roadmap-claim, and source-evidence consistency review;
- `.venv/bin/python -m ruff check .`;
- `.venv/bin/python -m ruff format --check .`;
- `.venv/bin/python -m mypy src/credit_risk_platform`;
- `.venv/bin/python -m pytest`;
- `.venv/bin/python -m pytest --cov=credit_risk_platform --cov-branch`;
- `git diff --check`; and
- `git status --short`.

Coverage must remain 100%. Any failed required check blocks commit and push.

## Documentation

- `docs/financial-methodology.md` owns company-specific financial eligibility,
  tag meaning and priority, cutoff, filing, amendment/restatement,
  duplicate/conflict resolution, outcomes, provenance requirements, methodology
  version, and limitations.
- `docs/data-contracts.md` owns the logical selection-stage structures and
  invariants that carry the methodology decisions between future components.
- `docs/data-dictionary.md` owns concise controlled term meanings.
- This plan records bounded execution, evidence, validation, deviations, and the
  stopping condition.
- `ROADMAP.md` owns progress and sequencing and is intentionally unchanged.

## Financial and analytical assumptions

- The analytical entity is Microsoft Corporation under the repository's canonical
  SEC CIK representation. Its narrow stable identifier is
  `microsoft_corporation`, its CIK is `0000789019`, and ticker and entity-name
  text remain descriptive.
- The policy is limited to consolidated annual Company Facts evidence for the five
  named concepts, exact issuer fiscal dates, USD monetary units, eligible 10-K
  context, and an inclusive date-only analysis cutoff.
- The stable methodology identifier is
  `microsoft_annual_company_facts_v1`; the exact eligible unit key is `USD`, and
  the cutoff rule is `observation.filed <= analysis_cutoff`.
- Duration and instant facts are evaluated separately. Annual duration is not
  inferred from a frame or fixed 365-day count, and point-in-time facts cannot
  have a start date.
- Selection cannot reconstruct values, translate currency, infer source-tag
  equivalence from labels, or use provider response order.
- Amendments, later prior-period reporting, duplicates, and conflicts remain
  distinct. Company Facts evidence that cannot establish a safe replacement must
  produce an explicit unresolved outcome.
- Exact concept tags and their order are approved only when primary evidence
  establishes Microsoft-specific accounting suitability.

## Data contracts and compatibility

This task adds new semantic contracts for an annual fact-selection request,
evaluated candidate, and structured selection outcome. It finalizes a narrow
selection-status vocabulary, a bounded reason-code vocabulary, selection
invariants, and one repository-controlled methodology identifier. These are new
documentation-level semantics for later implementation; no serialized format,
Python type, API, persistence schema, compatibility mechanism, or implemented
public contract changes in this task.

Any later implementation must preserve provider observations and raw-artifact
lineage rather than replacing them with only a selected value. A material change
to eligibility, cutoff, source-tag priority, amendment/restatement treatment, or
duplicate/conflict resolution will require a new methodology version.

## Error and edge-case behavior

- Wrong company identity, malformed candidate evidence, unsupported concepts,
  units, forms, periods, or treatments must fail explicitly.
- Evidence filed after the inclusive analysis cutoff is rejected before ranking.
- Missing approved tags or an empty eligible set produces an explicit
  value-less outcome; missing is never zero.
- Exact duplicates may collapse only under the documented equivalence rule while
  retaining every lineage record.
- Equally ranked conflicting values are never resolved by response order,
  retrieval time, averaging, minimum, maximum, or an undocumented “latest” rule.
- An amendment or later prior-period observation that cannot be related safely
  from preserved Company Facts fields produces a structured unresolved outcome.
- Absent or mismatched duration/instant boundaries, fiscal context, accession,
  unit, or filing evidence cannot be inferred.

## Risks and open questions

- **Microsoft tag history may be incomplete or semantically inconsistent.**
  Approving a guessed fallback could select the wrong accounting concept. Mitigate
  by requiring Microsoft filings, Company Facts observations, and official
  taxonomy definitions; omit unsupported tags and stop if a required concept has
  no defensible mapping.
- **Company Facts may not prove amendment or restatement supersession.** Guessing
  could rewrite historical evidence or introduce look-ahead bias. Mitigate with a
  conservative unresolved outcome whenever accession, form, filing date, period,
  and value evidence cannot establish the documented rule.
- **Interest concepts may be netted or broader than Interest Expense.** Treating
  net interest or finance cost as gross interest expense would invalidate Interest
  Coverage. Mitigate by approving only an exact, authoritative mapping; otherwise
  leave the concept unavailable or unsupported.
- **Documentation vocabularies could diverge.** Conflicting statuses, reasons,
  tag order, or version identifiers would make later implementation ambiguous.
  Mitigate with explicit cross-document checks and a complete diff review.
- **Remote `main` may advance.** Proceeding would violate the guarded baseline.
  Re-fetch immediately before push and stop rather than merge, rebase, amend, or
  force-push.

No open question may be answered by implementation guesswork. Insufficient primary
evidence, an unresolved owning-document conflict, a changed remote baseline, an
unexpected file change, failed validation, or coverage below 100% blocks commit
and push.

## Completion record

Primary SEC API, XBRL, filing, amendment, restatement, and individual Company
Concept evidence was sufficient to close the bounded methodology without an ADR
or implementation change. The completed policy establishes:

- stable Microsoft identifier `microsoft_corporation` associated with canonical
  SEC CIK `0000789019`;
- ordinary form `10-K`, conditional `10-K/A` amendment evidence, exact unit
  `USD`, annual fiscal-period code `FY`, exact issuer dates, and the inclusive
  date-only cutoff;
- ordered Revenue tags
  `us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax`,
  `us-gaap:SalesRevenueNet`, and `us-gaap:Revenues`;
- single Current Assets, Current Liabilities, and Operating Income tags
  `us-gaap:AssetsCurrent`, `us-gaap:LiabilitiesCurrent`, and
  `us-gaap:OperatingIncomeLoss`;
- ordered Interest Expense tags `us-gaap:InterestExpenseNonoperating` and
  `us-gaap:InterestExpense`;
- deterministic candidate occurrence, candidate fact, equivalence, fallback,
  primary-reason, status, and provenance semantics; and
- conservative Unsupported outcomes when Company Facts cannot resolve a changed
  amendment or later-reported prior-period value.

The final documentation review confirmed all five concepts, one identical
methodology identifier, exact status and reason vocabularies, one authoritative
tag order, consistent amendment/cutoff rules, separate duration and instant
requirements, and complete raw-artifact lineage. It also confirmed no
implementation or roadmap completion claim and no unapproved source mapping.

Validation completed without skipped checks:

- `.venv/bin/python -m ruff check .` — passed;
- `.venv/bin/python -m ruff format --check .` — passed, 38 files already
  formatted;
- `.venv/bin/python -m mypy src/credit_risk_platform` — passed, 20 source files;
- `.venv/bin/python -m pytest` — passed, 991 tests;
- `.venv/bin/python -m pytest --cov=credit_risk_platform --cov-branch` — passed,
  991 tests and 100% statement and branch coverage;
- `git diff --check` — passed; and
- `git status --short` — showed only the four expected documentation paths.

There were no scope deviations, skipped checks, dependency changes, ADRs, source
or test changes, or roadmap changes. Remaining limitations are intentional:
selection is not implemented; global company-registry and serialized-contract
mechanics remain deferred; and Company Facts alone cannot resolve every future
amendment or restatement ambiguity.

## Stopping condition

Stop after the four expected documentation files define and synchronize the
Microsoft-only annual selection policy, all required validation passes, the exact
files are committed with the required message and pushed to unchanged
`origin/main`, and final synchronization and cleanliness are verified. Do not
implement the later Python policy contracts or change roadmap progress.

## Completion criteria

- The four expected documentation files are the only changed and committed files.
- Primary evidence supports every approved source tag and the conservative
  amendment/restatement rules; unsupported alternatives remain excluded.
- All fifteen required methodology decisions are explicit, deterministic,
  auditable, Microsoft-specific, and independent of provider response order.
- Logical request, candidate, outcome, invariant, status, reason, and provenance
  contracts are synchronized without implementation names or schemas.
- The minimum controlled dictionary terms are defined consistently.
- No source, test, configuration, dependency, fixture, ADR, or roadmap file
  changes.
- Manual consistency checks and every listed command pass, including 100%
  coverage.
- The plan records actual validation, deviations, and remaining limitations and is
  marked Completed only after documentation and validation finish.
- The exact commit message is used; remote `main` has not advanced; push succeeds;
  final `HEAD` equals `origin/main`; and the working tree is clean.
