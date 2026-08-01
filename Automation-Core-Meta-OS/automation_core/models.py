"""Immutable public records for the Automation Core."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from types import MappingProxyType
from typing import Any, Mapping


def frozen_map(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(value))


class Record:
    def to_dict(self) -> dict[str, Any]:
        def convert(value: Any) -> Any:
            if isinstance(value, Mapping):
                return {key: convert(item) for key, item in value.items()}
            if isinstance(value, tuple):
                return [convert(item) for item in value]
            if is_dataclass(value):
                return {item.name: convert(getattr(value, item.name)) for item in fields(value)}
            return value
        return convert(self)


@dataclass(frozen=True, slots=True)
class DecisionRule(Record):
    field: str
    operator: str
    expected: Any


@dataclass(frozen=True, slots=True)
class WorkflowStep(Record):
    id: str
    action: str
    needs: tuple[str, ...] = ()
    parameters: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))
    when: DecisionRule | None = None


@dataclass(frozen=True, slots=True)
class TriggerSpec(Record):
    kind: str
    event_type: str | None = None
    rules: tuple[DecisionRule, ...] = ()


@dataclass(frozen=True, slots=True)
class WorkflowDefinition(Record):
    id: str
    version: str
    name: str
    steps: tuple[WorkflowStep, ...]
    trigger: TriggerSpec
    retry_limit: int = 0


@dataclass(frozen=True, slots=True)
class TriggerEvent(Record):
    id: str
    event_type: str
    occurred_at: str
    payload: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class ScheduleSpec(Record):
    start_at: str
    interval_seconds: int
    max_occurrences: int | None = None


@dataclass(frozen=True, slots=True)
class RoutineDefinition(Record):
    id: str
    workflow: WorkflowDefinition
    schedule: ScheduleSpec


@dataclass(frozen=True, slots=True)
class AuthorizationGrant(Record):
    id: str
    approved: bool
    safety_decision_id: str
    valid_from: str
    expires_at: str
    allowed_workflows: tuple[str, ...]
    allowed_actions: tuple[str, ...]
    max_steps: int
    max_batch_size: int
    allow_notifications: bool


@dataclass(frozen=True, slots=True)
class ExecutionEvent(Record):
    sequence: int
    state: str
    step_id: str | None
    detail: str


@dataclass(frozen=True, slots=True)
class Notification(Record):
    id: str
    kind: str
    execution_id: str
    status: str
    message: str


@dataclass(frozen=True, slots=True)
class StepResult(Record):
    step_id: str
    status: str
    attempts: int
    output: Any
    error: str | None
    compensated: bool


@dataclass(frozen=True, slots=True)
class ExecutionResult(Record):
    execution_id: str
    workflow_id: str
    authorization_id: str
    idempotency_key: str
    input_digest: str
    status: str
    started_at: str
    finished_at: str
    steps: tuple[StepResult, ...]
    events: tuple[ExecutionEvent, ...]
    notifications: tuple[Notification, ...]


@dataclass(frozen=True, slots=True)
class BatchResult(Record):
    batch_id: str
    workflow_id: str
    status: str
    results: tuple[ExecutionResult, ...]
