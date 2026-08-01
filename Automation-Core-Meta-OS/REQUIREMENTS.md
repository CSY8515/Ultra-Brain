# Automation Core Meta OS Requirements

| ID | Requirement | Evidence |
| --- | --- | --- |
| AUT-WFL-001 | Execute only valid bounded acyclic workflows. | Workflow and adversarial tests |
| AUT-SCH-001 | Evaluate schedules deterministically on explicit ticks. | Scheduler tests |
| AUT-TRG-001 | Match typed triggers and filters without collecting events. | Trigger tests |
| AUT-RTN-001 | Bind workflows to schedules as caller-driven routines. | Routine tests |
| AUT-EXE-001 | Invoke only registered actions allowed by a valid Safety-referenced grant. | Authorization tests |
| AUT-DEC-001 | Make automatic decisions only through explicit typed rules. | Decision tests |
| AUT-PIP-001 | Respect dependency order and propagate step outputs. | Pipeline tests |
| AUT-BAT-001 | Bound batch size and isolate item results. | Batch tests |
| AUT-NOT-001 | Produce local structured notifications without delivery connectors. | Notification tests |
| AUT-REL-001 | Support idempotency, bounded retry, cancellation, compensation, and audit evidence. | Lifecycle tests |
| AUT-SAF-001 | Invalid, expired, unauthorized, cyclic, oversized, or non-JSON input fails closed. | Adversarial tests |
| AUT-SCP-001 | Safety, Enhancement, excluded domains, UI/UX, and deployment remain unchanged. | Frozen-scope tests |
