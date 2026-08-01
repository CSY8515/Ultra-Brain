from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from safety_core.audit import AuditLedger
from safety_core.common import (
    ZERO_HASH,
    reject_sensitive_keys,
    require_exact_fields,
)
from safety_core.core import SafetyCore
from safety_core.errors import LedgerError, ValidationError


ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "policies" / "default_policy.json"


class AuditInputBoundaryTests(unittest.TestCase):
    def test_cyclic_huge_and_surrogate_data_fail_as_validation_errors(self) -> None:
        cyclic: dict[str, object] = {}
        cyclic["self"] = cyclic
        cases = (
            ("cyclic", cyclic),
            ("huge-integer", {"value": 10**10000}),
            ("surrogate", {"value": chr(0xD800)}),
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for label, data in cases:
                with self.subTest(label=label):
                    path = root / f"{label}.jsonl"
                    ledger = AuditLedger(path)
                    with self.assertRaises(ValidationError):
                        ledger.append("event-0001", "event", data)
                    self.assertFalse(path.exists())
                    self.assertFalse(
                        path.with_name(f".{path.name}.lock").exists()
                    )

    def test_hostile_huge_and_deep_ledger_json_fail_as_ledger_errors(self) -> None:
        hostile_lines = (
            ("huge", '{"sequence":' + "9" * 10000 + "}\n"),
            ("deep", "[" * 2000 + "0" + "]" * 2000 + "\n"),
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for label, content in hostile_lines:
                with self.subTest(label=label):
                    path = root / f"{label}.jsonl"
                    path.write_text(content, encoding="utf-8")
                    ledger = AuditLedger(path)
                    with self.assertRaises(LedgerError):
                        ledger.verify(expected_count=0, expected_head=ZERO_HASH)

    def test_invalid_ledger_path_fails_as_typed_validation_error(self) -> None:
        with self.assertRaises(ValidationError):
            SafetyCore.open(POLICY, object())  # type: ignore[arg-type]


class CommonValidationBoundaryTests(unittest.TestCase):
    def test_exact_fields_rejects_non_string_keys_without_raw_type_error(self) -> None:
        with self.assertRaises(ValidationError):
            require_exact_fields(
                {"required": True, 1: "invalid"},
                {"required"},
                label="mixed-fields",
            )

    def test_sensitive_key_walk_rejects_cycles_and_excessive_depth(self) -> None:
        cyclic: list[object] = []
        cyclic.append(cyclic)
        with self.assertRaises(ValidationError):
            reject_sensitive_keys(cyclic)

        deep: list[object] = []
        cursor = deep
        for _index in range(34):
            child: list[object] = []
            cursor.append(child)
            cursor = child
        with self.assertRaises(ValidationError):
            reject_sensitive_keys(deep)


class AuditAnchorBoundaryTests(unittest.TestCase):
    def test_reopened_nonempty_ledger_requires_anchor_for_verify_and_query(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.jsonl"
            initial = AuditLedger(path)
            receipt = initial.append("event-0001", "event", {})

            reopened = AuditLedger(path)
            with self.assertRaisesRegex(
                LedgerError, "^ledger:external-anchor-required$"
            ):
                reopened.verify()
            with self.assertRaisesRegex(
                LedgerError, "^ledger:external-anchor-required$"
            ):
                reopened.query()

            self.assertTrue(
                reopened.verify(
                    expected_count=1,
                    expected_head=receipt["record_hash"],
                )
            )
            self.assertEqual(len(reopened.query()), 1)

    def test_zero_anchor_for_missing_ledger_creates_no_ledger_or_lock(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing.jsonl"
            lock_path = path.with_name(f".{path.name}.lock")

            with self.assertRaisesRegex(
                LedgerError, "^ledger:anchored-ledger-missing$"
            ):
                SafetyCore.open(
                    POLICY,
                    path,
                    expected_ledger_count=0,
                    expected_ledger_head=ZERO_HASH,
                )

            self.assertFalse(path.exists())
            self.assertFalse(lock_path.exists())


class AuditFilesystemBoundaryTests(unittest.TestCase):
    def test_hardlinked_ledger_is_rejected_without_modifying_victim(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "audit.jsonl"
            lock_path = root / ".audit.jsonl.lock"
            victim = root / "victim.bin"
            victim.write_bytes(b"")
            ledger = AuditLedger(path)
            try:
                os.link(victim, path)
            except (OSError, NotImplementedError):
                self.skipTest("hardlink creation is not available")

            with self.assertRaisesRegex(LedgerError, "hardlink-forbidden"):
                ledger.append("event-0001", "event", {})

            self.assertEqual(victim.read_bytes(), b"")
            self.assertEqual(path.read_bytes(), b"")
            self.assertFalse(lock_path.exists())

    def test_path_swap_before_append_leaves_replacement_untouched(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "audit.jsonl"
            replacement = root / "replacement.bin"
            marker = b"replacement-must-not-be-modified"
            ledger = AuditLedger(path)
            ledger.append("event-0001", "event", {})
            replacement.write_bytes(marker)

            original_load = ledger._load_verified
            swapped = False

            def load_and_swap(*, require_exists: bool):
                nonlocal swapped
                result = original_load(require_exists=require_exists)
                if not swapped:
                    os.replace(replacement, path)
                    swapped = True
                return result

            with patch.object(ledger, "_load_verified", side_effect=load_and_swap):
                with self.assertRaisesRegex(
                    LedgerError, "file-changed-after-verification"
                ):
                    ledger.append("event-0002", "event", {})

            self.assertEqual(path.read_bytes(), marker)

    def test_post_write_record_loss_is_not_reported_as_success(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.jsonl"
            ledger = AuditLedger(path)
            ledger.append("event-0001", "event", {})
            original_body = path.read_bytes()
            original_load = ledger._load_verified
            calls = 0

            def remove_new_tail(*, require_exists: bool):
                nonlocal calls
                calls += 1
                if calls == 2:
                    path.write_bytes(original_body)
                return original_load(require_exists=require_exists)

            with patch.object(ledger, "_load_verified", side_effect=remove_new_tail):
                with self.assertRaisesRegex(LedgerError, "append-not-durable"):
                    ledger.append("event-0002", "event", {})

            self.assertEqual(path.read_bytes(), original_body)
            self.assertTrue(ledger.verify())

    def test_symlinked_parent_causes_no_external_side_effect(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outside = root / "outside"
            outside.mkdir()
            linked_parent = root / "linked-parent"
            try:
                os.symlink(outside, linked_parent, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("directory symlink creation is not available")

            path = linked_parent / "audit.jsonl"
            ledger = AuditLedger(path)
            with self.assertRaises(LedgerError):
                ledger.append("event-0001", "event", {})

            self.assertFalse((outside / "audit.jsonl").exists())
            self.assertFalse((outside / ".audit.jsonl.lock").exists())


if __name__ == "__main__":
    unittest.main()
