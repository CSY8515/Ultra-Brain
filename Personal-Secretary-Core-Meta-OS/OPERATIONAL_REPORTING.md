# Personal Secretary Operational Reporting Architecture

## Purpose

Define how bounded operational summaries reach the user through Personal
Secretary without transferring data ownership, execution authority, or runtime
responsibility.

## Canonical flow

> Source system -> Database Manager or status producer -> registered report adapter -> Personal Secretary operational-report port -> advisory operational brief -> user approval -> optional Automation handoff -> outcome report

Raw databases and business records never cross this boundary. Producers send
summary counts, findings, recommendations, candidate references, and recovery
evidence only.

## Status domains

| Domain | Minimum report content | Owner |
| --- | --- | --- |
| Ultra Brain | version, repository state, current release | Ultra Brain caller or release validator |
| Core Meta OS | component ID, version, status, validation result | Each Core Meta OS |
| Registry | registry ID, entity count, reference status | Ultra Brain Registry authority |
| Validation | gate, revision, result, findings | Validator |
| Release | tag, commit, publication state | Release authority |
| OS Ecosystem | version, project status, capability status | OS Ecosystem |
| Project | project identity, version, health, unresolved issues | Source project |
| Database | record totals, integrity, failures, recovery state | Source Database Manager |

## Verified producer bindings

- living-os.database-management: Living OS Database Management produces a
  read-only envelope and calls the existing aggregation contract.
- universal-learning-engine.operational-reporting: ULE Database Manager
  publishes a versioned summary through its existing Personal Secretary port.
- OS Ecosystem Personal Secretary Capability normalizes only registered
  producers and creates a cross-project advisory brief.

Ultra Brain and OS Ecosystem state reports use the same canonical schema when a
caller supplies them. v0.61 adds no poller, repository reader, network client,
or background collector.

## Recommendation and approval lifecycle

1. Rank findings by explicit priority, severity, unresolved state, and evidence.
2. Produce recommendations with source report IDs.
3. Mark consequential recommendations as approval_required.
4. Record user disposition as requested, approved, rejected, or deferred.
5. Send an approved execution request only to the existing Automation boundary.
6. Receive a bounded outcome report with completed, failed, recovery, or
   rollback state.
7. Present the result to the user and preserve source ownership.

Personal Secretary never treats a recommendation as approval and never executes
or rolls back an action.

## Failure support

Canonical findings support error, failure, incident, warning, recovery, and
rollback. Reports may also retain validation failure, execution failure,
invalid data, rejected decision, and unresolved issue as producer-specific
categories. Every recovery or rollback claim must reference source evidence;
absence of evidence remains unresolved.

## Containment

- Reject unregistered or unidentified sources.
- Reject unbounded, malformed, secret-bearing, or raw-record payloads.
- Preserve report IDs, source IDs, timestamps, contract versions, and evidence.
- Deduplicate only the advisory view; never delete source reports.
- Keep all output advisory until explicit user approval and separate Automation
  authorization.
