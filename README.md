# Ultra-Brain

Ultra Brain is the user's top-level Second Brain and governance layer. It defines how subordinate Meta OSs and OS ecosystems are identified, governed, connected, validated, and evolved without taking over the implementation responsibilities of those systems.

## Release status

The **v0.1 Foundation**, **v0.2 Safety**, and **v0.3 Enhancement** baselines
remain cumulative. The current release is **v0.4 Automation**, which implements
only the approved [Automation Core Meta OS](Automation-Core-Meta-OS/README.md)
execution plane.

v0.4 adds bounded workflows, explicit triggers and interval schedules,
caller-driven routines, deterministic decisions, registered local action
execution, dependency pipelines, batches, idempotency, retries, compensation,
audit events, and local notifications. It does not implement a user interface,
background service, external connectivity, another Core Meta OS, or a
lower-layer business product.

The canonical authority hierarchy is:

> **User > Ultra Brain > Meta OS > OS Ecosystem > Capability > Project > Module**

A lower layer MUST remain within the authority delegated by every layer above it. Cross-layer activity MUST use an explicit interface and contract; physical proximity in a repository does not grant authority.

## System identity

Ultra Brain governs through six permanent core axes:

1. **Global Governance** — authority, constitutional control, and accountable change.
2. **Global Memory** — durable history, provenance, and continuity.
3. **Global Decision** — decision framing, authorization, and evaluation.
4. **Global Knowledge** — validated meaning, models, and reusable understanding.
5. **Global Capability** — capability identity, ownership, lifecycle, and fitness.
6. **Global Ecosystem** — system topology, dependencies, boundaries, and health.

The global decision flow is:

> **Event → Analysis → Knowledge → Decision → Rule → Execution → Evaluation → Evolution**

The governance loop is:

> **Observe → Collect → Analyze → Decision → Rule → Standard → Execution → Validation → Analytics → Optimization → Evolution**

At v0.1, both sequences are architecture contracts only. No autonomous observation, execution, analytics, or optimization is implemented.

## Foundation documents

Start with the [MASTER Design](MASTER_DESIGN.md), then use the following documents by concern:

| Concern | Canonical document |
| --- | --- |
| Structural model and dependency direction | [Architecture](ARCHITECTURE.md) |
| Highest-order authority and invariants | [Constitution](CONSTITUTION.md) |
| Decision rights and controlled change | [Governance](GOVERNANCE.md) |
| Layer and owner accountability | [Responsibility](RESPONSIBILITY.md) |
| Included, excluded, and protected scope | [Boundary](BOUNDARY.md) |
| Six permanent system perspectives | [Core Axis](CORE_AXIS.md) |
| Decision lifecycle | [Decision Flow](DECISION_FLOW.md) |
| Continuous governance lifecycle | [Governance Loop](GOVERNANCE_LOOP.md) |
| Enforceable directives | [Rules](RULES.md) |
| Contextual constraints | [Policies](POLICIES.md) |
| Repeatable conformance criteria | [Standards](STANDARDS.md) |
| Registry model | [Registry Architecture](REGISTRY.md) |
| Evolution controls | [Evolution](EVOLUTION.md) |
| Validation and release | [Validation Framework](VALIDATION_FRAMEWORK.md) and [Release Framework](RELEASE_FRAMEWORK.md) |
| Repository and workspace safety | [Repository Strategy](REPOSITORY_STRATEGY.md) and [Workspace Protection](WORKSPACE_PROTECTION.md) |
| Version plan | [Roadmap](ROADMAP.md) |

If documents conflict, apply the precedence rules in the [Constitution](CONSTITUTION.md) and record the resolution through [Governance](GOVERNANCE.md). Definitions are centralized in [Terminology](TERMINOLOGY.md).

## v0.1 boundary

The foundation MAY describe later versions so that present contracts remain forward-compatible. Such descriptions are roadmap intent, not implemented capability or authorization to implement it. In particular, v0.1 contains no UI/UX, automation, external AI integration, persistent application service, scheduler, monitoring agent, or Meta OS runtime.

The repository root is the sole Ultra Brain repository root. A nested Ultra-Brain repository MUST NOT be created. Neighboring or pre-existing projects, including any OS Ecosystem workspace content, remain outside this foundation and MUST NOT be modified or silently adopted.

## v0.4 boundary

v0.4 activates only Automation Core Meta OS while preserving Safety Core v0.2
and Enhancement Core v0.3. Its reference runtime is local, dependency-free,
caller-driven, bounded, Safety-grant-gated, and observable. It has no daemon,
external event collection, dynamic code loading, network delivery, or hidden
background loop. Collaboration & Connectivity and Personal Secretary remain
scope-only future milestones; UI/UX, Streamlit, and deployment remain absent.
