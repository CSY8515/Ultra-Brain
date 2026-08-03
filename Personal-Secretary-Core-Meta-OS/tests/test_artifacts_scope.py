import ast,json,subprocess,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; REPOSITORY=ROOT.parent
class ArtifactTests(unittest.TestCase):
    def test_json_and_registry(self):
        for path in ROOT.rglob("*.json"): self.assertIsInstance(json.loads(path.read_text(encoding="utf-8")),dict)
        interface=json.loads((ROOT/"interfaces/personal_secretary_core.interface.json").read_text()); contract=json.loads((ROOT/"contracts/personal_secretary_core.contract.json").read_text()); registry=json.loads((ROOT/"registry/personal_secretary_core_registry.json").read_text())
        operational_interface=json.loads((ROOT/"interfaces/operational_reporting.interface.json").read_text()); operational_contract=json.loads((ROOT/"contracts/operational_reporting.contract.json").read_text())
        self.assertEqual((interface["version"],contract["version"],registry["version"]),("0.6.0","0.6.0","0.61.0")); self.assertEqual(registry["interface"],interface["id"]); self.assertEqual(registry["contract"],contract["id"])
        self.assertEqual((operational_interface["version"],operational_contract["version"]),("0.61.0","0.61.0")); self.assertEqual(registry["operational_interface"],operational_interface["id"]); self.assertEqual(registry["operational_contract"],operational_contract["id"])
        for item in registry["entities"]: self.assertTrue((ROOT/item["path"]).is_file())
    def test_no_forbidden_imports_or_paths(self):
        forbidden={"asyncio","http","importlib","requests","socket","subprocess","threading","tkinter","streamlit","urllib"}
        for path in (ROOT/"personal_secretary_core").glob("*.py"):
            tree=ast.parse(path.read_text()); imports=set()
            for node in ast.walk(tree):
                if isinstance(node,ast.Import): imports.update(a.name.split(".")[0] for a in node.names)
                elif isinstance(node,ast.ImportFrom) and node.module: imports.add(node.module.split(".")[0])
            self.assertFalse(imports&forbidden)
        dirs={p.name.lower() for p in ROOT.rglob("*") if p.is_dir()}; self.assertFalse(dirs&{".streamlit","deployment","pages","providers","sdk","streamlit","ui","ux","database","storage","connectors"})
    def test_prior_domains_match_v0_5(self):
        protected=["Safety-Core-Meta-OS","Enhancement-Core-Meta-OS","Automation-Core-Meta-OS","Collaboration-Connectivity-Core-Meta-OS","OS Ecosystem"]
        result=subprocess.run(["git","diff","--exit-code","v0.5","--",*protected],cwd=REPOSITORY,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
if __name__=="__main__": unittest.main()
