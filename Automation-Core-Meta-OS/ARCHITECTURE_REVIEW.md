# v0.4 Automation Core Meta OS Architecture Review

## Decision

The approved need belongs to the existing `automation-core-meta-os`. No new Meta
OS, OS Ecosystem, or Core Capability is justified. Product implementation is
confined to `Automation-Core-Meta-OS/`, apart from minimum v0.4 release
registration at repository root, and inherits the v0.1 Foundation, v0.2 Safety,
and v0.3 Enhancement boundaries.

## Architecture choice

Use a local standard-library Python package with immutable records and JSON
artifacts. A caller explicitly supplies time, events, workflow input,
authorization, and registered action handlers. There is no daemon, queue worker,
network client, subprocess, dynamic import, persistent service, or hidden loop.

> Validate -> Authorize -> Match trigger or schedule -> Resolve dependency graph -> Decide -> Execute registered actions -> Retry or compensate -> Audit -> Emit local notices -> Return result

## Authority and containment

- A grant must be explicitly approved, current, Safety-referenced, and limited by
  workflow, action, step, batch, and notification permissions.
- Registration does not authorize execution; the grant is checked for every run.
- Handler exceptions are contained, messages are not exposed, retry is bounded,
  and compensation runs in reverse successful-step order.
- Idempotency is local to the runtime instance and returns the stored result for
  the same workflow and key; conflicting reuse fails closed.
- Automatic decisions are typed comparisons against explicit context fields.
- Schedules are calculations evaluated by caller ticks, never background jobs.
- Notifications are local data records, never externally delivered messages.

## Cumulative controls

Safety remains the authority for approval and risk decisions; Automation only
verifies the explicit grant presented to it. Enhancement remains advisory and
is not modified or silently invoked. Connectivity, Personal Secretary, UI/UX,
and later product layers remain outside scope.

## Approval outcome

Architecture Review: approved for the bounded v0.4 implementation under the
explicit User mandate dated 2026-08-01. Release remains conditional on complete
validation, automatic tests, protected-scope review, version and registry
coherence, commit, push, tag, and GitHub Release verification.
