from __future__ import annotations

import itertools
import tempfile
import unittest
from collections.abc import Mapping
from pathlib import Path
from unittest import mock

import safety_core.incident as incident_module
from safety_core.backup import BackupManager
from safety_core.errors import PolicyError, RecoveryError, StateTransitionError, ValidationError
from safety_core.incident import HISTORY_FIELDS, IncidentManager
from safety_core.models import Incident, Observation
from safety_core.monitoring import Monitor
from safety_core.recovery import RecoveryManager
from safety_core.validation import load_policy


class SingleSnapshotHistoryEntry(Mapping[str, object]):
    def __init__(self, value: Mapping[str, object]) -> None:
        self._value = dict(value)
        self.iteration_count = 0

    def __getitem__(self, key: str) -> object:
        return self._value[key]

    def __iter__(self):
        self.iteration_count += 1
        if self.iteration_count > 1:
            raise RuntimeError("history entry read more than once")
        return iter(self._value)

    def __len__(self) -> int:
        return len(self._value)


def incident_with_history(
    incident: Incident,
    entry: Mapping[str, object],
) -> Incident:
    return Incident(
        id=incident.id,
        severity=incident.severity,
        status=incident.status,
        summary=incident.summary,
        containment_block=incident.containment_block,
        revision=incident.revision,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
        history=(entry,),
    )


class PublicBoundaryTests(unittest.TestCase):
    def test_monitor_revalidates_typed_observation(self) -> None:
        forged = Observation(
            id="observation-0001",
            metric="invalid\nmetric",
            value=1,
            warning_at=5,
            critical_at=10,
            observed_at="2026-08-01T00:00:00Z",
        )
        with self.assertRaises(ValidationError):
            Monitor.evaluate(forged)

    def test_monitor_normalizes_evaluation_timestamp_to_utc(self) -> None:
        observation = Observation(
            id="observation-0001",
            metric="validation-failures",
            value=1,
            warning_at=5,
            critical_at=10,
            observed_at="2026-08-01T09:00:00+09:00",
        )
        signal = Monitor.evaluate(
            observation,
            evaluated_at="2026-08-01T09:00:01+09:00",
        )
        self.assertEqual(signal.evaluated_at, "2026-08-01T00:00:01Z")

    def test_incident_validation_normalizes_malformed_history_to_typed_errors(self) -> None:
        base = IncidentManager.create(
            "incident-0001",
            "low",
            "Caller supplied incident",
            "2026-08-01T00:00:00Z",
        )
        malformed = Incident(
            id=base.id,
            severity=base.severity,
            status=base.status,
            summary=base.summary,
            containment_block=base.containment_block,
            revision=base.revision,
            created_at=base.created_at,
            updated_at=base.updated_at,
            history=(["not-a-transition"],),  # type: ignore[arg-type]
        )
        with self.assertRaises(ValidationError):
            IncidentManager.validate(malformed)
        with self.assertRaises(StateTransitionError):
            IncidentManager.transition(base, ["contained"], 1)  # type: ignore[arg-type]

    def test_incident_validation_snapshots_stateful_history_once(self) -> None:
        base = IncidentManager.create(
            "incident-single-snapshot",
            "low",
            "Caller supplied stateful history",
            "2026-08-01T00:00:00Z",
        )
        entry = SingleSnapshotHistoryEntry(base.history[0])

        validated = IncidentManager.validate(incident_with_history(base, entry))

        self.assertEqual(entry.iteration_count, 1)
        self.assertEqual(dict(validated.history[0]), dict(base.history[0]))

    def test_incident_history_rejects_tuple_subclass_without_iterating_it(self) -> None:
        base = IncidentManager.create(
            "incident-tuple-subclass",
            "low",
            "Caller supplied tuple subclass",
            "2026-08-01T00:00:00Z",
        )
        iteration_count = 0

        class InfiniteTuple(tuple):
            def __len__(self) -> int:
                raise AssertionError("tuple subclass length was inspected")

            def __iter__(self):
                nonlocal iteration_count
                iteration_count += 1
                return itertools.repeat(base.history[0])

        forged = Incident(
            id=base.id,
            severity=base.severity,
            status=base.status,
            summary=base.summary,
            containment_block=base.containment_block,
            revision=base.revision,
            created_at=base.created_at,
            updated_at=base.updated_at,
            history=InfiniteTuple((base.history[0],)),
        )

        with self.assertRaisesRegex(
            ValidationError,
            "incident.history:non-empty-tuple-required",
        ):
            IncidentManager.validate(forged)
        self.assertEqual(iteration_count, 0)

    def test_incident_rejects_equal_to_anything_containment_bypass(self) -> None:
        base = IncidentManager.create(
            "incident-deceptive-status",
            "low",
            "Caller supplied deceptive status",
            "2026-08-01T00:00:00Z",
        )

        class EqualToAnything(str):
            def __eq__(self, other: object) -> bool:
                return True

            def __ne__(self, other: object) -> bool:
                return False

            def __hash__(self) -> int:
                return hash("resolved")

        deceptive_status = EqualToAnything("attacker-controlled")
        self.assertIn(deceptive_status, {"open", "resolved"})
        self.assertNotIn(deceptive_status, {"active"})
        forged = Incident(
            id=base.id,
            severity=base.severity,
            status=deceptive_status,
            summary=base.summary,
            containment_block=False,
            revision=base.revision,
            created_at=base.created_at,
            updated_at=base.updated_at,
            history=(
                {
                    "revision": 1,
                    "from_status": None,
                    "to_status": deceptive_status,
                    "at": base.created_at,
                    "recovery_verified": False,
                },
            ),
        )

        with self.assertRaisesRegex(ValidationError, "incident.status:invalid"):
            IncidentManager.validate(forged)
        with self.assertRaisesRegex(
            StateTransitionError,
            "incident:invalid-target-status",
        ):
            IncidentManager.transition(base, deceptive_status, 1)

    def test_incident_subclass_is_rejected_before_field_access(self) -> None:
        base = IncidentManager.create(
            "incident-stateful-subclass",
            "low",
            "Caller supplied stateful incident",
            "2026-08-01T00:00:00Z",
        )

        class StatefulIncident(Incident):
            def __getattribute__(self, name: str):
                if name in {
                    "id",
                    "severity",
                    "status",
                    "summary",
                    "containment_block",
                    "revision",
                    "created_at",
                    "updated_at",
                    "history",
                }:
                    raise AssertionError("incident subclass field was accessed")
                return super().__getattribute__(name)

        forged = StatefulIncident(
            base.id,
            base.severity,
            base.status,
            base.summary,
            base.containment_block,
            base.revision,
            base.created_at,
            base.updated_at,
            base.history,
        )
        with self.assertRaisesRegex(ValidationError, "incident:incident-required"):
            IncidentManager.validate(forged)

    def test_incident_history_mapping_key_iteration_is_bounded(self) -> None:
        base = IncidentManager.create(
            "incident-bounded-history-entry",
            "low",
            "Caller supplied oversized mapping",
            "2026-08-01T00:00:00Z",
        )
        valid_keys = tuple(base.history[0])

        class LyingOversizedMapping(Mapping[str, object]):
            def __init__(self) -> None:
                self.keys_yielded = 0
                self.length_calls = 0

            def __getitem__(self, key: str) -> object:
                if key in base.history[0]:
                    return base.history[0][key]
                return key

            def __iter__(self):
                keys = (*valid_keys, *(f"extra-{index}" for index in range(60)))
                for key in keys:
                    self.keys_yielded += 1
                    yield key

            def __len__(self) -> int:
                self.length_calls += 1
                return len(HISTORY_FIELDS)

        entry = LyingOversizedMapping()
        with self.assertRaisesRegex(
            ValidationError,
            "incident.history:invalid-entry",
        ):
            IncidentManager.validate(incident_with_history(base, entry))
        self.assertEqual(entry.length_calls, 0)
        self.assertEqual(entry.keys_yielded, len(HISTORY_FIELDS) + 1)

    def test_giant_plain_history_dict_is_rejected_before_copy(self) -> None:
        base = IncidentManager.create(
            "incident-giant-history-entry",
            "low",
            "Caller supplied giant history mapping",
            "2026-08-01T00:00:00Z",
        )
        entry = dict(base.history[0])
        entry.update({f"extra-{index}": index for index in range(100_000)})

        with mock.patch.object(
            incident_module,
            "dict",
            side_effect=AssertionError("history mapping was copied"),
            create=True,
        ) as copy_constructor:
            with self.assertRaisesRegex(
                ValidationError,
                "incident.history:invalid-entry",
            ):
                IncidentManager.validate(incident_with_history(base, entry))
        copy_constructor.assert_not_called()

    def test_incident_validation_normalizes_mapping_protocol_failures(self) -> None:
        base = IncidentManager.create(
            "incident-mapping-failure",
            "low",
            "Caller supplied failing history",
            "2026-08-01T00:00:00Z",
        )

        class IterationFailure(Mapping[str, object]):
            def __getitem__(self, key: str) -> object:
                raise AssertionError("access should not be reached")

            def __iter__(self):
                raise KeyError("iteration failed")

            def __len__(self) -> int:
                return len(base.history[0])

        class AccessFailure(Mapping[str, object]):
            def __getitem__(self, key: str) -> object:
                raise KeyError("access failed")

            def __iter__(self):
                return iter(base.history[0])

            def __len__(self) -> int:
                return len(base.history[0])

        class NextFailure(Mapping[str, object]):
            class FailingIterator:
                def __iter__(self):
                    return self

                def __next__(self):
                    raise RuntimeError("next failed")

            def __getitem__(self, key: str) -> object:
                raise AssertionError("access should not be reached")

            def __iter__(self):
                return self.FailingIterator()

            def __len__(self) -> int:
                return len(base.history[0])

        class BaseExceptionFailure(Mapping[str, object]):
            def __getitem__(self, key: str) -> object:
                raise AssertionError("access should not be reached")

            def __iter__(self):
                raise KeyboardInterrupt("base exception must propagate")

            def __len__(self) -> int:
                return len(base.history[0])

        for entry, cause_type in (
            (IterationFailure(), KeyError),
            (AccessFailure(), KeyError),
            (NextFailure(), RuntimeError),
        ):
            with self.subTest(entry=type(entry).__name__):
                with self.assertRaisesRegex(
                    ValidationError,
                    "incident.history:invalid-entry",
                ) as raised:
                    IncidentManager.validate(incident_with_history(base, entry))
                self.assertIsInstance(raised.exception.__cause__, cause_type)

        with self.assertRaises(KeyboardInterrupt):
            IncidentManager.validate(
                incident_with_history(base, BaseExceptionFailure())
            )

    def test_invalid_filesystem_inputs_fail_before_side_effects(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            (source / "payload.txt").write_text("safe", encoding="utf-8")
            before = sorted(path.name for path in root.iterdir())

            with self.assertRaises(RecoveryError):
                BackupManager.create(source, root / "archive:stream")
            with self.assertRaises(RecoveryError):
                BackupManager.read_verified(None)  # type: ignore[arg-type]
            with self.assertRaises(RecoveryError):
                RecoveryManager.recover(None, root / "restore")  # type: ignore[arg-type]
            with self.assertRaises(PolicyError):
                load_policy(None)  # type: ignore[arg-type]

            self.assertEqual(sorted(path.name for path in root.iterdir()), before)


if __name__ == "__main__":
    unittest.main()
