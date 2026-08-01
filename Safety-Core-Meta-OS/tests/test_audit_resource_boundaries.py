from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import safety_core.audit as audit_module
from safety_core.audit import AuditLedger
from safety_core.errors import LedgerError, ValidationError


class AuditPayloadNormalizationTests(unittest.TestCase):
    def test_payload_key_separator_and_camel_case_variants_are_rejected(self) -> None:
        variants = (
            "requestPayload",
            "request_payload",
            "request.payload",
            "REQUESTPAYLOAD",
            "request-PayLoad",
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index, key in enumerate(variants):
                with self.subTest(key=key):
                    path = root / f"audit-{index}.jsonl"
                    with self.assertRaisesRegex(
                        ValidationError, "raw-payload-forbidden"
                    ):
                        AuditLedger(path).append(
                            f"event-{index:04d}", "event", {key: "forbidden"}
                        )
                    self.assertFalse(path.exists())
                    self.assertFalse(
                        path.with_name(f".{path.name}.lock").exists()
                    )

    def test_nfkc_payload_compatibility_variants_are_rejected(self) -> None:
        variants = (
            "ｐａｙｌｏａｄ",
            "ＰＡＹＬＯＡＤ",
            "ｒｅｑｕｅｓｔＰａｙｌｏａｄ",
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index, key in enumerate(variants):
                with self.subTest(key=key):
                    path = root / f"nfkc-{index}.jsonl"
                    with self.assertRaisesRegex(
                        ValidationError, "raw-payload-forbidden"
                    ):
                        AuditLedger(path).append(
                            f"event-{index:04d}", "event", {key: "forbidden"}
                        )
                    self.assertFalse(path.exists())
                    self.assertFalse(
                        path.with_name(f".{path.name}.lock").exists()
                    )


class AuditCallerResourceTests(unittest.TestCase):
    def test_top_level_dict_subclass_is_rejected_without_protocol_or_files(self) -> None:
        class BrokenDict(dict):
            def items(self):
                raise KeyError("items must not be called")

        with self.assertRaises(ValidationError):
            audit_module._preflight_audit_data(BrokenDict())

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.jsonl"
            lock_path = path.with_name(f".{path.name}.lock")

            with self.assertRaises(ValidationError):
                AuditLedger(path).append("event-0001", "event", BrokenDict())

            self.assertFalse(path.exists())
            self.assertFalse(lock_path.exists())

    def test_nested_builtin_subclasses_are_rejected_before_user_protocols(self) -> None:
        class BrokenList(list):
            def __iter__(self):
                raise KeyError("iterator must not be called")

        class BrokenString(str):
            def __iter__(self):
                raise KeyError("string iterator must not be called")

        class BrokenInteger(int):
            def bit_length(self):
                raise KeyError("integer protocol must not be called")

        class BrokenFloat(float):
            def __float__(self):
                raise KeyError("float protocol must not be called")

        cases = (
            ("list", {"value": BrokenList()}),
            ("string", {"value": BrokenString("text")}),
            ("integer", {"value": BrokenInteger(1)}),
            ("float", {"value": BrokenFloat(1.0)}),
            ("key", {BrokenString("value"): 1}),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index, (label, data) in enumerate(cases):
                with self.subTest(value_type=label):
                    path = root / f"{label}.jsonl"
                    lock_path = path.with_name(f".{path.name}.lock")

                    with self.assertRaises(ValidationError):
                        AuditLedger(path).append(
                            f"event-{index:04d}", "event", data
                        )

                    self.assertFalse(path.exists())
                    self.assertFalse(lock_path.exists())

    def test_finite_float_array_uses_actual_canonical_size(self) -> None:
        data = {"values": [0.0] * 9_000}
        canonical_size = len(audit_module.canonical_json(data).encode("utf-8"))
        self.assertLess(canonical_size, audit_module.MAX_AUDIT_DATA_BYTES)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.jsonl"
            ledger = AuditLedger(path)
            receipt = ledger.append("event-0001", "event", data)

            self.assertEqual(receipt["sequence"], 1)
            self.assertTrue(ledger.verify())
            self.assertEqual(len(ledger.query()[0]["data"]["values"]), 9_000)

    def test_preflight_rejects_nodes_depth_and_size_before_serialization(self) -> None:
        cases = (
            ("nodes", "MAX_AUDIT_DATA_NODES", 2, {"key": 1}, "node-limit"),
            (
                "depth",
                "MAX_AUDIT_DATA_DEPTH",
                1,
                {"outer": {"inner": 1}},
                "depth-limit",
            ),
            (
                "size",
                "MAX_AUDIT_DATA_BYTES",
                16,
                {"message": "too-large"},
                "size-limit",
            ),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for label, constant, ceiling, data, expected in cases:
                with self.subTest(limit=label):
                    path = root / f"{label}.jsonl"
                    with (
                        patch.object(audit_module, constant, ceiling),
                        patch.object(
                            audit_module,
                            "canonical_json",
                            side_effect=AssertionError("serialization reached"),
                        ),
                    ):
                        with self.assertRaisesRegex(ValidationError, expected):
                            AuditLedger(path).append("event-0001", "event", data)
                    self.assertFalse(path.exists())

    def test_record_limit_is_enforced_before_ledger_creation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.jsonl"
            ledger = AuditLedger(path)
            with patch.object(audit_module, "MAX_AUDIT_RECORD_BYTES", 64):
                with self.assertRaisesRegex(ValidationError, "audit-record:size-limit"):
                    ledger.append("event-0001", "event", {})
            self.assertFalse(path.exists())

    def test_append_count_and_ledger_limits_do_not_modify_existing_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.jsonl"
            ledger = AuditLedger(path)
            ledger.append("event-0001", "event", {})
            original = path.read_bytes()

            with patch.object(audit_module, "MAX_AUDIT_RECORDS", 1):
                with self.assertRaisesRegex(LedgerError, "record-count-limit"):
                    ledger.append("event-0002", "event", {})
            self.assertEqual(path.read_bytes(), original)

            with patch.object(
                audit_module, "MAX_AUDIT_LEDGER_BYTES", len(original) + 1
            ):
                with self.assertRaisesRegex(LedgerError, "size-limit"):
                    ledger.append("event-0003", "event", {})
            self.assertEqual(path.read_bytes(), original)


class AuditLedgerResourceTests(unittest.TestCase):
    def test_read_enforces_ledger_record_and_count_limits(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.jsonl"
            receipt = AuditLedger(path).append("event-0001", "event", {})
            body = path.read_bytes()

            cases = (
                ("ledger", "MAX_AUDIT_LEDGER_BYTES", len(body) - 1, "size-limit"),
                (
                    "record",
                    "MAX_AUDIT_RECORD_BYTES",
                    len(body) - 1,
                    "record-size-limit",
                ),
                ("count", "MAX_AUDIT_RECORDS", 0, "record-count-limit"),
            )
            for label, constant, ceiling, expected in cases:
                with self.subTest(limit=label):
                    with patch.object(audit_module, constant, ceiling):
                        with self.assertRaisesRegex(LedgerError, expected):
                            AuditLedger(path).verify(
                                expected_count=1,
                                expected_head=receipt["record_hash"],
                            )

    def test_read_cleanup_aggregates_stream_and_descriptor_failures(self) -> None:
        class BrokenStream:
            calls = 0

            def close(self) -> None:
                self.calls += 1
                raise OSError("stream-close-failed")

        stream = BrokenStream()
        with patch.object(
            audit_module.os, "close", side_effect=OSError("descriptor-close-failed")
        ) as close:
            cleanup = audit_module._cleanup_read_resources(stream, 123)

        self.assertIsInstance(cleanup, LedgerError)
        self.assertEqual(str(cleanup), "ledger:read-cleanup-failed")
        self.assertEqual(stream.calls, 1)
        close.assert_called_once_with(123)
        with self.assertRaisesRegex(LedgerError, "read-cleanup-failed"):
            audit_module._finish_after_cleanup(None, cleanup)


@unittest.skipUnless(os.name == "posix", "POSIX inode and FIFO behavior required")
class AuditPosixRaceTests(unittest.TestCase):
    def test_lock_path_is_revalidated_after_protected_operation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.jsonl"
            lock_path = path.with_name(f".{path.name}.lock")
            ledger = AuditLedger(path)
            original_load = ledger._load_verified
            calls = 0

            def replace_after_persist(*, require_exists: bool):
                nonlocal calls
                result = original_load(require_exists=require_exists)
                calls += 1
                if calls == 2:
                    lock_path.unlink()
                    lock_path.write_bytes(b"\0")
                return result

            with patch.object(
                ledger, "_load_verified", side_effect=replace_after_persist
            ):
                with self.assertRaisesRegex(
                    LedgerError, "lock-(?:replaced|hardlink-forbidden)"
                ):
                    ledger.append("event-0001", "event", {})
            self.assertEqual(calls, 2)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO creation unavailable")
    def test_fifo_swap_during_read_fails_without_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.jsonl"
            AuditLedger(path).append("event-0001", "event", {})
            ledger = AuditLedger(path)
            original_open = os.open
            swapped = False

            def swap_then_open(target, flags, *args):
                nonlocal swapped
                if not swapped and os.path.abspath(os.fspath(target)) == str(path):
                    path.unlink()
                    os.mkfifo(path)
                    swapped = True
                return original_open(target, flags, *args)

            with patch.object(audit_module.os, "open", side_effect=swap_then_open):
                with self.assertRaises(LedgerError):
                    ledger._load_verified(require_exists=True)
            self.assertTrue(swapped)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO creation unavailable")
    def test_fifo_swap_during_lock_open_fails_without_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.jsonl"
            AuditLedger(path).append("event-0001", "event", {})
            lock_path = path.with_name(f".{path.name}.lock")
            original_open = os.open
            swapped = False

            def swap_then_open(target, flags, *args):
                nonlocal swapped
                if not swapped and os.path.abspath(os.fspath(target)) == str(lock_path):
                    lock_path.unlink()
                    os.mkfifo(lock_path)
                    swapped = True
                return original_open(target, flags, *args)

            with patch.object(audit_module.os, "open", side_effect=swap_then_open):
                with self.assertRaisesRegex(LedgerError, "lock-not-regular"):
                    with audit_module._process_lock(path):
                        pass
            self.assertTrue(swapped)

    def test_all_posix_audit_opens_include_nonblocking_flag(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.jsonl"
            lock_path = path.with_name(f".{path.name}.lock")
            original_open = os.open
            observed: list[tuple[str, int]] = []

            def record_open(target, flags, *args):
                observed.append((os.path.abspath(os.fspath(target)), flags))
                return original_open(target, flags, *args)

            with patch.object(audit_module.os, "open", side_effect=record_open):
                AuditLedger(path).append("event-0001", "event", {})

            relevant = [
                flags
                for target, flags in observed
                if target in {str(path), str(lock_path)}
            ]
            self.assertGreaterEqual(len(relevant), 3)
            self.assertTrue(all(flags & os.O_NONBLOCK for flags in relevant))


if __name__ == "__main__":
    unittest.main()
