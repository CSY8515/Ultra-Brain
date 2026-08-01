"""Regression tests for preserved Foundation, Safety, and v0.3 Enhancement."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FoundationTests(unittest.TestCase):
    def test_foundation_validator(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "validation" / "validate_foundation.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_all_foundation_json_is_parseable(self) -> None:
        json_paths = sorted((ROOT / "registry").glob("*.json")) + sorted((ROOT / "schemas").glob("*.json"))
        self.assertGreater(len(json_paths), 0)
        for path in json_paths:
            with self.subTest(path=path.relative_to(ROOT)):
                with path.open(encoding="utf-8") as stream:
                    self.assertIsInstance(json.load(stream), dict)

    def test_version_is_v0_3(self) -> None:
        self.assertEqual((ROOT / "VERSION").read_text(encoding="utf-8").strip(), "0.3")

    def test_safety_registry_is_active_at_v0_2(self) -> None:
        registry = json.loads(
            (ROOT / "registry" / "meta_os_registry.json").read_text(encoding="utf-8")
        )
        safety = next(
            entity
            for entity in registry["entities"]
            if entity["id"] == "safety-core-meta-os"
        )
        self.assertEqual(safety["status"], "active")
        self.assertEqual(safety["current_version"], "0.2.0")

    def test_enhancement_registry_is_active_at_v0_3(self) -> None:
        registry = json.loads((ROOT / "registry" / "meta_os_registry.json").read_text(encoding="utf-8"))
        enhancement = next(entity for entity in registry["entities"] if entity["id"] == "enhancement-core-meta-os")
        self.assertEqual(enhancement["status"], "active")
        self.assertEqual(enhancement["current_version"], "0.3.0")

    def test_other_core_meta_os_directories_remain_scope_only(self) -> None:
        for directory_name in (
            "Automation-Core-Meta-OS",
            "Collaboration-Connectivity-Core-Meta-OS",
            "Personal-Secretary-Core-Meta-OS",
        ):
            directory = ROOT / directory_name
            files = sorted(
                path.relative_to(directory).as_posix()
                for path in directory.rglob("*")
                if path.is_file()
            )
            self.assertEqual(files, ["README.md"], directory_name)


if __name__ == "__main__":
    unittest.main()
