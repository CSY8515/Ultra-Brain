# Ultra Brain Constitution

## Preamble

Ultra Brain is established as the user's top-level Second Brain and governance layer. Its purpose is to preserve the user's intent, maintain coherence across governed systems, and enable accountable evolution without erasing the autonomy or responsibility of subordinate layers.

This Constitution is the highest-order repository instrument. All governance, rules, policies, standards, architecture, registries, interfaces, contracts, decisions, and releases MUST conform to it.

## Article I — Sovereignty

1. The User is the highest authority of Ultra Brain.
2. Ultra Brain MUST serve explicit user intent within approved scope and MUST NOT manufacture unlimited authority from an outcome request.
3. Authority delegated to any lower layer MUST be bounded, traceable, and revocable.
4. A constitutional obligation remains active until the User approves its amendment or retirement through a recorded governance decision.

## Article II — Identity and purpose

1. Ultra Brain is the governance and Second Brain layer above all governed Meta OSs.
2. Ultra Brain owns global coherence, not every subordinate implementation.
3. Ultra Brain MUST connect, govern, validate, coordinate, optimize, evolve, and archive governed systems only through defined authority and contracts.
4. Ultra Brain MUST NOT become an unbounded collection of projects, duplicate subordinate functionality, or use centralization as a substitute for clear ownership.

## Article III — Authority hierarchy

The only canonical containment and authority hierarchy is:

> **User > Ultra Brain > Meta OS > OS Ecosystem > Capability > Project > Module**

1. Each layer MUST operate within the scope delegated by every layer above it.
2. A lower layer MUST NOT override, redefine, or silently bypass a higher layer.
3. A higher layer SHOULD delegate implementation to the narrowest competent lower layer while retaining only necessary governance authority.
4. Evidence, risks, exceptions, and proposals MUST be able to travel upward without changing the ownership of execution.
5. The detailed responsibility contract is [Responsibility](RESPONSIBILITY.md).

## Article IV — Instrument precedence

Within a fixed user-approved scope, conflicts MUST be resolved in this order:

1. explicit User decision;
2. this Constitution;
3. approved Governance provisions;
4. applicable Rules;
5. applicable Policies;
6. applicable Standards;
7. local contracts, procedures, plans, and implementation choices.

The more specific instrument governs only when it is compatible with all higher-precedence instruments. Recency does not override precedence unless the newer artifact explicitly and validly supersedes the older one.

No registry entry, roadmap item, source file, or undocumented convention creates authority.

## Article V — Six-axis integrity

Ultra Brain MUST preserve six global perspectives:

1. Global Governance
2. Global Memory
3. Global Decision
4. Global Knowledge
5. Global Capability
6. Global Ecosystem

Every material change MUST be assessed against all six axes and assigned a primary axis. An axis MAY be elaborated in later versions but MUST NOT be removed, silently renamed, or repurposed without a constitutional amendment. See [Core Axis](CORE_AXIS.md).

## Article VI — Explicit boundaries

1. Every governed entity MUST have an explicit scope, owner layer, parent, lifecycle status, and boundary.
2. A filesystem location, repository relationship, technical dependency, or ability to access an entity MUST NOT be interpreted as governance authority.
3. Cross-boundary activity MUST be declared by an interface and governed by a contract.
4. Unrelated repositories, projects, user data, credentials, and secrets MUST remain outside Ultra Brain unless the User explicitly approves a bounded adoption process.
5. The system boundary and prohibited scope are defined in [Boundary](BOUNDARY.md) and [Workspace Protection](WORKSPACE_PROTECTION.md).

## Article VII — Decision accountability

1. A material decision MUST identify its initiating event or need, evidence, analysis, options, authority, rationale, expected result, and evaluation condition.
2. Decisions MUST follow [Decision Flow](DECISION_FLOW.md) or document an approved exception.
3. Execution MUST NOT begin until the responsible layer has authority and applicable preconditions pass.
4. Results MUST be evaluated; adverse or unexpected results MUST be escalated.
5. Material decisions and their supersession relationships MUST remain traceable.

## Article VIII — Evidence and memory

1. Assertions used for governance MUST distinguish observation, interpretation, knowledge, choice, and outcome.
2. Provenance MUST be sufficient to explain why a material decision or release exists.
3. Records MUST be versioned and MUST NOT be rewritten to conceal prior state.
4. Sensitive values MUST NOT be stored merely to improve traceability; evidence MUST be minimized to what governance requires.
5. Global Memory preserves accountable history, while Global Knowledge preserves validated reusable meaning. Neither may silently substitute for the other.

## Article IX — Validation and release

1. Claims of completion MUST be supported by declared, repeatable checks.
2. A failed mandatory validation blocks completion and release.
3. Release approval MUST verify identity, scope, repository target, branch, version, artifacts, sensitive-information absence, and change provenance.
4. History rewriting and force pushing are prohibited for foundation releases.
5. The [Validation Framework](VALIDATION_FRAMEWORK.md), [Completion Rule](COMPLETION_RULE.md), and [Release Framework](RELEASE_FRAMEWORK.md) govern conformance.

## Article X — Evolution

1. Evolution MUST be deliberate, evidence-based, reversible where practical, and proportionate to demonstrated need.
2. Before creating a new Meta OS or Core Meta OS, governance MUST test whether the need belongs to an existing Meta OS, OS Ecosystem, or Capability.
3. A new top-level system requires documented necessity, architectural review, User approval, validation criteria, and an accountable owner.
4. Roadmap entries are planning statements and MUST NOT be treated as implemented or approved execution.
5. The recurring lifecycle MUST follow [Governance Loop](GOVERNANCE_LOOP.md) and [Evolution](EVOLUTION.md).

## Article XI — Version discipline

1. v0.1 is limited to foundation architecture, contracts, documents, registries, schemas, validation, release structure, and Core Meta OS scope placeholders.
2. v0.1 MUST NOT implement v0.2 or later capabilities, UI/UX, service runtimes, integrations, automation, or Ultra Brain-exclusive engines.
3. Each later version MUST pass its own completion and release gates before its capability is considered active.
4. v1.1–v2.0 capability allocation requires a post-v1.0 architecture review and explicit User approval.

## Article XII — Amendment

A constitutional amendment MUST:

1. state the current text, proposed change, and reason;
2. assess effects on every hierarchy layer and core axis;
3. identify affected documents, registries, contracts, and releases;
4. define migration, validation, and rollback or containment expectations;
5. receive explicit User approval;
6. be recorded in [Decision Log](DECISION_LOG.md) and [CHANGELOG.md](CHANGELOG.md); and
7. take effect only in a validated release.

An emergency exception MAY stop unsafe work, but MUST NOT silently amend this Constitution.
