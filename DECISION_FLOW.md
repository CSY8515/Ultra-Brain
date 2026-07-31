# Ultra Brain Global Decision Flow

## 1. Purpose

The global decision flow defines how a bounded event becomes an authorized action, an evaluated result, and a controlled evolution proposal:

> **Event → Analysis → Knowledge → Decision → Rule → Execution → Evaluation → Evolution**

At v0.1 this is an architecture and record contract only. It does not implement an event listener, decision engine, rule engine, executor, evaluator, or autonomous learner.

## 2. Flow invariants

1. Each stage MUST preserve links to the initiating event and prior-stage evidence.
2. A stage MUST NOT claim completion until its output and exit gate are satisfied.
3. Uncertainty MUST be visible and MUST NOT be converted silently into fact or authority.
4. Execution MUST have a responsible owner, bounded authorization, and validation criteria.
5. Material outcomes MUST be evaluated.
6. Evolution is a governed proposal, not automatic self-modification.
7. A decision MAY stop, return to an earlier stage, or be rejected without reaching execution.

## 3. Stage contract

| Stage | Required work | Required output | Exit gate |
| --- | --- | --- | --- |
| Event | Identify a change, need, signal, conflict, risk, or opportunity; establish source and scope | Event statement with provenance, affected entities, owner, urgency, and initial boundary | Event is genuine, in scope, and assigned for analysis |
| Analysis | Separate facts, assumptions, constraints, causes, impacts, options, and uncertainty | Analysis record with evidence links, alternatives, risks, and six-axis impact | Evidence is sufficient for a decision or gaps are explicitly accepted/escalated |
| Knowledge | Convert validated analysis into reusable, context-bounded understanding | Knowledge references with meaning, provenance, confidence, and applicability | Relevant knowledge is validated and distinct from unsupported inference |
| Decision | Select an option under identified authority and state why | Approved or rejected decision, rationale, owner, expected outcome, and evaluation criteria | Correct authority approves; conflicts and exceptions are resolved |
| Rule | Translate the approved decision into binding direction when repeatability or enforcement is required | New, changed, referenced, or explicitly unnecessary rule/policy/standard with scope and version | Instrument conforms to higher authority and is unambiguous enough for execution |
| Execution | Perform only the authorized work at the responsible layer | Result, change reference, execution evidence, and deviations | Declared work is complete or safely stopped; evidence is available |
| Evaluation | Compare the result with expected outcome, validation criteria, risks, and side effects | Evaluation finding: effective, ineffective, harmful, inconclusive, or superseded | Outcome is accepted, corrective action is opened, or uncertainty is escalated |
| Evolution | Propose retained learning, optimization, contract change, rollback, or retirement | Governed evolution proposal or explicit no-change conclusion | Proposal enters governance; no automatic mutation occurs |

## 4. Decision record minimum

A material decision MUST include:

- decision ID, title, status, and version;
- initiating event and provenance;
- scope, affected entities, owner layer, and primary core axis;
- evidence, analysis, knowledge references, and known uncertainty;
- considered options and material consequences;
- decision, rationale, approving authority, and approval date;
- applicable or derived rules, policies, and standards;
- execution owner, boundary, preconditions, and prohibited actions;
- validation and evaluation criteria;
- result, evaluation, and evolution or supersession references.

The registry schema is canonical for machine-readable fields. [Decision Log](DECISION_LOG.md) is canonical for the human-readable index and rationale summary.

## 5. Authority and responsibility

The flow does not transfer responsibility between stages automatically:

- the event source owns only the accuracy of the supplied signal;
- the analyst owns the quality and limitations of analysis;
- the knowledge owner owns validation and applicability of knowledge;
- the approving authority owns the choice and accepted tradeoffs;
- the relevant governance owner owns any derived instrument;
- the executor owns conformance to authorized scope;
- the validator/evaluator owns the evidence-based finding; and
- the authorized governance layer owns the evolution decision.

One person MAY perform multiple roles, but each role and output MUST remain distinguishable. See [Responsibility](RESPONSIBILITY.md).

## 6. Return, stop, and refusal paths

The flow MUST stop or return when:

- the event is false, duplicated, out of scope, or unowned;
- analysis lacks material evidence;
- knowledge is invalid, stale, or inapplicable;
- authority is missing or instruments conflict;
- execution preconditions or validation fail;
- execution exceeds approved scope; or
- evaluation reveals unacceptable harm or uncertainty.

A stop MUST record the reason, current state, owner, and condition for resumption. Urgency MAY shorten review only through an approved exception; it MUST NOT eliminate authority or safety gates.

## 7. Rules and standards in the flow

The Rule stage determines whether a decision needs a reusable directive. A one-time bounded decision MAY proceed under an existing rule or explicit decision authorization; the record MUST say why no new instrument is required.

Standards are governed more explicitly in the broader [Governance Loop](GOVERNANCE_LOOP.md). A rule defines what must occur; a standard defines repeatable evidence of conformance. Neither substitutes for execution authority.

## 8. Relationship to core axes

- Global Ecosystem identifies affected scope and relationships.
- Global Memory preserves provenance from event through evaluation.
- Global Knowledge governs reusable understanding.
- Global Decision owns decision framing and evaluation linkage.
- Global Governance owns authority and derived instruments.
- Global Capability owns assignment and fitness of the executing capability.

Every material flow MUST conduct the six-axis review in [Core Axis](CORE_AXIS.md).

## 9. v0.1 validation

For v0.1, conformance means the flow is consistently documented, decision records and schemas can represent its required evidence, and no artifact claims that any stage is automated or operational. Future implementations MUST pass separate version approval and contract validation.
