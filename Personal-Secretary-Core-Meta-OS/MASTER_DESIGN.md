# Personal Secretary Core Meta OS MASTER Design

## Mission

Provide consent-aware personal coordination and assistance that turns explicit,
bounded, caller-supplied context into transparent preparation and advisory
outputs while preserving personal authority, privacy, provenance, and
non-execution.

## Invariants

1. Every operation requires a current approved Safety-referenced grant.
2. Grants explicitly allow operations, context categories, item counts, horizon,
   and sensitive-context use.
3. All personal records are supplied by the caller and remain ephemeral.
4. Briefings and reviews report source identifiers and fixed period boundaries.
5. Reminders are due/upcoming views; no timer or notification is created.
6. Recommendations cite evidence and remain advisory.
7. Priority scores expose reasons and never overwrite caller records.
8. Decision support ranks caller-scored options but never decides or executes.
9. Context matches preserve category, source, and observed time.
10. Scheduling support returns open slots/conflicts and never books time.
11. No external I/O, persistence, daemon, UI, deployment, or hidden inference exists.

## Component topology

`PersonalSecretaryCore` validates authorization and coordinates six pure
services: briefing/review, reminder support, priority management,
recommendation, decision/assistance support, and context/scheduling support.
Immutable public records cross the boundary. The clock is caller-injectable for
reproducible time behavior.

## Information model

- `SecretaryGrant`: user identity, Safety reference, validity, allowlists, and budgets.
- `Task`: status, due time, importance, effort, category, and sensitivity.
- `ScheduleItem`: explicit time interval, category, confirmation, and sensitivity.
- `Reminder`: reminder time, source reference, acknowledgement, and sensitivity.
- `Goal`: period, status, and bounded progress.
- `ContextItem`: category, content, observation time, source, and sensitivity.
- `DecisionOption`: caller-defined criterion scores from zero to one.
- Output records: briefing, review, priority plan, recommendations, decision
  analysis, assistance plan, context result, and schedule plan.

## Operation lifecycle

1. Validate the grant and operation at the injected current time.
2. Validate all records, uniqueness, item budgets, allowed categories, sensitive
   flags, and requested horizon.
3. Compute a deterministic view using only explicit fields.
4. Preserve source IDs and produce score/evidence explanations.
5. Return an immutable result without retaining input or output.

## Compatibility

The Python and JSON contract version is `0.6.0`. Additive changes may remain in
`0.6.x`. Persistence, autonomous action, background reminders, calendar writes,
external services, behavioral profiling, or inferred sensitive data require a
new architecture and contract review.
