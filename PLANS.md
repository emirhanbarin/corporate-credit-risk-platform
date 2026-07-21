# Execution Plans

## 1. Purpose

An execution plan describes how one approved, bounded body of work will be
completed. It is used when a short task description is not sufficient to make the
work safe, reviewable, and testable.

An execution plan is not:

- a product requirements document;
- a roadmap or progress tracker;
- an Architecture Decision Record;
- permission to exceed the active roadmap phase; or
- a substitute for inspecting the repository before implementation.

Document ownership and precedence are defined in `AGENTS.md`.

## 2. When a plan is required

Create an execution plan when work:

- adds or changes a source integration;
- changes financial methodology, fact selection, or normalized concepts;
- changes a stored, serialized, database, or public API contract;
- adds or changes risk scoring or stress-testing logic;
- crosses multiple architecture layers;
- introduces a major dependency or durable architecture decision;
- requires a significant refactor or multiple implementation sessions; or
- carries material financial-correctness, provenance, security, or migration risk.

A full plan is normally unnecessary for a typo, narrow documentation correction,
isolated test addition, small configuration correction, or well-understood local
bug fix with no contract or methodology effect.

When uncertainty is material, prepare a short plan before implementing.

## 3. Planning-only behavior

When asked only to create or review a plan:

- inspect relevant documentation, implementation, tests, callers, schemas, and
  configuration;
- do not edit implementation files or begin implementation;
- do not install dependencies or create migrations;
- do not commit, push, publish, or change external systems;
- distinguish confirmed repository facts, approved requirements, proposals,
  assumptions, open questions, and deferred work; and
- end with an explicit stopping condition.

## 4. Storage and identity

Store repository execution plans under `docs/plans/` when a plan file is requested
or needed for multi-session work.

Use a descriptive filename:

```text
YYYY-MM-DD-short-task-name.md
```

Use one status:

- Draft
- Approved
- In progress
- Blocked
- Completed
- Superseded

Include creation and update dates, author or owner, target roadmap phase, and links
to a related issue or ADR when they exist. Completed plans remain available unless
an approved archival policy says otherwise.

## 5. Always-required plan fields

Every execution plan must contain the following fields.

### Objective

State the testable outcome that must exist when the task is complete.

### Current state

Summarize what was inspected, what exists now, what is missing, and which approved
decisions constrain the work. Do not describe repository behavior without evidence.

### In scope

List concrete deliverables. Identify expected files or components and the intended
responsibility of each.

### Out of scope

Name adjacent work that must not be implemented. This is mandatory whenever scope
could reasonably expand.

### Implementation approach

Provide ordered steps with a specific outcome for each. Identify architecture
ownership and allowed dependency direction where relevant. Do not use vague steps
such as “implement everything” or “fix issues.”

### Testing and validation

Describe the tests required by the behavior and list exact commands that the
repository supports. Include targeted checks before broader checks when practical.
Default validation must not require live network access.

### Documentation

Identify authoritative documents that must change with the behavior. Do not update
unrelated documents merely because they are listed in the repository.

### Risks and open questions

For each material risk, state the failure scenario, impact, mitigation, and
remaining uncertainty. Identify questions that require approval before work can
continue.

### Stopping condition

State exactly where implementation ends, including nearby features that remain
excluded.

### Completion criteria

List observable conditions for completion, including required behavior, tests,
documentation, validation, scope compliance, and unresolved limitations.

## 6. Conditional plan fields

Include these sections only when the task affects them.

### Financial and analytical assumptions

For financial work, define or reference the accounting concepts, reporting period,
scope, currency, units, filing treatment, missing-data behavior, estimation status,
look-ahead controls, interpretation, and applicability limitations.

### Data contracts and compatibility

For contract changes, identify affected requests, responses, domain objects,
schemas, files, identifiers, enums, statuses, reason codes, or environment
variables. Mark changes as new, compatible, breaking, internal, or user-visible.
Breaking changes require explicit approval and a migration or compatibility plan.

### Error and edge-case behavior

For behavior with material failure modes, define relevant handling for missing,
invalid, duplicate, conflicting, ambiguous, mismatched, partial, unavailable,
rate-limited, or otherwise exceptional inputs.

### Architecture and durable decisions

Describe component ownership, data flow, side effects, configuration, failure
representation, and dependency boundaries when the task changes them. Link an ADR
for a durable choice; the execution plan describes how, while the ADR describes why.

### Rollout, migration, or rollback

Include this section when persisted data, public contracts, deployed behavior, or
external consumers could be affected.

## 7. Reusable plan template

```markdown
# <Outcome-oriented title>

Status: Draft
Owner: <name>
Created: YYYY-MM-DD
Updated: YYYY-MM-DD
Target phase: <roadmap phase>
Related issue/ADR: <links or none>

## Objective
<Testable completed outcome>

## Current state
<Evidence, inspected files, constraints, and missing behavior>

## In scope
- <deliverable>

## Out of scope
- <explicit exclusion>

## Implementation approach
1. <ordered step and outcome>

## Testing and validation
- <test behavior>
- `<supported command>`

## Documentation
- <authoritative document and required update>

## Risks and open questions
- <failure scenario, impact, mitigation, uncertainty>

## Stopping condition
<Exact boundary at which implementation stops>

## Completion criteria
- <observable criterion>

## Conditional sections
Include only applicable financial assumptions, data-contract and compatibility,
edge-case behavior, architecture/ADR, and rollout or migration sections.
```

## 8. Maintaining an active plan

An active plan is a concise record of execution, not a prediction that must be made
to look perfect. Update its status, progress, discoveries, decisions, deviations,
validation results, and remaining risks as work proceeds.

If implementation reveals a material scope, architecture, methodology, contract,
or risk change:

1. stop the affected work;
2. record the evidence and impact;
3. propose the smallest viable plan change;
4. update or add the appropriate authoritative document or ADR; and
5. obtain approval when the change exceeds the approved task.

Minor implementation details that preserve scope and contracts may be recorded
without full reapproval.

## 9. Relationship to issues, ADRs, and the roadmap

- A GitHub issue states an approved task and acceptance criteria.
- An execution plan explains how one task will be delivered.
- An ADR explains why a durable technical decision was chosen.
- `ROADMAP.md` controls sequence, dependencies, active phase, and progress.

Do not duplicate an entire plan in an issue or copy roadmap status into a plan.
Completing a plan does not automatically complete a roadmap phase.

## 10. Completing a plan

Before marking a plan completed:

- record validation results and any skipped checks;
- record deviations and remaining limitations;
- confirm required documentation is synchronized;
- review status and the complete diff;
- confirm no unrelated changes were included;
- confirm the stopping condition was respected; and
- update the related issue or roadmap status when authorized.

Code being written is not, by itself, completion.
