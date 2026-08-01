from __future__ import annotations

import ast
import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = ROOT.parent


class ArtifactScopeTests(unittest.TestCase):
    def test_all_local_json_is_parseable(self):
        for path in ROOT.rglob("*.json"):
            with self.subTest(path=path):
                self.assertIsInstance(json.loads(path.read_text(encoding="utf-8")), dict)

    def test_registry_references_resolve(self):
        registry = json.loads((ROOT / "registry/enhancement_core_registry.json").read_text(encoding="utf-8"))
        self.assertEqual(registry["version"], "0.3.0")
        ids = [item["id"] for item in registry["entities"]]
        self.assertEqual(len(ids), len(set(ids)))
        for item in registry["entities"]:
            self.assertTrue((ROOT / item["path"]).is_file())
        interface = json.loads((ROOT / "interfaces/enhancement_core.interface.json").read_text(encoding="utf-8"))
        contract = json.loads((ROOT / "contracts/enhancement_core.contract.json").read_text(encoding="utf-8"))
        self.assertEqual(interface["id"], registry["interface"])
        self.assertEqual(contract["id"], registry["contract"])
        self.assertFalse(interface["execution_authority"])

    def test_no_forbidden_runtime_imports(self):
        forbidden = {"asyncio", "http", "requests", "socket", "subprocess", "threading", "streamlit", "tkinter"}
        for path in (ROOT / "enhancement_core").glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.add(node.module.split(".")[0])
            self.assertFalse(imports & forbidden, path)

    def test_prohibited_product_paths_are_absent(self):
        forbidden = {".streamlit", "automation", "connectors", "pages", "streamlit", "ui", "ux"}
        observed = {path.name.lower() for path in ROOT.rglob("*") if path.is_dir()}
        self.assertFalse(forbidden & observed)
        self.assertFalse((ROOT / ".git").exists())

    def test_safety_and_excluded_domains_match_v0_2(self):
        protected = [
            "Safety-Core-Meta-OS", "Automation-Core-Meta-OS",
            "Collaboration-Connectivity-Core-Meta-OS",
            "Personal-Secretary-Core-Meta-OS", "OS Ecosystem",
        ]
        result = subprocess.run(
            ["git", "diff", "--exit-code", "v0.2", "--", *protected],
            cwd=REPOSITORY, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
