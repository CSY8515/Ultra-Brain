# Ultra Brain Governance Loop

## 1. Purpose

The governance loop defines how Ultra Brain repeatedly observes governed state, establishes direction, verifies outcomes, and proposes controlled evolution:

> **Observe → Collect → Analyze → Decision → Rule → Standard → Execution → Validation → Analytics → Optimization → Evolution**

This is the continuous governance lifecycle. At v0.1 it is a state-transition and evidence contract only; no monitoring, automation, analytics, optimization, or execution runtime is implemented.

## 2. Loop invariants

1. The loop MUST remain subordinate to the User and [Constitution](CONSTITUTION.md).
2. Each transition MUST preserve provenance, owner, scope, version, and status.
3. Observation and collection MUST be distinguished from analysis and judgment.
4. Decisions MUST use correct authority and [Decision Flow](DECISION_FLOW.md).
5. Rules and standards MUST conform to higher-order instruments.
6. Execution MUST remain at the responsible layer and within an explicit contract.
7. Validation MUST test declared criteria independently of desired narrative.
8. Analytics MUST aggregate validated evidence without erasing uncertainty or context.
9. Optimization MUST be proposed and approved; it MUST NOT mutate governance automatically.
10. Evolution MUST either open a governed next cycle or record that no change is warranted.

## 3. State contract

| State | Governance obligation | Evidence produced | Transition condition |
| --- | --- | --- | --- |
| Observe | Notice relevant state, event, variance, risk, or opportunity without premature interpretation | Observation with source, time, scope, and confidence | Observation is relevant and collection is authorized |
| Collect | Gather the minimum sufficient evidence with provenance and boundary controls | Evidence set, gaps, data limitations, and custody references | Evidence is adequate for analysis or insufficiency is escalated |
| Analyze | Assess causes, patterns, alternatives, impact, uncertainty, and all six axes | Analysis with assumptions, options, risks, and affected entities | Analysis is reviewable and decision-ready |
| Decision | Select, reject, defer, or request more evidence under proper authority | Decision record, rationale, owner, expected outcome, and evaluation criteria | Approval is valid and conflicts are resolved |
| Rule | Establish or reference enforceable direction required by the decision | Scoped rule or documented reason an existing instrument is sufficient | Rule is constitutional, applicable, and versioned |
| Standard | Define repeatable criteria and evidence by which conformance will be judged | Measurable standard and validation mapping | Criteria are feasible, unambiguous, and approved |
| Execution | Perform the bounded approved action at the responsible layer | Result and execution evidence, including deviations | Work completes within authority or stops safely |
| Validation | Test artifacts and outcomes against rules, standards, contracts, and completion criteria | Pass, fail, or blocked findings with reproducible evidence | Mandatory checks pass or corrective governance begins |
| Analytics | Compare validated results across time and context without overstating causality | Trends, patterns, confidence, and limitations | Findings are sufficient to consider optimization |
| Optimization | Form a bounded improvement proposal with tradeoffs and rollback or containment | Proposal, expected benefit, risk, and evaluation plan | Authorized governance accepts, rejects, or defers proposal |
| Evolution | Update approved architecture, instruments, capabilities, or lifecycle state through controlled change | Versioned change, decision links, migration and evaluation condition | New baseline is validated and begins the next observation cycle |

## 4. Entry and exit

A loop begins with a relevant observation or an unresolved evaluation from the global decision flow. The initial owner MUST establish scope before collection.

A loop iteration ends only when one of the following is recorded:

- an approved and validated evolution establishes a new baseline;
- the decision is to retain the current baseline;
- the matter is rejected as invalid, duplicate, or outside scope;
- the matter is deferred with an owner and resumption condition; or
- an unresolved conflict is escalated to the appropriate authority.

The loop MUST NOT continue indefinitely without a named state, owner, and next condition.

## 5. Relationship to the global decision flow

The governance loop and decision flow serve different scales:

| Governance loop | Decision-flow relationship |
| --- | --- |
| Observe + Collect | Establish the decision flow's Event and evidence provenance |
| Analyze | Corresponds to Analysis and supplies candidate Knowledge |
| Decision | Uses the Decision stage and its authority contract |
| Rule + Standard | Extends the Rule stage with measurable conformance criteria |
| Execution | Corresponds directly, under the same bounded authorization |
| Validation + Analytics | Deepens Evaluation with conformance and longitudinal evidence |
| Optimization + Evolution | Forms and governs the Evolution proposal |

An individual decision MAY complete without a recurring optimization cycle. A systemic or repeated concern SHOULD enter the full governance loop.

## 6. Control gates

The following gates are mandatory:

### Evidence gate

Collection MUST be lawful, authorized, minimal, and traceable. Missing material evidence blocks analysis or MUST be disclosed as accepted uncertainty.

### Authority gate

The decision and derived instruments MUST have the approval required by [Governance](GOVERNANCE.md). A proposal, recommendation, or roadmap line is not approval.

### Boundary gate

Execution MUST have an owner, interface, contract, and declared scope. Changes involving external systems, new Meta OSs, or top-level structure require explicit User approval under [Boundary](BOUNDARY.md).

### Validation gate

Mandatory checks in [Validation Framework](VALIDATION_FRAMEWORK.md) MUST pass before an outcome is declared complete or a release proceeds.

### Evolution gate

Optimization MUST demonstrate need, test reuse of existing Meta OSs or capabilities, assess all six axes, define containment and evaluation, and receive correct approval under [Evolution](EVOLUTION.md).

## 7. Escalation and correction

A state MUST stop and escalate when authority is ambiguous, evidence integrity fails, scope expands, an instrument conflicts, execution deviates materially, or mandatory validation fails.

Correction SHOULD return to the earliest state whose output is no longer valid. A failed validation normally returns to Analysis, Decision, Rule, Standard, or Execution depending on cause; it MUST NOT be relabeled as success to preserve cadence.

## 8. Records and metrics

Each iteration MUST retain sufficient references to connect observation, evidence, decision, instruments, execution, validation, analysis, and evolution. Metrics MUST have a defined purpose, owner, unit, source, context, and interpretation boundary.

Metrics do not create goals or authority. A metric SHOULD NOT be optimized when doing so would undermine the higher-order outcome, a constitutional principle, or an unmeasured stakeholder impact.

## 9. Version boundary

v0.1 defines this loop in documents, registries, and schemas only. Later versions may implement parts of observation, validation, analytics, automation, connectivity, or personal reporting in their assigned Core Meta OS. Such implementation MUST be separately approved, contracted, tested, and released; the v0.1 contract alone grants no runtime authority.
