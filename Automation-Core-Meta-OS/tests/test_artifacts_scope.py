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
        registry = json.loads((ROOT / "registry/automation_core_registry.json").read_text(encoding="utf-8"))
        self.assertEqual(registry["version"], "0.4.0")
        ids = [item["id"] for item in registry["entities"]]
        self.assertEqual(len(ids), len(set(ids)))
        for item in registry["entities"]:
            self.assertTrue((ROOT / item["path"]).is_file())
        interface = json.loads((ROOT / "interfaces/automation_core.interface.json").read_text(encoding="utf-8"))
        contract = json.loads((ROOT / "contracts/automation_core.contract.json").read_text(encoding="utf-8"))
        self.assertEqual(interface["id"], registry["interface"])
        self.assertEqual(contract["id"], registry["contract"])
        self.assertTrue(interface["authorization_required"])
        self.assertFalse(interface["background_execution"])
        self.assertFalse(interface["external_delivery"])

    def test_no_forbidden_runtime_imports(self):
        forbidden = {
            "asyncio", "http", "importlib", "requests", "socket", "subprocess",
            "threading", "tkinter", "streamlit",
        }
        for path in (ROOT / "automation_core").glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.add(node.module.split(".")[0])
            self.assertFalse(imports & forbidden, path)

    def test_no_ui_connectivity_or_deployment_paths(self):
        forbidden = {
            ".streamlit", "components", "connectors", "deployment", "pages",
            "streamlit", "ui", "ux", "webhooks",
        }
        observed = {path.name.lower() for path in ROOT.rglob("*") if path.is_dir()}
        self.assertFalse(forbidden & observed)
        self.assertFalse((ROOT / ".git").exists())

    def test_protected_domains_match_v0_3(self):
        protected = [
            "Safety-Core-Meta-OS", "Enhancement-Core-Meta-OS",
            "Collaboration-Connectivity-Core-Meta-OS",
            "Personal-Secretary-Core-Meta-OS", "OS Ecosystem",
        ]
        result = subprocess.run(
            ["git", "diff", "--exit-code", "v0.3", "--", *protected],
            cwd=REPOSITORY, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
