from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from safety_core.common import reject_duplicate_keys


SAFETY_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = SAFETY_ROOT.parent
FROZEN_SHA256 = {
    "CONSTITUTION.md": "1166d85c3abf5adc9a9c2f8388d10e91aa1c8b18fbfe8c9a9017085c9fd9da67",
    "GOVERNANCE.md": "b7c2018533160b5a31eac973cd9ddaaf13cb2c5e9704e244972d623483d45e2f",
    "ARCHITECTURE.md": "700cb870cfd24e74af790a2cc937dfa40e7d349c461e5381b18239eefb67998a",
    "MASTER_DESIGN.md": "e058c03e28e0c4f8f869fa206950bfd7fd9ca7521e95d6618c7e15dc11fff3d6",
    "RULES.md": "42ddf97125e2a072cd5a1cb5aca914a78110c2a98faf83f071b7113392d38646",
    "POLICIES.md": "8327ca595e3fa74ceb26b5c292d271990f53de60a27397067e5b2e0c3f626187",
    "STANDARDS.md": "8e97a20e77f9972fce5954a7c1a6a51f20418d6dd4ba09485ebc7ea5f3a1959f",
    "RESPONSIBILITY.md": "9f1079dc8996e47056ea64a4b22520e46b6027c992b50358c2d77f3dfda882b4",
    "BOUNDARY.md": "484e8ba7284c67bf751a9160d703bcd51ff409ffe71b16f41fb6b18241224bef",
    "CORE_AXIS.md": "9a357662bae3504863cbbf22d95c5c93be68f02e3a5085bbea2903a222e9db61",
    "REGISTRY.md": "1ffdc1a77d62b06e86fa3bdc8716550efedc5cb0f499e6c41484b65fbc4c350a",
    "REPOSITORY_STRATEGY.md": "04b822792fcef92f67ee5d4c2fa1bd55338da51c2274159f7d3da2e5b235f3fb",
    "WORKSPACE_PROTECTION.md": "0ff3d41d52cbc76d8f8c7d4f754c15b01b285db19f2eac2f3d17d9e681c3e47b",
    "RELEASE_FRAMEWORK.md": "ec93692ebd3ec6c8bafc2a5e73717468c5ba94d10a697950d0b5f3ce41d14c65",
    "VALIDATION_FRAMEWORK.md": "978d86d63d14ea32a883728c0d266a247e416b12005982344896bbac1f55f2d3",
    "COMPLETION_RULE.md": "37fcc1f4ab5d5c6d80d47adbef5dcee44ff128017f60acd78b618325f246cce1",
    "DEVELOPMENT_STANDARD.md": "e44415e8013600f5309b62bddeccbf9cb0d643911498c020dbce5e0b908d9add",
    "EVOLUTION.md": "0ffed5f1a1494824d7f4b356d2199b71b24e788466bb27cf4861ee329ee38079",
    "DECISION_FLOW.md": "6ad183c4da5f1a55713bc6073c83016f1845f1185c6b9a175ec3112c238272dc",
    "GOVERNANCE_LOOP.md": "9e5a1407f23bff6ea2207322de4ec3e859a439c85401751c29038ae2bf9ad42c",
    "TERMINOLOGY.md": "0a6065d6596ea83956c649bba564d6ad96261c70915a1fe9df8b9e41820c923f",
    "Enhancement-Core-Meta-OS/README.md": "173e69c2c42d3a36296c16894d406c804122e03fbda86789d132b50aa2e9b972",
    "Automation-Core-Meta-OS/README.md": "d837e482d90784fa0cd8ad1e76a2f11b62b17978cdd7e6a0e173f8646a8f3581",
    "Collaboration-Connectivity-Core-Meta-OS/README.md": "e51fec7e9bd7e736eff8928e753365613767629f08d4b58cb4696784f8ccd26c",
    "Personal-Secretary-Core-Meta-OS/README.md": "824a19db0b3829a616374202e317f2620a02aa8ca727a5cc3955c43cc6fae924",
}


class ArtifactAndScopeTests(unittest.TestCase):
    def test_foundation_authority_and_other_meta_os_files_are_frozen(self) -> None:
        for relative, expected in FROZEN_SHA256.items():
            with self.subTest(path=relative):
                path = REPOSITORY_ROOT / relative
                self.assertTrue(path.is_file(), relative)
                observed = hashlib.sha256(path.read_bytes()).hexdigest()
                self.assertEqual(observed, expected)

    def test_all_safety_json_is_strictly_parseable(self) -> None:
        for path in sorted(SAFETY_ROOT.rglob("*.json")):
            with self.subTest(path=path.relative_to(SAFETY_ROOT)):
                value = json.loads(
                    path.read_text(encoding="utf-8"),
                    object_pairs_hook=reject_duplicate_keys,
                )
                self.assertIsInstance(value, dict)

    def test_registry_paths_and_contract_references_resolve(self) -> None:
        registry = json.loads(
            (SAFETY_ROOT / "registry" / "safety_core_registry.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(registry["interface"], "safety-core-control-interface")
        self.assertEqual(registry["contract"], "safety-core-control-contract")
        ids = [entity["id"] for entity in registry["entities"]]
        self.assertEqual(len(ids), len(set(ids)))
        for entity in registry["entities"]:
            self.assertTrue((SAFETY_ROOT / entity["path"]).is_file())
        interface = json.loads(
            (SAFETY_ROOT / "interfaces" / "safety_core.interface.json").read_text(
                encoding="utf-8"
            )
        )
        contract = json.loads(
            (SAFETY_ROOT / "contracts" / "safety_core.contract.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(interface["id"], registry["interface"])
        self.assertEqual(contract["id"], registry["contract"])
        self.assertEqual(interface["version"], "0.2.0")
        self.assertEqual(contract["version"], "0.2.0")

    def test_prohibited_product_paths_are_absent(self) -> None:
        forbidden = {
            ".streamlit",
            "components",
            "connectors",
            "pages",
            "streamlit",
            "ui",
            "ux",
        }
        observed = {
            path.name.lower()
            for path in SAFETY_ROOT.rglob("*")
            if path.is_dir()
        }
        self.assertFalse(forbidden & observed)
        self.assertFalse((SAFETY_ROOT / ".git").exists())


if __name__ == "__main__":
    unittest.main()
