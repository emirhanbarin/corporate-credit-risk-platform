# Financial Health and Risk Assessment Governance

## 1. Purpose and scope

This document governs how future financial-health and financial-risk assessments must be structured, explained, validated, versioned, communicated, and limited. The framework may provide evidence-based decision support that helps financial, credit-risk, and investment-research analysts examine financial condition, direction, strengths, weaknesses, and data limitations.

The platform provides explainable financial-health and financial-risk decision support. It does not produce investment recommendations or replace independent analytical judgment.

The platform does not exist merely to produce a score. It exists to produce an explainable financial assessment. A score may later provide a concise summary, but it must not replace underlying evidence, metrics, component results, limitations, or analyst interpretation.

This document currently approves governance principles only. It does not approve formulas, weights, thresholds, ranges, boundaries, component inclusion rules, probability-of-default estimates, official credit ratings, investment recommendations, valuation conclusions, distress-model rules, stress assumptions, or machine-learning models.

The project has no implemented financial-health score, component score, aggregate assessment, analytical category, or risk-flag engine. [`../ROADMAP.md`](../ROADMAP.md) alone governs implementation sequence and status.

Authority remains divided by subject: `AGENTS.md` governs agent behavior; product requirements govern scope and acceptance; architecture and ADRs govern technical decisions; financial methodology governs financial-analysis semantics; data contracts govern stage structures and invariants; the data dictionary governs controlled terminology; this document governs future assessment principles and controls; `ROADMAP.md` governs sequencing and status; and an approved execution plan governs one bounded implementation task.

## 2. Analyst-first philosophy

The platform must augment analytical work rather than replace analysts. Future features must prioritize analytical usefulness, explainability, transparency, reproducibility, source traceability, reviewability, and clear limitations over automation, visual simplicity, or model complexity.

A useful assessment must help an analyst understand:

- the company's current financial condition and direction of change;
- major strengths and weaknesses;
- contradictory and missing evidence; and
- the source of every material conclusion.

Human-readable output must not conceal analytical complexity by removing important evidence. Concision may organize analysis, but must not suppress uncertainty, exceptions, provenance, or competing signals.

## 3. Evidence-first principle

No assessment should be published without traceable evidence. The expected analytical chain is:

```text
Original provider source
  -> preserved source response
  -> validated provider record
  -> normalized financial fact
  -> calculated metric
  -> component assessment
  -> aggregate assessment
  -> analytical summary
```

Every material conclusion must remain traceable through each applicable stage, including selection rationale, methodology version, analysis cutoff, and data-quality outcomes. Unsupported narrative, fabricated explanations, and scores detached from source evidence are prohibited.

## 4. Assessment philosophy and terminology boundaries

- **Financial-health assessment** summarizes supported evidence about financial condition, resilience, and direction under approved methodology.
- **Credit-risk analysis** examines capacity and vulnerability relevant to meeting financial obligations; it is broader than one score and is not automatically a probability of default.
- **Financial distress indicator** is an independently governed method intended to identify specified distress characteristics within its applicable population.
- **Operational financial strength** concerns the financial performance and resilience of operations; it is not the same as operational-risk management.
- **Investment attractiveness** combines financial quality with price, valuation, market, competitive, qualitative, and investor-specific considerations.
- **Valuation** estimates economic or intrinsic value under a separately approved methodology.
- **Market-price attractiveness** compares a security's market price with an analytical value or return framework.
- **Official credit rating** is an assessment issued under an external rating framework; the platform does not issue one.
- **Probability of default** is a calibrated probability estimate requiring separate research and validation; none is approved here.
- **Bankruptcy prediction** attempts to predict a legal or distress outcome; a financial-health assessment is not such a prediction.
- **Scenario analysis** evaluates explicit assumptions and is not a forecast.
- **Forecasting** estimates future outcomes under a defined forecasting methodology; none is approved here.

These terms must not be treated as interchangeable. A financially healthy company is not automatically an attractive investment; a weak result does not predict bankruptcy; an internal category is not an agency rating; a scenario is not a forecast; and a score is not a valuation conclusion.

## 5. Core design principles

- Explainability must precede complexity, and evidence must precede conclusion.
- Deterministic methods must precede probabilistic methods unless separate approval establishes otherwise.
- Design must be component-first, with transparent methodology and reproducible outcomes.
- Provenance must be preserved from source evidence through every assessment output.
- Missing-data treatment must be conservative, and assumptions must be explicit.
- Hidden assumptions, weights, thresholds, and black-box scoring are prohibited.
- The platform must not fabricate precision or silently override contradictory evidence.
- Missing data must not become neutral data, and scoring must not exist solely for presentation convenience.

Every published assessment must be explainable enough that another analyst can understand why it was produced without reading the implementation code.

## 6. No-magic-number principle

- Every numerical assessment must decompose into understandable analytical components.
- Every component must remain traceable to approved metrics and evidence.
- An aggregate number without component explanations is insufficient.
- A score must not imply greater precision than the methodology supports.
- The platform must not optimize for producing a score when evidence does not support one.
- An unavailable assessment must remain unavailable rather than receive a default score.

The score is a consequence of the analysis, not the purpose of the analysis.

## 7. Component-first assessment model

The future conceptual structure is:

```text
Normalized financial facts
  -> calculated financial metrics
  -> financial-health components
  -> component assessments
  -> aggregated financial-health assessment
  -> internal analytical category
  -> explanations, signals, and risk flags
```

Independent components make assumptions, evidence, contradictions, and limitations reviewable without relying on one opaque formula. Component outputs must remain accessible when an aggregate assessment is produced, and aggregate presentation must not flatten materially different component outcomes.

## 8. Candidate future components

These components are candidates, not approved model contents:

| Candidate | Intended analytical question |
|---|---|
| Liquidity | Can reported near-term resources support reported near-term obligations, subject to asset quality and timing limitations? |
| Leverage | How dependent is the company on debt or other fixed financial claims, and how constrained may its balance sheet be? |
| Debt-service capacity | How well do supported earnings or cash-generating measures cover financing obligations? |
| Profitability | Does the company generate sustainable reported profit from its activities, and how is that performance changing? |
| Cash-flow quality | How well do reported earnings translate into cash generation, and how resilient is that cash generation? |
| Growth and stability | Is supported financial performance expanding or contracting, and how stable is the observed pattern? |

A candidate becomes approved only after explicit methodology approval and validation planning. No inputs, formulas, transformations, thresholds, weights, ranges, or category boundaries are established here.

## 9. Current condition and direction of change

Future assessments must distinguish current financial condition, direction of change, and stability of the observed direction. A financially strong company may be deteriorating, while a financially weak company may be improving.

Current condition and direction must not collapse into one unexplained conclusion. Trend interpretation requires comparable periods, consistent methodology, and cutoff integrity. Insufficient or noncomparable history must remain visible rather than being converted into a trend. Trend formulas, time windows, and deterioration thresholds remain unapproved.

## 10. Component assessment contract

Each future component assessment should preserve:

- component identifier and analytical purpose;
- input metric references, values, statuses, and reporting periods;
- analysis cutoff and methodology version;
- assessment status;
- current-condition result and direction-of-change result, only when approved;
- normalized contribution, weight, and weighted contribution, only when approved;
- positive, negative, contradictory, and incomplete evidence;
- reason codes and a human-readable explanation;
- completeness status and provenance references; and
- limitations.

This is a semantic contract, not a Python model, serialized structure, database design, or API schema.

## 11. Aggregate assessment contract

A future aggregate assessment may include:

- assessment identifier, company identity, analysis period, and analysis cutoff;
- component assessments;
- aggregate value and internal analytical category, only when approved;
- current-condition and direction-of-change summaries;
- completeness and reason codes;
- major strengths and weaknesses;
- positive signals, risk flags, and contradictory evidence;
- methodology version and calculation timestamp;
- provenance, limitations, and disclaimer.

Unavailable assessments must not fabricate numeric outputs. Partial assessments must remain visibly partial. An aggregate result must never remove access to component results and supporting evidence.

## 12. Explainability contract

Every published assessment must make it possible to determine:

- which inputs were used, unavailable, or rejected;
- which periods and filings were used;
- which methodology version and rules were applied;
- how each component contributed;
- why any category, signal, flag, or score was produced;
- which contradictory evidence and limitations affected the result; and
- whether the result reflects current condition, direction, or both.

Explanations must be evidence-linked, specific, reproducible, understandable to a financial analyst, consistent with the calculated result, and free from unsupported causal claims.

## 13. Positive, negative, contradictory, and incomplete evidence

The framework must preserve four distinct evidence classes:

- **Positive evidence:** supported facts or results favorable to the stated analytical question.
- **Negative evidence:** supported facts or results adverse to the stated analytical question.
- **Contradictory evidence:** supported signals that point in materially different directions or cannot be reconciled under approved rules.
- **Incomplete evidence:** required or useful evidence that is missing, unavailable, invalid, unsupported, or otherwise insufficient.

Positive evidence must not be omitted because the product is risk-oriented, and negative evidence must not be softened to create a favorable narrative. Contradictory signals must remain visible. Offsetting factors may be described but must not silently cancel one another. Missing evidence is not neutral evidence, and inconvenient facts must not be suppressed for narrative simplicity.

## 14. Completeness framework

The framework must use completeness, not confidence, terminology:

- **Complete:** all required approved components and evidence are usable, compatible, and traceable.
- **Partial:** an assessment is permitted despite disclosed non-critical missing or incomplete evidence.
- **Unavailable:** critical evidence or components prevent a supported assessment.
- **Required component:** a component whose usable result is necessary under the approved aggregate methodology.
- **Optional component:** an approved component whose absence does not block an aggregate result.
- **Critical missing component:** an absent required component that blocks aggregation.
- **Non-critical missing component:** an absent optional component that reduces completeness without necessarily blocking aggregation.
- **Missing component:** no usable component assessment exists; **incomplete component:** a component exists but lacks some supporting evidence or context.

Partial assessments must remain visibly partial, and unavailable assessments must not receive numeric substitutes. Completeness measures evidence coverage, not prediction accuracy or statistical confidence. A complete assessment may still have material methodological limitations. No numerical completeness thresholds are approved.

## 15. Internal analytical categories

Future categories must be internal analytical summaries, not agency ratings. Their terminology must not reasonably be confused with official credit ratings.

Any category framework requires approved boundaries, boundary tests, explicit missing-data behavior, traceability to components, visible completeness and limitations, and methodology versioning. Category names, ordering, and boundaries remain deferred.

## 16. Positive signals and risk flags

Positive signals and risk flags must be deterministic, explainable analytical outputs, not predictions.

Potential positive-signal families may include strong liquidity, improving debt-service capacity, stable profitability, improving cash-flow quality, sustained revenue growth, and strengthening balance-sheet resilience.

Potential risk-flag families may include weak liquidity, elevated leverage, weak debt-service capacity, negative or deteriorating cash flow, declining profitability, repeated revenue contraction, inconsistent source data, and incomplete source data.

No trigger, threshold, or severity level is approved. Each future signal or flag should preserve:

- identifier and signal or flag type;
- affected metric or component;
- triggering rule and observed value;
- comparison value or threshold, only when approved;
- reporting period and analysis cutoff;
- severity, only when approved;
- reason code, explanation, provenance, and status; and
- methodology version.

## 17. Assessment change explanation

A future material-change explanation should identify, when available:

- prior and current assessments;
- methodology compatibility;
- changed source facts, metrics, and component results;
- newly available and newly missing evidence;
- major positive and negative contributors; and
- methodology changes affecting comparability.

Change must not be attributed to business performance when caused by methodology. Incomparable versions must be labeled accordingly. A changed aggregate score without contribution analysis is insufficient. Contribution formulas and materiality thresholds remain deferred.

## 18. Time and cutoff integrity

Every assessment must retain its analysis cutoff, eligible filings, source periods, filing dates, calculation timestamp, and methodology version. A historical assessment must not use information unavailable at its cutoff.

Amendments and restatements must be handled explicitly. Given unchanged preserved evidence, the same cutoff and methodology should reproduce the same result. Later information must not silently alter a historical assessment; revised historical views must be separately identified. These controls prevent look-ahead bias and preserve historical reproducibility.

## 19. Methodology evolution and comparability

- **Methodology version:** the stable identifier for one approved set of assessment rules.
- **Backward-compatible clarification:** a documentation improvement that does not change outcomes or required interpretation.
- **Material methodology change:** a change to analytical meaning, behavior, or comparability requiring a new version.
- **Breaking assessment change:** a change that makes prior and current outputs unsafe to compare directly.
- **Historical recomputation:** a new result calculated for an earlier cutoff using a later methodology or approved revised evidence.
- **Preserved historical result:** the original result retained with its original evidence, cutoff, and methodology.

Changes to formulas, weights, thresholds, categories, component definitions, or missing-data rules require a new methodology version when material. Changes must document analytical rationale. Original results must not be silently overwritten; recomputed results must be distinguishable. Cross-version comparison is permitted only when methodologically valid.

## 20. Model governance

A future model or material change must have:

- documented business objective, user, and analytical purpose;
- defined population and applicability;
- approved component set and input metrics;
- explicit formulas and transformations;
- approved weights and thresholds;
- boundary and missing-data behavior;
- contradictory-evidence behavior;
- validation plan and manually reviewed examples;
- documented limitations and methodology version;
- synchronized documentation updates;
- an ADR where the decision is durable or architectural; and
- explicit approval before implementation.

No scoring logic may be introduced solely through code without approved methodology documentation.

## 21. Validation framework

Future validation must address:

- deterministic reproducibility;
- metric-to-component mapping and component-level tests;
- aggregate calculation and boundary tests;
- missing-data and unavailable-assessment tests;
- contradictory-signal and positive-and-negative evidence tests;
- cutoff-integrity and methodology-version tests;
- monotonicity checks where economically justified;
- manually reviewed company cases and historical stability checks;
- reason-code and provenance completeness;
- explanation consistency; and
- regression testing.

Passing software tests does not prove economic validity, and historical checks do not prove predictive validity. Manually reviewed examples do not replace broader validation. Validation must consider analytical correctness and communication risk.

## 22. Analyst notes and human judgment

Future versions may allow analysts to attach notes, observations, qualitative context, review status, and follow-up questions.

Analyst notes must remain distinguishable from system-calculated outputs and must not silently alter deterministic calculations. Any future manual change to an approved assessment requires an explicit, auditable override record while preserving the original calculated result. Qualitative judgment must not be presented as a reported financial fact. Override workflow and interface design remain deferred.

## 23. Use in investment research

The platform may support investment research by helping users inspect financial quality, identify deterioration or improvement, compare reported trends, examine strengths and weaknesses, review source evidence, understand period changes, and later test approved adverse scenarios.

The platform must not:

- issue buy, sell, or hold recommendations;
- determine portfolio allocation or personalize investment advice;
- estimate intrinsic value without a separately approved valuation methodology;
- replace market, industry, competitive, management, qualitative, or investor-specific analysis;
- imply that financial health automatically makes an investment attractive; or
- imply that a weak assessment automatically means a security should be sold.

## 24. External financial-distress methodologies

Altman Z-Score and Piotroski F-Score are deferred, independent methodologies. Each requires exact variant selection, documented applicability, separately approved inputs, independent calculations, explanations, outputs, limitations, and validation against intended use.

Neither methodology may be silently blended into the internal financial-health assessment. This document defines no distress formula or scoring rule.

## 25. Stress-testing relationship

Future stress testing may recalculate financial facts derived from explicit assumptions, metrics, component assessments, and aggregate assessments under approved scenarios.

Stress testing must remain separate from baseline reported analysis, assumption-driven, versioned, reproducible, clearly labeled, traceable to scenario assumptions, and distinguishable from forecasting. No scenario, shock, probability, or forecast method is approved here.

## 26. Security, ethics, and communication

Future assessment communication must provide:

- no misleading rating terminology, guaranteed-outcome language, or unsupported predictive claims;
- visible limitations and completeness;
- clear distinction among reported facts, normalized facts, calculated metrics, scenarios, system interpretations, and analyst notes;
- no fabricated precision or concealment of unavailable data;
- no presentation encouraging blind reliance on an aggregate score;
- no personalization of investment advice within current scope; and
- no use of generative AI as the source of financial calculations.

If generative AI is later used for narrative assistance, it must explain only approved deterministic outputs and evidence. It must not calculate authoritative metrics or scores, invent facts, causes, sources, or recommendations, or appear indistinguishable from deterministic analytical output.

## 27. Current project boundary

Phase 1, when implemented, is limited to:

- Microsoft-focused SEC Company Facts ingestion;
- raw evidence preservation, validation, and normalization;
- Revenue Growth, Current Ratio, and Interest Coverage; and
- provenance-aware outputs.

Phase 1 does not implement:

- a financial-health score, component scoring, or aggregate scoring;
- internal analytical categories or trend scoring;
- positive-signal, risk-flag, or assessment-change attribution rules;
- Altman Z-Score or Piotroski F-Score;
- stress testing or valuation;
- investment or portfolio recommendations; or
- machine-learning models.

This document defines governance for later phases only. The project currently has no assessment model in code, and `ROADMAP.md` remains authoritative for timing.

## 28. Known limitations and deferred decisions

The following remain unresolved:

- approved component set and metric-to-component mapping;
- minimum historical-period requirements;
- current-condition, direction-of-change, and trend-stability methodology;
- formulas and transformations;
- weights, thresholds, and score scale;
- category names and boundaries;
- positive-signal, risk-flag, and severity vocabularies;
- reason-code vocabulary;
- required-component policy and completeness rules;
- contradictory-evidence treatment and aggregation behavior;
- methodology-version format;
- validation population and historical-evaluation approach;
- cross-sector applicability and sector-specific methodology;
- relationship between internal assessment and external distress indicators;
- analyst-note and override governance; and
- portfolio and investment-research presentation.

No dependent implementation may invent these decisions implicitly.

## 29. Related documents

- [`../AGENTS.md`](../AGENTS.md) — agent behavior, priorities, ownership, and precedence.
- [`../README.md`](../README.md) — project orientation and current-state summary.
- [`../ROADMAP.md`](../ROADMAP.md) — sequencing, dependencies, active phase, and progress.
- [`../PLANS.md`](../PLANS.md) — bounded execution-plan requirements.
- [`product-requirements.md`](product-requirements.md) — product scope, users, acceptance, and non-goals.
- [`architecture.md`](architecture.md) — technical boundaries and dependency rules.
- [`financial-methodology.md`](financial-methodology.md) — financial concepts, metrics, period treatment, and limitations.
- [`data-contracts.md`](data-contracts.md) — data-stage structures, invariants, and provenance contract.
- [`data-dictionary.md`](data-dictionary.md) — controlled terminology and field meanings.

When documents overlap, the ownership and precedence rules in `AGENTS.md` apply.
