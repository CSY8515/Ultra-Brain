from __future__ import annotations

import math
import unittest
from datetime import datetime, timezone

from automation_core import (
    AuthorizationError, AutoDecision, AutomationCore, Scheduler, ValidationError,
    validate_workflow,
)


NOW = datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc)


def workflow(kind="manual", **changes):
    value = {
        "id": "daily-pipeline", "version": "0.4.0", "name": "Daily pipeline",
        "steps": [
            {"id": "prepare", "action": "prepare", "needs": [], "parameters": {"factor": 2}, "when": None},
            {"id": "publish", "action": "publish", "needs": ["prepare"], "parameters": {}, "when": None},
        ],
        "trigger": {"kind": kind, "event_type": "work-ready" if kind == "event" else None, "rules": []},
        "retry_limit": 0,
    }
    value.update(changes)
    return value


def grant(**changes):
    value = {
        "id": "grant-001", "approved": True, "safety_decision_id": "safety-decision-001",
        "valid_from": "2026-08-01T00:00:00Z", "expires_at": "2026-08-02T00:00:00Z",
        "allowed_workflows": ["daily-pipeline"], "allowed_actions": ["prepare", "publish", "fail"],
        "max_steps": 10, "max_batch_size": 5, "allow_notifications": True,
    }
    value.update(changes)
    return value


class AutomationCoreTests(unittest.TestCase):
    def core(self, calls=None):
        calls = calls if calls is not None else []
        core = AutomationCore(clock=lambda: NOW)

        def prepare(payload):
            calls.append("prepare")
            return {"value": payload["input"]["value"] * payload["parameters"]["factor"]}

        def undo(payload):
            calls.append(f"undo-{payload['output']['value']}")
            return {"undone": True}

        def publish(payload):
            calls.append("publish")
            return {"published": payload["dependencies"]["prepare"]["value"]}

        core.register_action("prepare", prepare, undo)
        core.register_action("publish", publish)
        return core

    def test_pipeline_executes_in_dependency_order(self):
        calls = []
        result = self.core(calls).execute(workflow(), grant(), {"value": 3}, "run-001", now=NOW)
        self.assertEqual(calls, ["prepare", "publish"])
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.steps[1].output["published"], 6)
        self.assertEqual([item.status for item in result.steps], ["completed", "completed"])

    def test_auto_decision_and_conditional_step(self):
        rule = {"field": "input.run", "operator": "eq", "expected": True}
        self.assertTrue(AutoDecision().evaluate(rule, {"input": {"run": True}}))
        value = workflow()
        value["steps"][1]["when"] = rule
        result = self.core().execute(value, grant(), {"value": 2, "run": False}, "run-002", now=NOW)
        self.assertEqual(result.steps[1].status, "skipped")
        self.assertEqual(result.status, "completed")

    def test_unapproved_expired_and_excess_authority_fail_before_execution(self):
        for bad_grant, message in (
            (grant(approved=False), "not-approved"),
            (grant(expires_at="2026-08-01T11:00:00Z"), "validity"),
            (grant(allowed_actions=["prepare"]), "action-not-allowed"),
            (grant(max_steps=1), "step-budget"),
        ):
            with self.subTest(message=message), self.assertRaisesRegex(AuthorizationError, message):
                self.core().execute(workflow(), bad_grant, {"value": 1}, f"bad-{message}", now=NOW)

    def test_unregistered_action_fails_before_execution(self):
        value = workflow(steps=[{"id": "missing", "action": "fail", "needs": [], "parameters": {}, "when": None}])
        with self.assertRaisesRegex(AuthorizationError, "not-registered"):
            self.core().execute(value, grant(), {"value": 1}, "missing-001", now=NOW)

    def test_bounded_retry_then_success(self):
        attempts = []
        core = AutomationCore(clock=lambda: NOW)

        def flaky(payload):
            attempts.append(1)
            if len(attempts) < 3:
                raise RuntimeError("private detail")
            return {"ok": True}

        core.register_action("prepare", flaky)
        value = workflow(steps=[{"id": "prepare", "action": "prepare", "needs": [], "parameters": {}, "when": None}], retry_limit=2)
        result = core.execute(value, grant(), {"value": 1}, "retry-001", now=NOW)
        self.assertEqual(len(attempts), 3)
        self.assertEqual(result.steps[0].attempts, 3)
        self.assertEqual(result.status, "completed")

    def test_terminal_failure_compensates_in_reverse_and_sanitizes_error(self):
        calls = []
        core = self.core(calls)

        def fail(payload):
            calls.append("fail")
            raise RuntimeError("secret internal failure")

        core.register_action("fail", fail)
        value = workflow(steps=[
            {"id": "prepare", "action": "prepare", "needs": [], "parameters": {"factor": 2}, "when": None},
            {"id": "fail", "action": "fail", "needs": ["prepare"], "parameters": {}, "when": None},
        ])
        result = core.execute(value, grant(), {"value": 4}, "failure-001", now=NOW)
        self.assertEqual(calls, ["prepare", "fail", "undo-8"])
        self.assertEqual(result.status, "compensated")
        self.assertTrue(result.steps[0].compensated)
        self.assertEqual(result.steps[1].error, "RuntimeError:action-failed")
        self.assertNotIn("secret", str(result.to_dict()))

    def test_partial_compensation_is_not_reported_as_compensated(self):
        core = AutomationCore(clock=lambda: NOW)
        core.register_action("publish", lambda payload: {"done": True})
        core.register_action("fail", lambda payload: (_ for _ in ()).throw(RuntimeError("failed")))
        value = workflow(steps=[
            {"id": "publish", "action": "publish", "needs": [], "parameters": {}, "when": None},
            {"id": "fail", "action": "fail", "needs": ["publish"], "parameters": {}, "when": None},
        ])
        result = core.execute(value, grant(), {"value": 1}, "partial-001", now=NOW)
        self.assertEqual(result.status, "failed")
        self.assertFalse(result.steps[0].compensated)

    def test_idempotency_returns_previous_result_and_rejects_conflict(self):
        calls = []
        core = self.core(calls)
        first = core.execute(workflow(), grant(), {"value": 2}, "stable-001", now=NOW)
        second = core.execute(workflow(), grant(), {"value": 2}, "stable-001", now=NOW)
        self.assertIs(first, second)
        self.assertEqual(calls, ["prepare", "publish"])
        with self.assertRaisesRegex(ValidationError, "idempotency-conflict"):
            core.execute(workflow(), grant(), {"value": 3}, "stable-001", now=NOW)

    def test_event_trigger_matches_type_and_rules(self):
        value = workflow("event")
        value["trigger"]["rules"] = [{"field": "payload.priority", "operator": "gte", "expected": 5}]
        event = {"id": "event-001", "event_type": "work-ready", "occurred_at": "2026-08-01T11:00:00Z", "payload": {"priority": 7, "value": 4}}
        result = self.core().handle_event(value, event, grant(), now=NOW)
        self.assertIsNotNone(result)
        event["payload"]["priority"] = 1
        self.assertIsNone(self.core().handle_event(value, event, grant(), now=NOW))

    def test_scheduler_is_caller_driven_and_bounded(self):
        scheduler = Scheduler()
        schedule = {"start_at": "2026-08-01T10:00:00Z", "interval_seconds": 3600, "max_occurrences": 3}
        self.assertFalse(scheduler.is_due(schedule, datetime(2026, 8, 1, 9, tzinfo=timezone.utc)))
        self.assertTrue(scheduler.is_due(schedule, NOW, "2026-08-01T11:00:00Z"))
        self.assertFalse(scheduler.is_due(schedule, NOW, "2026-08-01T12:00:00Z"))
        self.assertFalse(scheduler.is_due(schedule, datetime(2026, 8, 1, 13, tzinfo=timezone.utc)))

    def test_routine_runs_once_per_due_occurrence(self):
        value = workflow("schedule")
        routine = {"id": "routine-001", "workflow": value, "schedule": {"start_at": "2026-08-01T10:00:00Z", "interval_seconds": 3600, "max_occurrences": 10}}
        core = self.core()
        result = core.run_routine(routine, grant(), {"value": 2}, now=NOW, last_run_at="2026-08-01T11:00:00Z")
        self.assertEqual(result.status, "completed")
        self.assertIsNone(core.run_routine(routine, grant(), {"value": 2}, now=NOW, last_run_at="2026-08-01T12:00:00Z"))

    def test_batch_is_bounded_and_independently_traceable(self):
        result = self.core().run_batch(workflow(), grant(), ({"value": 1}, {"value": 2}), "batch-001", now=NOW)
        self.assertEqual(result.status, "completed")
        self.assertEqual(len(result.results), 2)
        self.assertNotEqual(result.results[0].execution_id, result.results[1].execution_id)
        with self.assertRaisesRegex(AuthorizationError, "size"):
            self.core().run_batch(workflow(), grant(max_batch_size=1), ({"value": 1}, {"value": 2}), "batch-002", now=NOW)

    def test_cancellation_blocks_dependents_without_execution(self):
        calls = []
        result = self.core(calls).execute(workflow(), grant(), {"value": 1}, "cancel-001", cancelled_steps=("prepare",), now=NOW)
        self.assertEqual(calls, [])
        self.assertEqual([item.status for item in result.steps], ["cancelled", "blocked"])
        self.assertEqual(result.status, "cancelled")

    def test_notifications_are_local_records_and_can_be_disabled(self):
        result = self.core().execute(workflow(), grant(), {"value": 1}, "notice-001", now=NOW)
        self.assertEqual([item.status for item in result.notifications], ["started", "completed"])
        quiet = self.core().execute(workflow(), grant(allow_notifications=False), {"value": 1}, "notice-002", now=NOW)
        self.assertEqual(quiet.notifications, ())

    def test_cycles_non_finite_values_and_bad_versions_fail_closed(self):
        cycle = workflow(steps=[
            {"id": "one", "action": "prepare", "needs": ["two"], "parameters": {}, "when": None},
            {"id": "two", "action": "publish", "needs": ["one"], "parameters": {}, "when": None},
        ])
        with self.assertRaisesRegex(ValidationError, "cycle"):
            validate_workflow(cycle)
        with self.assertRaisesRegex(ValidationError, "finite"):
            self.core().execute(workflow(), grant(), {"value": math.inf}, "finite-001", now=NOW)
        with self.assertRaisesRegex(ValidationError, "unsupported-version"):
            validate_workflow(workflow(version="0.3.0"))

    def test_cyclic_sensitive_and_custom_mapping_payloads_fail_closed(self):
        cyclic = {}
        cyclic["child"] = cyclic
        with self.assertRaisesRegex(ValidationError, "cycle"):
            self.core().execute(workflow(), grant(), cyclic, "cycle-001", now=NOW)
        with self.assertRaisesRegex(ValidationError, "sensitive-key"):
            self.core().execute(workflow(), grant(), {"password": "hidden"}, "secret-001", now=NOW)

        class CustomMap(dict):
            pass

        with self.assertRaisesRegex(ValidationError, "json-required"):
            self.core().execute(workflow(), grant(), CustomMap(value=1), "custom-001", now=NOW)


if __name__ == "__main__":
    unittest.main()
