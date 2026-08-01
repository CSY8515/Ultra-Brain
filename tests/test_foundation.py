"""Regression tests for Foundation and cumulative v0.2-v0.6 integrations."""

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

    def test_version_is_v0_6(self) -> None:
        self.assertEqual((ROOT / "VERSION").read_text(encoding="utf-8").strip(), "0.6")

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

    def test_automation_registry_is_active_at_v0_4(self) -> None:
        registry = json.loads((ROOT / "registry" / "meta_os_registry.json").read_text(encoding="utf-8"))
        automation = next(entity for entity in registry["entities"] if entity["id"] == "automation-core-meta-os")
        self.assertEqual(automation["status"], "active")
        self.assertEqual(automation["current_version"], "0.4.0")

    def test_connectivity_registry_is_active_at_v0_5(self) -> None:
        registry = json.loads((ROOT / "registry" / "meta_os_registry.json").read_text(encoding="utf-8"))
        connectivity = next(entity for entity in registry["entities"] if entity["id"] == "collaboration-connectivity-core-meta-os")
        self.assertEqual(connectivity["status"], "active")
        self.assertEqual(connectivity["current_version"], "0.5.0")

    def test_personal_secretary_registry_is_active_at_v0_6(self) -> None:
        registry = json.loads((ROOT / "registry" / "meta_os_registry.json").read_text(encoding="utf-8"))
        secretary = next(entity for entity in registry["entities"] if entity["id"] == "personal-secretary-core-meta-os")
        self.assertEqual(secretary["status"], "active")
        self.assertEqual(secretary["current_version"], "0.6.0")


if __name__ == "__main__":
    unittest.main()
