# Automation Core Meta OS MASTER Design

## Mission

Automation Core Meta OS executes explicitly approved local workflows while
preserving authority, boundedness, observability, idempotency, failure
containment, recovery evidence, and caller control.

## Invariants

1. Every workflow, event, schedule, routine, batch, grant, and payload is explicit and bounded.
2. Every action is both registered locally and allowlisted by a current approved grant.
3. A Safety decision identifier is mandatory but never manufactured by Automation.
4. Pipelines are acyclic; dependencies complete before dependent steps run.
5. Automatic decisions use declared comparison rules only.
6. Retry, batch size, step count, schedule occurrence, and stored output are bounded.
7. Idempotency keys cannot be reused for different workflow input.
8. Failed pipelines compensate successful compensable steps in reverse order.
9. Audit events and notifications disclose lifecycle state without handler exception text.
10. No background, network, connector, UI, deployment, or later-domain behavior exists.

## Component topology

`AutomationCore` owns an in-memory action allowlist and idempotency ledger.
`WorkflowEngine` validates authorization, resolves the step graph, evaluates
conditions, invokes handlers, applies retries, and compensates on terminal
failure. `TriggerEngine` matches caller-supplied events. `Scheduler` calculates
due occurrences from UTC timestamps. `RoutineEngine` joins schedules to
workflows. `BatchProcessor` runs bounded items with independent idempotency keys.
`NotificationCenter` returns structured local notices as part of each result.

## Information model

- `WorkflowDefinition`: versioned DAG of `WorkflowStep` records.
- `DecisionRule`: field, typed operator, and expected JSON value.
- `TriggerSpec` and `TriggerEvent`: manual, event, or schedule activation data.
- `ScheduleSpec` and `RoutineDefinition`: interval schedule and workflow binding.
- `AuthorizationGrant`: Safety reference, validity window, allowlists, and budgets.
- `ExecutionResult`: immutable status, step results, audit events, notices, and input digest.
- `BatchResult`: ordered independently traceable execution results.

## Execution lifecycle

1. Canonicalize and validate all input before action lookup.
2. Validate grant approval, time window, workflow allowlist, action allowlist, and budgets.
3. Resolve a stable topological order; reject cycles or missing dependencies.
4. Skip a conditioned step when its rule is false; block dependents of skipped steps.
5. Invoke each action with immutable workflow input, parameters, and dependency outputs.
6. Retry failures only up to the workflow limit.
7. On terminal failure, compensate successful steps in reverse order when handlers exist.
8. Record sanitized audit events and local notifications and cache successful key ownership.

## Failure semantics

Validation and authorization failures raise typed errors before execution.
Handler failures become failed or compensated execution results. Exception text
is never copied into results. A compensation failure is recorded and leaves the
run failed. Batch items do not hide one another's outcomes. No failure path
creates an external message, connection, or uncontrolled retry.

## Compatibility

The Python and JSON contract version is `0.4.0`. Additive changes may remain in
`0.4.x`. Enabling background execution, external delivery, persistent services,
dynamic handlers, or weakening authorization requires a new architecture and
contract review.
