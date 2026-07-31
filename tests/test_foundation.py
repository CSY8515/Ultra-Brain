"""Regression tests for the Ultra Brain v0.1 declarative foundation."""

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

    def test_version_is_v0_1(self) -> None:
        self.assertEqual((ROOT / "VERSION").read_text(encoding="utf-8").strip(), "0.1")


if __name__ == "__main__":
    unittest.main()
