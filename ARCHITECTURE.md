# Ultra Brain Architecture

## 1. Purpose

This document defines the v0.1 structural architecture of Ultra Brain: its system boundary, authority layers, artifact planes, dependency direction, and cross-layer contracts. The [MASTER Design](MASTER_DESIGN.md) is the architectural overview; this document is the canonical structural model.

This is a specification, not a runtime design. No component described here is implemented as a service, agent, database, user interface, or automation in v0.1.

## 2. System context

Ultra Brain is the user's top-level Second Brain and governance layer. It governs the coherence of subordinate systems while leaving execution and domain implementation at the narrowest responsible layer.

The context boundary has three directions:

- **Above:** the User supplies intent, authority, approval, and final accountability.
- **Within:** Ultra Brain maintains global governance, memory, decisions, knowledge, capabilities, and ecosystem relationships.
- **Below:** Meta OSs and their descendants implement bounded responsibilities under delegated authority.

Ultra Brain MUST NOT infer that a system is governed merely because it is visible in the same filesystem or repository. Adoption requires explicit registration, ownership, boundary, interface, and contract.

## 3. Canonical layer model

> **User > Ultra Brain > Meta OS > OS Ecosystem > Capability > Project > Module**

### 3.1 Dependency direction

Normative authority and constraints flow from left to right (top to bottom). Evidence, outcomes, risks, and change proposals flow from right to left (bottom to top).

A lower layer:

- MUST comply with applicable higher-layer instruments;
- MUST act only within delegated scope;
- MUST expose required evidence through its contract;
- MUST escalate conflicts it cannot resolve locally; and
- MUST NOT alter a higher layer's artifacts or authority.

A higher layer:

- MUST state the outcome, constraints, and evidence it requires;
- SHOULD avoid prescribing internal implementation below the level necessary for governance;
- MUST NOT silently appropriate a lower layer's implementation responsibility; and
- MUST evaluate results against declared contracts.

See [Responsibility](RESPONSIBILITY.md) for the complete allocation.

## 4. Architectural planes

Ultra Brain organizes foundation artifacts into four planes. The planes are logical classifications, not directories or executable subsystems.

| Plane | Purpose | Principal artifacts |
| --- | --- | --- |
| Authority | Establish permission, precedence, and control | Constitution, governance, rules, policies |
| Structure | Establish identity, ownership, relationships, and boundaries | Architecture, responsibilities, core axes, registries, interfaces, contracts |
| Assurance | Establish measurable conformance and release confidence | Standards, schemas, validation, tests, completion and release criteria |
| Evolution | Preserve decisions and control future change | Decision flow, governance loop, decision log, roadmap, version and changelog |

No plane MAY override the authority hierarchy. For example, a registry records an approved relationship; it does not create authority by itself.

## 5. Global axis model

Every architectural concern MUST have one primary axis from [Core Axis](CORE_AXIS.md):

- Global Governance
- Global Memory
- Global Decision
- Global Knowledge
- Global Capability
- Global Ecosystem

An artifact MAY serve multiple axes but MUST identify a single accountable owner when registered. Cross-axis effects MUST be visible in the decision rationale and validation scope.

## 6. Entity and relationship model

At v0.1, the architecture recognizes these entity classes:

- governed layer entities: Meta OS, OS Ecosystem, Capability, Project, and Module;
- authority entities: rule, policy, and standard;
- coordination entities: interface and contract;
- evidence entities: decision and release;
- repository entities: repositories and registered paths.

Every registered entity MUST have a stable identity, type, name, scope, status, owner layer, parent relationship where applicable, version, and provenance timestamps. Repository and path fields MUST reflect actual structure. The canonical field contract belongs to [Registry Architecture](REGISTRY.md) and the schemas under `schemas/`.

Parent relationships MUST follow the canonical hierarchy unless an approved architectural decision documents why a non-containment relationship is required. Dependencies do not change parentage or transfer ownership.

## 7. Interfaces and contracts

An **interface** describes the observable exchange boundary between governed entities. A **contract** binds that exchange to authority, obligations, evidence, and failure handling.

Every cross-boundary interaction MUST identify:

1. provider and consumer;
2. owning layers and scopes;
3. purpose and permitted data or action;
4. inputs, outputs, and validation criteria;
5. authority and applicable rules, policies, and standards;
6. failure, refusal, and escalation behavior;
7. version and compatibility expectations; and
8. required evidence and audit references.

An interface without an approved contract MUST NOT authorize execution. A contract MUST NOT grant more authority than its parties possess. See `interfaces/README.md`, `contracts/README.md`, and [Boundary](BOUNDARY.md).

## 8. Control topology

The [Decision Flow](DECISION_FLOW.md) converts a bounded event into an evaluated result and possible evolution proposal:

> Event → Analysis → Knowledge → Decision → Rule → Execution → Evaluation → Evolution

The [Governance Loop](GOVERNANCE_LOOP.md) governs recurring change and institutional learning:

> Observe → Collect → Analyze → Decision → Rule → Standard → Execution → Validation → Analytics → Optimization → Evolution

Execution always belongs to an explicitly authorized responsible layer. Ultra Brain's architectural role is to define and verify the contract; this does not make Ultra Brain the executor.

## 9. State and provenance

Documents define normative state; registries describe governed entities; schemas constrain machine-readable structure; the decision log and changelog preserve change provenance; releases establish reviewed baselines.

The following rules apply:

- A file's existence MUST NOT be treated as approval.
- Registry status MUST agree with governing decisions and actual repository state.
- A superseded artifact MUST remain traceable to its successor.
- A release MUST be reproducible from its versioned repository state.
- Sensitive values, credentials, and personal data MUST NOT be stored as foundation evidence.

## 10. Failure containment

Each boundary MUST support refusal and escalation. When evidence is missing, authority is ambiguous, validation fails, or a higher-order conflict is found, the affected action MUST stop before execution or release.

Failures SHOULD be contained at the narrowest affected layer. Escalation proceeds upward to the first layer with authority to resolve the issue, ultimately to the User. Failure containment MUST NOT be bypassed by weakening a rule, relabeling scope, or treating a proposal as approved.

## 11. Repository mapping

The v0.1 repository maps architecture to files as follows:

- root Markdown files hold system-wide foundation contracts;
- `registry/` holds governed entity records;
- `schemas/` holds machine-readable structural constraints;
- `interfaces/` and `contracts/` hold cross-boundary principles and future definitions;
- `validation/` and `tests/` hold foundation verification scope;
- five separate root-level Core Meta OS directories hold scope README files only.

This mapping does not place OS Ecosystem implementation inside Ultra Brain. Existing unrelated or protected workspace content remains outside the governed repository scope unless the User explicitly approves adoption through [Governance](GOVERNANCE.md).

## 12. v0.1 conformance

An architecture change conforms to v0.1 only if it:

- preserves the authority hierarchy and six core axes;
- is consistent with the [Constitution](CONSTITUTION.md);
- assigns scope and responsibility without implementing later-version behavior;
- uses explicit interfaces and contracts for boundary crossings;
- updates affected registries, decisions, and validation evidence together; and
- passes [Validation Framework](VALIDATION_FRAMEWORK.md) and [Completion Rule](COMPLETION_RULE.md).
