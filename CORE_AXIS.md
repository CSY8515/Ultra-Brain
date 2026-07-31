# Ultra Brain Core Axis

## 1. Purpose

The six core axes are permanent views through which Ultra Brain governs the whole system. They prevent global concerns from becoming fragmented across subordinate implementations.

Axes are classification and accountability contracts at v0.1. They are not services, engines, databases, agents, or user-interface modules.

## 2. Axis rules

1. Every material entity, decision, contract, and change MUST name one primary axis.
2. Effects on the other five axes MUST be considered for architectural and release decisions.
3. An axis classification does not change an entity's owner layer or parent.
4. Cross-axis work MUST use shared identities and explicit contracts rather than duplicate records.
5. No axis may override the [Constitution](CONSTITUTION.md) or authority hierarchy.
6. Adding, removing, or redefining an axis requires a constitutional amendment.

## 3. Global Governance

**Question:** Who may decide, under which constraints, and with what accountability?

Global Governance owns the coherence of authority, constitutional constraints, decisions, rules, policies, standards, approval, escalation, and exceptions.

It accepts user intent, proposals, impact assessments, conflicts, and evaluation results. It produces approved authority, decision rationale, governing instruments, and escalation outcomes.

It MUST NOT implement subordinate behavior, fabricate consent, or treat successful execution as retrospective approval. Its detailed mechanisms are defined in [Governance](GOVERNANCE.md).

## 4. Global Memory

**Question:** What must remain durable and traceable across time?

Global Memory owns continuity and provenance across decisions, entities, versions, changes, evaluations, and releases. It distinguishes current state from historical state and preserves supersession relationships.

It accepts verified records and evidence references. It produces traceable history sufficient to explain present governance state.

It MUST NOT become an unrestricted archive of secrets or personal data. It records that knowledge or evidence existed and where it came from; it does not decide whether an interpretation is valid.

## 5. Global Decision

**Question:** How does evidence become an authorized and evaluable choice?

Global Decision owns decision framing, alternatives, authority, rationale, expected outcomes, and evaluation criteria. It connects a triggering event to an enforceable result through [Decision Flow](DECISION_FLOW.md).

It accepts events, evidence, analysis, knowledge, constraints, and risk. It produces a decision record, derived authority artifacts where required, execution authorization, and evaluation conditions.

It MUST NOT bypass governance approval, confuse a recommendation with a decision, or execute the decision itself unless a separately responsible layer is authorized to do so.

## 6. Global Knowledge

**Question:** What validated understanding can be reused to make better decisions?

Global Knowledge owns concepts, interpretations, models, evidence relationships, confidence, and applicability. It converts analysis into reusable meaning while preserving provenance to Global Memory.

It accepts observations, sources, analysis, validation status, and context. It produces knowledge references and explicit uncertainty or applicability boundaries.

It MUST NOT present unsupported inference as fact, replace source provenance, or create authority merely because information is believed to be true.

## 7. Global Capability

**Question:** What can the governed system do, who owns it, and is it fit for use?

Global Capability owns capability identity, scope, owner, consumer, contract, lifecycle, dependencies, fitness, and reuse across ecosystems.

It accepts approved needs, architecture boundaries, interface contracts, project outcomes, and validation evidence. It produces capability definitions, lifecycle status, and fitness assessments.

It MUST NOT equate a planned feature with an active capability, duplicate an existing capability without review, or assign implementation to Ultra Brain solely because the capability has global value.

## 8. Global Ecosystem

**Question:** How do governed systems relate while retaining clear boundaries and ownership?

Global Ecosystem owns the global topology of Meta OSs, OS ecosystems, capabilities, repositories, dependencies, interfaces, contracts, and lifecycle relationships.

It accepts registered entities, ownership, dependency and compatibility evidence, and boundary decisions. It produces coherent relationship maps and impact scope.

It MUST NOT treat proximity as integration, a dependency as ownership, or an external project as governed without approval. See [Boundary](BOUNDARY.md).

## 9. Axis interaction contract

The axes cooperate in this order without forming a rigid runtime pipeline:

1. Global Ecosystem locates affected entities and boundaries.
2. Global Memory supplies provenance and prior state.
3. Global Knowledge supplies validated understanding and uncertainty.
4. Global Decision frames and records the authorized choice.
5. Global Governance validates authority and establishes binding instruments.
6. Global Capability assigns fulfillment and measures fitness.
7. All axes receive evaluation evidence and update only through governed evolution.

No axis MAY maintain an incompatible identity for the same entity. Registry identity and approved decisions are the shared references.

## 10. Six-axis impact review

A material proposal MUST answer:

| Axis | Required review question |
| --- | --- |
| Governance | Does authority, precedence, accountability, or exception scope change? |
| Memory | What history and provenance must be preserved? |
| Decision | What choice, alternatives, rationale, and evaluation condition exist? |
| Knowledge | What is known, uncertain, inferred, or context-limited? |
| Capability | What ability, owner, consumer, lifecycle, or fitness changes? |
| Ecosystem | What entity, boundary, dependency, interface, or contract changes? |

An unanswered material question blocks approval or MUST be recorded explicitly as accepted uncertainty by the authorized decision maker.

## 11. v0.1 conformance

v0.1 conforms when documents and registries use these six names consistently, assign concerns without creating runtime components, distinguish Memory from Knowledge and Decision from Governance, and validate cross-axis effects before release.
