# Ultra Brain Decision Log

## Record policy

This log records material Ultra Brain decisions beginning with the v0.1
Foundation. Entries are append-oriented. A later decision may supersede an
earlier entry by ID, but the earlier entry MUST remain visible. Required fields
are decision ID, date, status, decision, rationale, consequences, authority, and
related artifacts.

## decision-0001 — Single Repository Strategy

- **Date:** 2026-07-31
- **Status:** `accepted`
- **Decision:** Ultra Brain uses `https://github.com/CSY8515/Ultra-Brain.git` as its only canonical repository, `main` as the release branch, and the current `Ultra Brain` workspace itself as the Git root. No nested `Ultra-Brain` clone or nested repository is permitted.
- **Rationale:** One root prevents ambiguous ownership, accidental publication, and fragmented history.
- **Consequences:** Foundation and Core Meta OS scopes are versioned together; repository splitting requires a future Evolution Gate decision.
- **Authority:** User v0.1 Foundation mandate
- **Related:** [REPOSITORY_STRATEGY.md](REPOSITORY_STRATEGY.md), [WORKSPACE_PROTECTION.md](WORKSPACE_PROTECTION.md)

## decision-0002 — Version-Bounded Development

- **Date:** 2026-07-31
- **Status:** `accepted`
- **Decision:** v0.1 establishes governance, architecture, registries, schemas, interface and contract guidance, validation, release guidance, and repository scope. It does not implement runtime behavior, UI/UX, or any v0.2+ feature.
- **Rationale:** Stable authority and boundaries must precede feature development.
- **Consequences:** Future-version functionality may appear only as clearly labeled scope or roadmap material.
- **Authority:** User v0.1 Foundation mandate
- **Related:** [ROADMAP.md](ROADMAP.md), [MASTER_DESIGN.md](MASTER_DESIGN.md), [COMPLETION_RULE.md](COMPLETION_RULE.md)

## decision-0003 — Deferred Official UI and UX

- **Date:** 2026-07-31
- **Status:** `accepted`
- **Decision:** Official UI and UX implementation is deferred to the v0.7–v0.9 sequence, after the five Core Meta OS scopes assigned to v0.2–v0.6 have stabilized. v0.1 contains no UI, page, component, style, or interaction implementation.
- **Rationale:** Interface implementation before the governed system boundaries stabilize would encode premature assumptions and blur milestone completion.
- **Consequences:** v0.1 may document the roadmap boundary but cannot claim or contain UI/UX implementation.
- **Authority:** User v0.1 Foundation mandate
- **Related:** [ROADMAP.md](ROADMAP.md), [MASTER_DESIGN.md](MASTER_DESIGN.md), [COMPLETION_RULE.md](COMPLETION_RULE.md)

## decision-0004 - Activate Safety Core Meta OS v0.2

- **Date:** 2026-08-01
- **Status:** `accepted`
- **Decision:** Implement and release the existing `safety-core-meta-os` scope
  as the v0.2 Safety control plane. Product implementation remains centered in
  `Safety-Core-Meta-OS/`; root changes are limited to v0.2 version, changelog,
  roadmap, status, decision, registry, validation, test, and release integration.
- **Rationale:** Later milestones require enforceable, testable validation,
  integrity, monitoring, risk, logging, audit, recovery, execution-safety, and
  incident controls while the v0.1 Foundation remains unchanged.
- **Consequences:** Safety decisions are fail-closed and separate from business
  execution. Other Core Meta OSs, UI/UX, Streamlit, Core Capability, OS
  Ecosystem, Living OS, ULE, and Ultra Brain-exclusive capabilities remain
  outside scope.
- **Authority:** Explicit User approval on 2026-08-01 after Architecture Review
- **Related:** [Safety Architecture Review](Safety-Core-Meta-OS/ARCHITECTURE_REVIEW.md),
  [Safety MASTER Design](Safety-Core-Meta-OS/MASTER_DESIGN.md),
  [ROADMAP.md](ROADMAP.md)

## decision-0005 - Activate Enhancement Core Meta OS v0.3

- **Date:** 2026-08-01
- **Status:** `accepted`
- **Decision:** Implement and release the existing `enhancement-core-meta-os`
  scope as the v0.3 governed assistance plane. Product implementation remains
  inside `Enhancement-Core-Meta-OS/`; root changes are limited to v0.3 release
  registration, validation, tests, and documentation status.
- **Rationale:** Ultra Brain requires evidence-linked analytics, bounded learning,
  patterns, knowledge candidates, optimization, draft rules, predictions,
  insights, and advisory decision support without granting execution authority.
- **Consequences:** v0.2 Safety remains cumulative. Outputs are deterministic and
  non-executing; knowledge and rules remain candidates; decisions remain human-
  owned. Automation, external connectivity, Personal Secretary, UI/UX, Streamlit,
  Core Capability, OS Ecosystem, Living OS, and ULE remain outside scope.
- **Authority:** Explicit User mandate on 2026-08-01
- **Related:** [Enhancement Architecture Review](Enhancement-Core-Meta-OS/ARCHITECTURE_REVIEW.md),
  [Enhancement MASTER Design](Enhancement-Core-Meta-OS/MASTER_DESIGN.md),
  [ROADMAP.md](ROADMAP.md)

## decision-0006 - Activate Automation Core Meta OS v0.4

- **Date:** 2026-08-01
- **Status:** `accepted`
- **Decision:** Implement and release the existing `automation-core-meta-os`
  scope as the v0.4 controlled local execution plane. Product implementation
  remains inside `Automation-Core-Meta-OS/`; root changes are limited to v0.4
  release registration, validation, tests, and documentation status.
- **Rationale:** Ultra Brain requires governed workflows, schedules, triggers,
  routines, registered local action execution, typed automatic decisions,
  pipelines, batches, and notifications with bounded, observable, recoverable
  behavior.
- **Consequences:** v0.2 Safety and v0.3 Enhancement remain cumulative. Every
  execution requires a caller-supplied Safety-referenced grant and registered
  allowlisted handler. Background services, external connectivity,
  Collaboration & Connectivity, Personal Secretary, UI/UX, Streamlit, Core
  Capability, OS Ecosystem, Living OS, ULE, and deployment remain outside scope.
- **Authority:** Explicit User mandate on 2026-08-01
- **Related:** [Automation Architecture Review](Automation-Core-Meta-OS/ARCHITECTURE_REVIEW.md),
  [Automation MASTER Design](Automation-Core-Meta-OS/MASTER_DESIGN.md),
  [ROADMAP.md](ROADMAP.md)

## decision-0007 - Activate Collaboration & Connectivity Core Meta OS v0.5

- **Date:** 2026-08-01
- **Status:** `accepted`
- **Decision:** Implement and release the existing
  `collaboration-connectivity-core-meta-os` scope as the v0.5 governed exchange
  plane. Product implementation remains inside
  `Collaboration-Connectivity-Core-Meta-OS/`; root changes are limited to v0.5
  release registration, validation, tests, and documentation status.
- **Rationale:** Ultra Brain requires bounded APIs, connectors, portable data,
  synchronization, cross-platform exchange, repository access, external AI,
  communication, and ecosystem connectivity without storing credentials or
  granting implicit external authority.
- **Consequences:** v0.1-v0.4 remain cumulative. Every external operation uses a
  registered caller-supplied transport and a current Safety-referenced grant.
  Personal Secretary, UI/UX, Streamlit, Core Capability, OS Ecosystem
  implementation, Living OS, ULE, Ultra Brain-exclusive capability, and
  deployment remain outside scope.
- **Authority:** Explicit User mandate on 2026-08-01
- **Related:** [Connectivity Architecture Review](Collaboration-Connectivity-Core-Meta-OS/ARCHITECTURE_REVIEW.md),
  [Connectivity MASTER Design](Collaboration-Connectivity-Core-Meta-OS/MASTER_DESIGN.md),
  [ROADMAP.md](ROADMAP.md)

## decision-0008 - Activate Personal Secretary Core Meta OS v0.6

- **Date:** 2026-08-01
- **Status:** `accepted`
- **Decision:** Implement and release the existing
  `personal-secretary-core-meta-os` scope as the v0.6 consent-aware personal
  assistance plane. Product implementation remains inside
  `Personal-Secretary-Core-Meta-OS/`; root changes are limited to v0.6 release
  registration, validation, tests, and documentation status.
- **Rationale:** Ultra Brain requires bounded daily and periodic preparation,
  reminders, priorities, recommendations, decision support, context support,
  personal assistance, and scheduling proposals without retaining personal
  data or granting action authority.
- **Consequences:** v0.1-v0.5 remain cumulative. Every operation requires a
  current Safety-referenced grant. Outputs are caller-data-only, provenance-
  preserving, advisory, ephemeral, and non-executing. UI/UX, Streamlit, Core
  Capability, OS Ecosystem implementation, Living OS, ULE, Ultra Brain-
  exclusive capability, autonomous action, and deployment remain outside scope.
- **Authority:** Explicit User mandate on 2026-08-01
- **Related:** [Personal Secretary Architecture Review](Personal-Secretary-Core-Meta-OS/ARCHITECTURE_REVIEW.md),
  [Personal Secretary MASTER Design](Personal-Secretary-Core-Meta-OS/MASTER_DESIGN.md),
  [ROADMAP.md](ROADMAP.md)

## decision-0009 - Recover Personal Secretary Operational Architecture v0.61

- **Date:** 2026-08-03
- **Status:** accepted
- **Decision:** Release v0.61 as an Architecture hotfix that restores the
  Personal Secretary operational-reporting port, Database Report and advisory
  brief schemas, OS Ecosystem and project ownership mappings, recommendation
  approval lifecycle, outcome reporting, and failure/recovery/rollback support.
- **Rationale:** The v0.6 runtime implemented personal assistance services, but
  its Core Architecture did not register the existing Living OS, Universal
  Learning Engine, and OS Ecosystem operational-report relationships or define
  Ultra Brain and ecosystem status-report domains.
- **Consequences:** The v0.6 Python runtime remains unchanged. Living OS, ULE,
  OS Ecosystem, and source databases retain ownership and execution authority.
  The recovered Core port is advisory, summary-only, evidence-linked, and
  requires explicit user approval before any separate Automation handoff.
- **Authority:** Explicit User v0.61 hotfix mandate on 2026-08-03
- **Related:** [v0.61 Architecture Audit](Personal-Secretary-Core-Meta-OS/ARCHITECTURE_AUDIT_v0.61.md),
  [Operational Reporting Architecture](Personal-Secretary-Core-Meta-OS/OPERATIONAL_REPORTING.md),
  [ROADMAP.md](ROADMAP.md)

## Adding a decision

New entries MUST use the next unused `decision-####` identifier, be added to the decision registry, and include the fields above. A superseding entry MUST identify every superseded decision and explain migration or compatibility consequences.
