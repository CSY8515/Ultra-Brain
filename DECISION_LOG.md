# Ultra Brain Decision Log

## Record policy

This log records material v0.1 Foundation decisions. Entries are append-oriented. A later decision may supersede an earlier entry by ID, but the earlier entry MUST remain visible. Required fields are decision ID, date, status, decision, rationale, consequences, authority, and related artifacts.

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

## Adding a decision

New entries MUST use the next unused `decision-####` identifier, be added to the decision registry, and include the fields above. A superseding entry MUST identify every superseded decision and explain migration or compatibility consequences.
