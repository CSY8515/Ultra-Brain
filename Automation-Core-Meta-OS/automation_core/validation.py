"""Fail-closed validation for Automation Core public input."""

from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping

from .models import (
    AuthorizationGrant, DecisionRule, RoutineDefinition, ScheduleSpec,
    TriggerEvent, TriggerSpec, WorkflowDefinition, WorkflowStep,
)


CONTRACT_VERSION = "0.4.0"
MAX_STEPS = 64
MAX_BATCH_SIZE = 100
MAX_RETRY_LIMIT = 3
MAX_JSON_BYTES = 262_144
MAX_INTERVAL_SECONDS = 31_536_000
MAX_DEPTH = 32
MAX_NODES = 10_000
IDENTIFIER = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FIELD_PATH = re.compile(r"^[a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)*$")
MAPPING_PROXY_TYPE = type(MappingProxyType({}))
SENSITIVE_KEYS = {
    "apikey", "authorization", "cookie", "credential", "password",
    "privatekey", "secret", "token",
}


class ValidationError(ValueError):
    """Raised before execution when input violates the public contract."""


class AuthorizationError(PermissionError):
    """Raised before execution when delegated authority is absent or invalid."""


def _identifier(value: Any, label: str) -> str:
    if type(value) is not str or len(value) > 128 or not IDENTIFIER.fullmatch(value):
        raise ValidationError(f"{label}:identifier-required")
    return value


def _text(value: Any, label: str, limit: int = 256) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit or "\x00" in value:
        raise ValidationError(f"{label}:text-invalid")
    return value


def _timestamp(value: Any, label: str) -> str:
    value = _text(value, label, 64)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError(f"{label}:timestamp-invalid") from exc
    if parsed.tzinfo is None:
        raise ValidationError(f"{label}:timezone-required")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def thaw_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [thaw_json(item) for item in value]
    return value


def _json_value(
    value: Any,
    label: str = "value",
    *,
    check_size: bool = True,
    _seen: set[int] | None = None,
    _depth: int = 0,
    _nodes: list[int] | None = None,
) -> Any:
    seen = set() if _seen is None else _seen
    nodes = [0] if _nodes is None else _nodes
    nodes[0] += 1
    if nodes[0] > MAX_NODES:
        raise ValidationError(f"{label}:node-limit-exceeded")
    if _depth > MAX_DEPTH:
        raise ValidationError(f"{label}:depth-exceeded")
    if value is None or type(value) in {bool, str, int}:
        clean = value
    elif type(value) is float:
        if not math.isfinite(value):
            raise ValidationError(f"{label}:finite-required")
        clean = value
    elif type(value) in {dict, MAPPING_PROXY_TYPE}:
        identity = id(value)
        if identity in seen:
            raise ValidationError(f"{label}:cycle-detected")
        seen.add(identity)
        clean_map = {}
        for key, item in value.items():
            if type(key) is not str or not key or len(key) > 128:
                raise ValidationError(f"{label}:key-invalid")
            normalized = "".join(character for character in key.casefold() if character.isalnum())
            if normalized in SENSITIVE_KEYS:
                raise ValidationError(f"{label}:sensitive-key-rejected")
            clean_map[key] = _json_value(
                item, f"{label}.{key}", check_size=False,
                _seen=seen, _depth=_depth + 1, _nodes=nodes,
            )
        seen.remove(identity)
        clean = MappingProxyType(clean_map)
    elif type(value) in {list, tuple}:
        if len(value) > 1_000:
            raise ValidationError(f"{label}:array-too-large")
        identity = id(value)
        if identity in seen:
            raise ValidationError(f"{label}:cycle-detected")
        seen.add(identity)
        clean = tuple(
            _json_value(
                item, label, check_size=False,
                _seen=seen, _depth=_depth + 1, _nodes=nodes,
            )
            for item in value
        )
        seen.remove(identity)
    else:
        raise ValidationError(f"{label}:json-required")
    if check_size:
        try:
            encoded = json.dumps(thaw_json(clean), ensure_ascii=False, sort_keys=True).encode("utf-8")
        except (RecursionError, TypeError, ValueError) as exc:
            raise ValidationError(f"{label}:json-invalid") from exc
        if len(encoded) > MAX_JSON_BYTES:
            raise ValidationError(f"{label}:payload-too-large")
    return clean


def validate_output(value: Any) -> Any:
    return _json_value(value, "output")


def validate_payload(value: Any, label: str = "payload") -> Mapping[str, Any]:
    clean = _json_value(value, label)
    if not isinstance(clean, Mapping):
        raise ValidationError(f"{label}:object-required")
    return clean


def validate_rule(value: DecisionRule | Mapping[str, Any]) -> DecisionRule:
    data = value.to_dict() if type(value) is DecisionRule else value
    if not isinstance(data, Mapping) or set(data) != {"field", "operator", "expected"}:
        raise ValidationError("rule:fields-invalid")
    if not isinstance(data["field"], str) or not FIELD_PATH.fullmatch(data["field"]):
        raise ValidationError("rule:field-invalid")
    operator = data["operator"]
    if operator not in {"eq", "ne", "gt", "gte", "lt", "lte", "in", "contains"}:
        raise ValidationError("rule:operator-invalid")
    return DecisionRule(data["field"], operator, _json_value(data["expected"], "rule:expected"))


def validate_step(value: WorkflowStep | Mapping[str, Any]) -> WorkflowStep:
    data = value.to_dict() if type(value) is WorkflowStep else value
    required = {"id", "action", "needs", "parameters", "when"}
    if not isinstance(data, Mapping) or set(data) != required:
        raise ValidationError("step:fields-invalid")
    needs = data["needs"]
    if not isinstance(needs, (list, tuple)) or len(needs) > MAX_STEPS:
        raise ValidationError("step:needs-invalid")
    clean_needs = tuple(_identifier(item, "step:need") for item in needs)
    if len(clean_needs) != len(set(clean_needs)):
        raise ValidationError("step:duplicate-need")
    when = None if data["when"] is None else validate_rule(data["when"])
    return WorkflowStep(
        _identifier(data["id"], "step:id"),
        _identifier(data["action"], "step:action"),
        clean_needs,
        validate_payload(data["parameters"], "step:parameters"),
        when,
    )


def _assert_acyclic(steps: tuple[WorkflowStep, ...]) -> None:
    ids = {step.id for step in steps}
    if any(step.id in step.needs or not set(step.needs) <= ids for step in steps):
        raise ValidationError("workflow:dependency-invalid")
    visiting: set[str] = set()
    visited: set[str] = set()
    lookup = {step.id: step for step in steps}

    def visit(step_id: str) -> None:
        if step_id in visiting:
            raise ValidationError("workflow:dependency-cycle")
        if step_id in visited:
            return
        visiting.add(step_id)
        for dependency in lookup[step_id].needs:
            visit(dependency)
        visiting.remove(step_id)
        visited.add(step_id)

    for step in steps:
        visit(step.id)


def validate_trigger(value: TriggerSpec | Mapping[str, Any]) -> TriggerSpec:
    data = value.to_dict() if type(value) is TriggerSpec else value
    if not isinstance(data, Mapping) or set(data) != {"kind", "event_type", "rules"}:
        raise ValidationError("trigger:fields-invalid")
    if data["kind"] not in {"manual", "event", "schedule"}:
        raise ValidationError("trigger:kind-invalid")
    event_type = data["event_type"]
    if data["kind"] == "event":
        event_type = _identifier(event_type, "trigger:event-type")
    elif event_type is not None:
        raise ValidationError("trigger:event-type-not-allowed")
    rules = data["rules"]
    if not isinstance(rules, (list, tuple)) or len(rules) > 16:
        raise ValidationError("trigger:rules-invalid")
    return TriggerSpec(data["kind"], event_type, tuple(validate_rule(item) for item in rules))


def validate_workflow(value: WorkflowDefinition | Mapping[str, Any]) -> WorkflowDefinition:
    data = value.to_dict() if type(value) is WorkflowDefinition else value
    required = {"id", "version", "name", "steps", "trigger", "retry_limit"}
    if not isinstance(data, Mapping) or set(data) != required:
        raise ValidationError("workflow:fields-invalid")
    if data["version"] != CONTRACT_VERSION:
        raise ValidationError("workflow:unsupported-version")
    raw_steps = data["steps"]
    if not isinstance(raw_steps, (list, tuple)) or not 1 <= len(raw_steps) <= MAX_STEPS:
        raise ValidationError("workflow:step-count-invalid")
    steps = tuple(validate_step(item) for item in raw_steps)
    ids = [item.id for item in steps]
    if len(ids) != len(set(ids)):
        raise ValidationError("workflow:duplicate-step-id")
    _assert_acyclic(steps)
    retry_limit = data["retry_limit"]
    if isinstance(retry_limit, bool) or not isinstance(retry_limit, int) or not 0 <= retry_limit <= MAX_RETRY_LIMIT:
        raise ValidationError("workflow:retry-limit-invalid")
    return WorkflowDefinition(
        _identifier(data["id"], "workflow:id"), CONTRACT_VERSION,
        _text(data["name"], "workflow:name"), steps,
        validate_trigger(data["trigger"]), retry_limit,
    )


def validate_event(value: TriggerEvent | Mapping[str, Any]) -> TriggerEvent:
    data = value.to_dict() if type(value) is TriggerEvent else value
    if not isinstance(data, Mapping) or set(data) != {"id", "event_type", "occurred_at", "payload"}:
        raise ValidationError("event:fields-invalid")
    return TriggerEvent(
        _identifier(data["id"], "event:id"),
        _identifier(data["event_type"], "event:type"),
        _timestamp(data["occurred_at"], "event:occurred-at"),
        validate_payload(data["payload"], "event:payload"),
    )


def validate_schedule(value: ScheduleSpec | Mapping[str, Any]) -> ScheduleSpec:
    data = value.to_dict() if type(value) is ScheduleSpec else value
    if not isinstance(data, Mapping) or set(data) != {"start_at", "interval_seconds", "max_occurrences"}:
        raise ValidationError("schedule:fields-invalid")
    interval = data["interval_seconds"]
    if isinstance(interval, bool) or not isinstance(interval, int) or not 1 <= interval <= MAX_INTERVAL_SECONDS:
        raise ValidationError("schedule:interval-invalid")
    maximum = data["max_occurrences"]
    if maximum is not None and (isinstance(maximum, bool) or not isinstance(maximum, int) or not 1 <= maximum <= 100_000):
        raise ValidationError("schedule:max-occurrences-invalid")
    return ScheduleSpec(_timestamp(data["start_at"], "schedule:start-at"), interval, maximum)


def validate_routine(value: RoutineDefinition | Mapping[str, Any]) -> RoutineDefinition:
    data = value.to_dict() if type(value) is RoutineDefinition else value
    if not isinstance(data, Mapping) or set(data) != {"id", "workflow", "schedule"}:
        raise ValidationError("routine:fields-invalid")
    workflow = validate_workflow(data["workflow"])
    if workflow.trigger.kind != "schedule":
        raise ValidationError("routine:schedule-trigger-required")
    return RoutineDefinition(_identifier(data["id"], "routine:id"), workflow, validate_schedule(data["schedule"]))


def validate_grant(value: AuthorizationGrant | Mapping[str, Any]) -> AuthorizationGrant:
    data = value.to_dict() if type(value) is AuthorizationGrant else value
    required = {
        "id", "approved", "safety_decision_id", "valid_from", "expires_at",
        "allowed_workflows", "allowed_actions", "max_steps", "max_batch_size",
        "allow_notifications",
    }
    if not isinstance(data, Mapping) or set(data) != required:
        raise ValidationError("grant:fields-invalid")
    if type(data["approved"]) is not bool or type(data["allow_notifications"]) is not bool:
        raise ValidationError("grant:boolean-required")
    valid_from = _timestamp(data["valid_from"], "grant:valid-from")
    expires_at = _timestamp(data["expires_at"], "grant:expires-at")
    if parse_timestamp(valid_from) >= parse_timestamp(expires_at):
        raise ValidationError("grant:window-invalid")
    workflows = data["allowed_workflows"]
    actions = data["allowed_actions"]
    if not isinstance(workflows, (list, tuple)) or not workflows or len(workflows) > 64:
        raise ValidationError("grant:workflows-invalid")
    if not isinstance(actions, (list, tuple)) or not actions or len(actions) > 128:
        raise ValidationError("grant:actions-invalid")
    clean_workflows = tuple(_identifier(item, "grant:workflow") for item in workflows)
    clean_actions = tuple(_identifier(item, "grant:action") for item in actions)
    if len(clean_workflows) != len(set(clean_workflows)) or len(clean_actions) != len(set(clean_actions)):
        raise ValidationError("grant:duplicate-authority")
    max_steps = data["max_steps"]
    max_batch = data["max_batch_size"]
    if isinstance(max_steps, bool) or not isinstance(max_steps, int) or not 1 <= max_steps <= MAX_STEPS:
        raise ValidationError("grant:max-steps-invalid")
    if isinstance(max_batch, bool) or not isinstance(max_batch, int) or not 1 <= max_batch <= MAX_BATCH_SIZE:
        raise ValidationError("grant:max-batch-invalid")
    return AuthorizationGrant(
        _identifier(data["id"], "grant:id"), data["approved"],
        _identifier(data["safety_decision_id"], "grant:safety-decision-id"),
        valid_from, expires_at, clean_workflows, clean_actions, max_steps,
        max_batch, data["allow_notifications"],
    )
