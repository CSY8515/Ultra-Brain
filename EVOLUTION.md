# Ultra Brain Evolution

## Purpose and boundary

Evolution is controlled change that improves Ultra Brain without fragmenting authority, duplicating capability, or weakening safety. This v0.1 document defines the gate only. It does not authorize or implement a new Meta OS, capability, runtime, integration, or UI.

## Principles

Evolution MUST be evidence-led, reuse-first, reversible where practical, compatible with higher-authority rules, and traceable to a decision. Novelty alone is not a need. Organizational symmetry alone is not a reason to create a component.

The smallest existing owner capable of meeting the need SHOULD receive the change. A new Meta OS is the last architectural option, not the default.

## Evolution Gate

A proposal MUST pass these stages in order:

1. **Need test** — State the user or system outcome, evidence, urgency, success measure, constraints, and cost of not acting. If the need is unproven, stop.
2. **Reuse an existing Meta OS?** — Evaluate every relevant Meta OS scope and document why reuse or a bounded extension can or cannot meet the need. If it can, route the proposal there and do not create a new Meta OS.
3. **Reuse an existing Capability?** — Search the capability registry and relevant contracts for reuse, composition, or a small extension. If an existing capability can meet the need, use it and do not duplicate it.
4. **Architecture review** — Evaluate ownership, boundaries, dependencies, data, interfaces, contracts, registry effects, safety, compatibility, migration, validation, release, and retirement. Unresolved critical risk stops the proposal.
5. **User approval** — Present the recommended option, alternatives, evidence, risk, cost, scope, and review outcome. Approval MUST be explicit and recorded in [DECISION_LOG.md](DECISION_LOG.md).
6. **Development** — Development MAY begin only after stages 1–5 pass. It MUST follow the approved scope and [DEVELOPMENT_STANDARD.md](DEVELOPMENT_STANDARD.md).

No stage may be inferred from silence, reordered, or bypassed. A failed stage returns the proposal for revision or closes it.

## Architecture review outcomes

The review MUST recommend exactly one primary outcome:

- reject or defer because the need or readiness is insufficient;
- use an existing capability unchanged;
- extend or compose an existing capability;
- extend an existing Meta OS within its boundary;
- create a new capability under an existing owner;
- propose a new Meta OS, with evidence that all reuse paths fail.

## Required proposal record

The proposal record MUST include a stable ID, owner, target version, need, evidence, considered reuse candidates, architectural impact, interface and contract impact, security and privacy impact, validation plan, release plan, rollback or retirement plan, review result, User decision, and links to affected registry entries.

## Lifecycle review

Approved evolution remains subject to evaluation after release. The owner MUST compare actual outcomes with success measures and MAY propose continuation, correction, consolidation, or retirement through the same governance system. Material expansion repeats the Evolution Gate.

## v0.1 application

The five Core Meta OS directories are approved scope placeholders from the v0.1 mandate, not implemented systems. Their later implementation remains bound to the target version, architecture, validation, and release gates in the roadmap.
