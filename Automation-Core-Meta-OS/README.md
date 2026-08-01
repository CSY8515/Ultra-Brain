# Automation Core Meta OS

## v0.4 Automation baseline

Automation Core Meta OS is Ultra Brain's controlled local workflow runtime. It
turns approved workflow definitions, trigger events, schedules, routines, and
batches into bounded execution with explicit authorization, deterministic
decisions, dependency ordering, idempotency, retries, compensation, audit
events, and local notifications.

The runtime is caller-driven and dependency-free. It does not create a daemon,
poll external systems, open network connections, load code dynamically, or
deliver messages. Automatic execution can invoke only action handlers explicitly
registered by the embedding caller and allowed by the supplied authorization
grant. Safety approval remains external and independently mandatory.

## Components

| Component | Responsibility | Boundary |
| --- | --- | --- |
| Workflow | Validate and run bounded directed acyclic step graphs | No workflow-defined code or dynamic imports |
| Scheduler | Determine whether an interval schedule is due | No clock polling or background process |
| Trigger | Match manual, event, or schedule inputs against explicit rules | No external event collection |
| Routine | Bind a workflow to a governed schedule | Runs only on an explicit caller tick |
| Auto execution | Invoke registered local handlers under a valid grant | No unregistered or unauthorized action |
| Auto decision | Evaluate typed comparison rules | No model inference or policy creation |
| Pipeline | Order steps by declared dependencies | Cycles and missing dependencies fail closed |
| Batch processing | Execute bounded items independently | No queue, worker, or unbounded fan-out |
| Notification | Emit structured local execution notices | No email, chat, webhook, or connector delivery |

## Public API

The `automation_core` package exposes immutable records and `AutomationCore`.
Register allowlisted local handlers with `register_action()`, then use
`execute()`, `handle_event()`, `run_routine()`, or `run_batch()`. See
`contracts/`, `interfaces/`, and `schemas/` for the machine-readable boundary.

## Safety and scope

The v0.2 Safety and v0.3 Enhancement baselines remain unchanged. Every execution
requires a current caller-supplied authorization grant containing a Safety
decision reference, workflow and action allowlists, step and batch budgets, and
an explicit approval flag. The runtime fails closed before invoking handlers
when authorization, validation, schedule, trigger, or budget checks fail.

This implementation contains no external connectivity, collaboration, Personal
Secretary behavior, UI/UX, Streamlit, Core Capability, OS Ecosystem, Living OS,
Universal Learning Engine, or Ultra Brain-exclusive capability.

Run validation and tests from this directory:

```text
python validation/validate_automation_core.py
python -m unittest discover -s tests -v
```
