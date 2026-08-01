"""Governed, caller-driven Automation Core runtime."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from types import MappingProxyType
from typing import Any, Callable, Mapping

from .models import (
    AuthorizationGrant, BatchResult, DecisionRule, ExecutionEvent,
    ExecutionResult, Notification, RoutineDefinition, ScheduleSpec, StepResult,
    TriggerEvent, TriggerSpec, WorkflowDefinition, WorkflowStep,
)
from .validation import (
    AuthorizationError, IDENTIFIER, ValidationError, parse_timestamp, thaw_json,
    validate_event, validate_grant, validate_output, validate_payload,
    validate_routine, validate_rule, validate_schedule, validate_workflow,
)


ActionHandler = Callable[[Mapping[str, Any]], Any]
Clock = Callable[[], datetime]


def _utc_text(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValidationError("time:timezone-required")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _digest(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class AutoDecision:
    """Evaluate explicit comparison rules without inference or side effects."""

    def evaluate(self, rule: DecisionRule | Mapping[str, Any], context: Mapping[str, Any]) -> bool:
        clean_rule = validate_rule(rule)
        current: Any = context
        for part in clean_rule.field.split("."):
            if not isinstance(current, Mapping) or part not in current:
                return False
            current = current[part]
        expected = clean_rule.expected
        try:
            if clean_rule.operator == "eq":
                return current == expected
            if clean_rule.operator == "ne":
                return current != expected
            if clean_rule.operator == "gt":
                return current > expected
            if clean_rule.operator == "gte":
                return current >= expected
            if clean_rule.operator == "lt":
                return current < expected
            if clean_rule.operator == "lte":
                return current <= expected
            if clean_rule.operator == "in":
                return current in expected
            if clean_rule.operator == "contains":
                return expected in current
        except (TypeError, ValueError) as exc:
            raise ValidationError("decision:incompatible-values") from exc
        raise ValidationError("decision:operator-invalid")


class TriggerEngine:
    def __init__(self, decision: AutoDecision | None = None) -> None:
        self.decision = decision or AutoDecision()

    def matches(self, trigger: TriggerSpec, event: TriggerEvent) -> bool:
        if trigger.kind != "event" or trigger.event_type != event.event_type:
            return False
        context = MappingProxyType({"event_type": event.event_type, "payload": event.payload})
        return all(self.decision.evaluate(rule, context) for rule in trigger.rules)


class Scheduler:
    """Pure schedule calculation; it never waits, polls, or starts work."""

    def occurrence(self, schedule: ScheduleSpec | Mapping[str, Any], now: datetime) -> int | None:
        clean = validate_schedule(schedule)
        now_value = now.astimezone(timezone.utc) if now.tzinfo else None
        if now_value is None:
            raise ValidationError("schedule:now-timezone-required")
        start = parse_timestamp(clean.start_at)
        if now_value < start:
            return None
        index = int((now_value - start).total_seconds() // clean.interval_seconds) + 1
        if clean.max_occurrences is not None and index > clean.max_occurrences:
            return None
        return index

    def is_due(
        self,
        schedule: ScheduleSpec | Mapping[str, Any],
        now: datetime,
        last_run_at: str | None = None,
    ) -> bool:
        clean = validate_schedule(schedule)
        index = self.occurrence(clean, now)
        if index is None:
            return False
        if last_run_at is None:
            return True
        last = parse_timestamp(last_run_at)
        start = parse_timestamp(clean.start_at)
        due_at = start + timedelta(seconds=(index - 1) * clean.interval_seconds)
        return last < due_at


class AutomationCore:
    """Facade for workflows, triggers, routines, batches, and local notices."""

    def __init__(self, clock: Clock | None = None) -> None:
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._actions: dict[str, tuple[ActionHandler, ActionHandler | None]] = {}
        self._ledger: dict[tuple[str, str], tuple[str, ExecutionResult]] = {}
        self.decision = AutoDecision()
        self.triggers = TriggerEngine(self.decision)
        self.scheduler = Scheduler()

    def register_action(
        self,
        name: str,
        handler: ActionHandler,
        compensation: ActionHandler | None = None,
    ) -> None:
        if not isinstance(name, str) or not IDENTIFIER.fullmatch(name):
            raise ValidationError("action:name-invalid")
        if not callable(handler) or (compensation is not None and not callable(compensation)):
            raise ValidationError("action:callable-required")
        if name in self._actions:
            raise ValidationError("action:already-registered")
        self._actions[name] = (handler, compensation)

    def _authorize(self, workflow: WorkflowDefinition, grant: AuthorizationGrant, now: datetime) -> None:
        if not grant.approved:
            raise AuthorizationError("authorization:not-approved")
        current = now.astimezone(timezone.utc) if now.tzinfo else None
        if current is None:
            raise ValidationError("authorization:now-timezone-required")
        if not parse_timestamp(grant.valid_from) <= current < parse_timestamp(grant.expires_at):
            raise AuthorizationError("authorization:outside-validity-window")
        if workflow.id not in grant.allowed_workflows:
            raise AuthorizationError("authorization:workflow-not-allowed")
        if len(workflow.steps) > grant.max_steps:
            raise AuthorizationError("authorization:step-budget-exceeded")
        workflow_actions = {step.action for step in workflow.steps}
        if not workflow_actions <= set(grant.allowed_actions):
            raise AuthorizationError("authorization:action-not-allowed")
        if not workflow_actions <= self._actions.keys():
            raise AuthorizationError("authorization:action-not-registered")

    @staticmethod
    def _ordered_steps(workflow: WorkflowDefinition) -> tuple[WorkflowStep, ...]:
        remaining = {step.id: step for step in workflow.steps}
        resolved: list[WorkflowStep] = []
        completed: set[str] = set()
        while remaining:
            ready = sorted(
                (step for step in remaining.values() if set(step.needs) <= completed),
                key=lambda step: step.id,
            )
            if not ready:
                raise ValidationError("workflow:dependency-cycle")
            for step in ready:
                resolved.append(step)
                completed.add(step.id)
                del remaining[step.id]
        return tuple(resolved)

    def execute(
        self,
        workflow: WorkflowDefinition | Mapping[str, Any],
        grant: AuthorizationGrant | Mapping[str, Any],
        input_data: Mapping[str, Any],
        idempotency_key: str,
        *,
        cancelled_steps: tuple[str, ...] = (),
        now: datetime | None = None,
    ) -> ExecutionResult:
        clean_workflow = validate_workflow(workflow)
        clean_grant = validate_grant(grant)
        clean_input = validate_payload(input_data, "execution:input")
        if not isinstance(idempotency_key, str) or not IDENTIFIER.fullmatch(idempotency_key):
            raise ValidationError("execution:idempotency-key-invalid")
        if not isinstance(cancelled_steps, tuple) or len(cancelled_steps) != len(set(cancelled_steps)):
            raise ValidationError("execution:cancelled-steps-invalid")
        known_steps = {step.id for step in clean_workflow.steps}
        if any(not isinstance(item, str) or item not in known_steps for item in cancelled_steps):
            raise ValidationError("execution:cancelled-step-unknown")
        current = now or self._clock()
        self._authorize(clean_workflow, clean_grant, current)

        plain_input = thaw_json(clean_input)
        input_digest = _digest({
            "workflow": clean_workflow.to_dict(),
            "authorization_id": clean_grant.id,
            "input": plain_input,
            "cancelled_steps": cancelled_steps,
        })
        ledger_key = (clean_workflow.id, idempotency_key)
        if ledger_key in self._ledger:
            previous_digest, previous_result = self._ledger[ledger_key]
            if previous_digest != input_digest:
                raise ValidationError("execution:idempotency-conflict")
            return previous_result

        execution_id = f"execution-{_digest([clean_workflow.id, idempotency_key])[:16]}"
        started_at = _utc_text(current)
        events: list[ExecutionEvent] = [ExecutionEvent(1, "started", None, "workflow-started")]
        notices: list[Notification] = []
        if clean_grant.allow_notifications:
            notices.append(Notification(f"{execution_id}-started", "lifecycle", execution_id, "started", "Workflow execution started."))

        ordered = self._ordered_steps(clean_workflow)
        results: dict[str, StepResult] = {}
        outputs: dict[str, Any] = {}
        successful: list[WorkflowStep] = []
        terminal_failure = False

        for step in ordered:
            if terminal_failure or any(results[need].status != "completed" for need in step.needs):
                results[step.id] = StepResult(step.id, "blocked", 0, None, None, False)
                events.append(ExecutionEvent(len(events) + 1, "blocked", step.id, "dependency-not-completed"))
                continue
            if step.id in cancelled_steps:
                results[step.id] = StepResult(step.id, "cancelled", 0, None, None, False)
                events.append(ExecutionEvent(len(events) + 1, "cancelled", step.id, "caller-cancelled"))
                continue
            context = MappingProxyType({"input": clean_input, "outputs": MappingProxyType(outputs)})
            if step.when is not None and not self.decision.evaluate(step.when, context):
                results[step.id] = StepResult(step.id, "skipped", 0, None, None, False)
                events.append(ExecutionEvent(len(events) + 1, "skipped", step.id, "condition-false"))
                continue

            handler, _ = self._actions[step.action]
            payload = MappingProxyType({
                "input": clean_input,
                "parameters": step.parameters,
                "dependencies": MappingProxyType({need: outputs[need] for need in step.needs}),
            })
            output: Any = None
            error: str | None = None
            attempts = 0
            for attempts in range(1, clean_workflow.retry_limit + 2):
                events.append(ExecutionEvent(len(events) + 1, "attempted", step.id, f"attempt-{attempts}"))
                try:
                    output = validate_output(handler(payload))
                    error = None
                    break
                except Exception as exc:
                    error = f"{type(exc).__name__}:action-failed"
            if error is None:
                outputs[step.id] = output
                successful.append(step)
                results[step.id] = StepResult(step.id, "completed", attempts, output, None, False)
                events.append(ExecutionEvent(len(events) + 1, "completed", step.id, "action-completed"))
            else:
                results[step.id] = StepResult(step.id, "failed", attempts, None, error, False)
                events.append(ExecutionEvent(len(events) + 1, "failed", step.id, "action-failed"))
                terminal_failure = True

        compensation_complete = bool(successful)
        if terminal_failure:
            for step in reversed(successful):
                _, compensation = self._actions[step.action]
                if compensation is None:
                    compensation_complete = False
                    continue
                payload = MappingProxyType({
                    "input": clean_input,
                    "parameters": step.parameters,
                    "output": outputs[step.id],
                })
                try:
                    validate_output(compensation(payload))
                    results[step.id] = replace(results[step.id], compensated=True)
                    events.append(ExecutionEvent(len(events) + 1, "compensated", step.id, "compensation-completed"))
                except Exception:
                    compensation_complete = False
                    events.append(ExecutionEvent(len(events) + 1, "compensation-failed", step.id, "compensation-failed"))

        statuses = {result.status for result in results.values()}
        if terminal_failure:
            status = "compensated" if compensation_complete else "failed"
        elif "cancelled" in statuses:
            status = "cancelled"
        else:
            status = "completed"
        finished_at = _utc_text(self._clock() if now is None else current)
        events.append(ExecutionEvent(len(events) + 1, status, None, f"workflow-{status}"))
        if clean_grant.allow_notifications:
            notices.append(Notification(f"{execution_id}-{status}", "lifecycle", execution_id, status, f"Workflow execution {status}."))
        result = ExecutionResult(
            execution_id, clean_workflow.id, clean_grant.id, idempotency_key,
            input_digest, status, started_at, finished_at,
            tuple(results[step.id] for step in ordered), tuple(events), tuple(notices),
        )
        self._ledger[ledger_key] = (input_digest, result)
        return result

    def handle_event(
        self,
        workflow: WorkflowDefinition | Mapping[str, Any],
        event: TriggerEvent | Mapping[str, Any],
        grant: AuthorizationGrant | Mapping[str, Any],
        *,
        now: datetime | None = None,
    ) -> ExecutionResult | None:
        clean_workflow = validate_workflow(workflow)
        clean_event = validate_event(event)
        if not self.triggers.matches(clean_workflow.trigger, clean_event):
            return None
        return self.execute(
            clean_workflow, grant, {"event": clean_event.to_dict()},
            f"event-{clean_event.id}", now=now,
        )

    def run_routine(
        self,
        routine: RoutineDefinition | Mapping[str, Any],
        grant: AuthorizationGrant | Mapping[str, Any],
        input_data: Mapping[str, Any],
        *,
        now: datetime,
        last_run_at: str | None = None,
    ) -> ExecutionResult | None:
        clean_routine = validate_routine(routine)
        occurrence = self.scheduler.occurrence(clean_routine.schedule, now)
        if occurrence is None or not self.scheduler.is_due(clean_routine.schedule, now, last_run_at):
            return None
        return self.execute(
            clean_routine.workflow, grant, input_data,
            f"routine-{clean_routine.id}-{occurrence}", now=now,
        )

    def run_batch(
        self,
        workflow: WorkflowDefinition | Mapping[str, Any],
        grant: AuthorizationGrant | Mapping[str, Any],
        items: tuple[Mapping[str, Any], ...],
        batch_id: str,
        *,
        now: datetime | None = None,
    ) -> BatchResult:
        clean_workflow = validate_workflow(workflow)
        clean_grant = validate_grant(grant)
        if not isinstance(batch_id, str) or not IDENTIFIER.fullmatch(batch_id):
            raise ValidationError("batch:id-invalid")
        if not isinstance(items, tuple) or not 1 <= len(items) <= clean_grant.max_batch_size:
            raise AuthorizationError("batch:size-not-authorized")
        clean_items = tuple(validate_payload(item, "batch:item") for item in items)
        results = tuple(
            self.execute(clean_workflow, clean_grant, item, f"batch-{batch_id}-{index}", now=now)
            for index, item in enumerate(clean_items, 1)
        )
        statuses = {item.status for item in results}
        status = "completed" if statuses == {"completed"} else "failed" if statuses <= {"failed", "compensated"} else "partial"
        return BatchResult(batch_id, clean_workflow.id, status, results)
