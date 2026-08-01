# Ultra-Brain

Ultra Brain is the user's top-level Second Brain and governance layer. It defines how subordinate Meta OSs and OS ecosystems are identified, governed, connected, validated, and evolved without taking over the implementation responsibilities of those systems.

## Release status

The **v0.1 Foundation** through **v0.5 Collaboration & Connectivity** baselines
remain cumulative. The current release is **v0.6 Personal Secretary**, which
implements only the approved [Personal Secretary Core Meta OS](Personal-Secretary-Core-Meta-OS/README.md)
assistance plane.

v0.6 adds consent-aware daily briefings, weekly and monthly reviews, reminder
views, evidence-linked recommendations, transparent priorities, advisory
decision support, assistance plans, context support, and scheduling proposals.
It stores no personal data, performs no external action, sends no reminder,
books no time, implements no user interface, and runs no background service.

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

## v0.6 boundary

v0.6 activates only Personal Secretary Core Meta OS while preserving the
cumulative v0.1-v0.5 baselines. Its reference runtime is dependency-free,
caller-driven, bounded, Safety-grant-gated, ephemeral, and non-executing. It
has no personal store, memory service, behavioral profile, daemon, timer,
calendar write, message delivery, external I/O, or hidden background loop.
UI/UX, Streamlit, and deployment remain absent.
