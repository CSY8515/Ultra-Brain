from __future__ import annotations
import json
import subprocess
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; REPOSITORY=ROOT.parent
class OperationalArchitectureTests(unittest.TestCase):
    def test_operational_port_contract_and_schemas_are_coherent(self):
        interface=json.loads((ROOT/"interfaces/operational_reporting.interface.json").read_text(encoding="utf-8"))
        contract=json.loads((ROOT/"contracts/operational_reporting.contract.json").read_text(encoding="utf-8"))
        report=json.loads((ROOT/"schemas/operational_report.schema.json").read_text(encoding="utf-8"))
        brief=json.loads((ROOT/"schemas/operational_brief.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(interface["version"],"0.61.0"); self.assertEqual(contract["version"],"0.61.0")
        self.assertEqual(contract["interface"],interface["id"]); self.assertFalse(interface["runtime_change"]); self.assertFalse(contract["runtime_change"])
        domains=set(interface["status_domains"])
        self.assertEqual(domains,set(report["properties"]["status_domain"]["enum"]))
        self.assertEqual(domains,set(brief["properties"]["status_domains"]["items"]["enum"]))
    def test_failure_and_approval_lifecycle_is_complete(self):
        report=json.loads((ROOT/"schemas/operational_report.schema.json").read_text(encoding="utf-8"))
        brief=json.loads((ROOT/"schemas/operational_brief.schema.json").read_text(encoding="utf-8"))
        categories=set(report["properties"]["findings"]["items"]["properties"]["category"]["enum"])
        self.assertTrue({"error","failure","incident","warning","recovery","rollback"}<=categories)
        approval=set(brief["properties"]["approval_requests"]["items"]["properties"]["state"]["enum"])
        outcomes=set(brief["properties"]["outcomes"]["items"]["properties"]["state"]["enum"])
        self.assertEqual(approval,{"requested","approved","rejected","deferred"})
        self.assertTrue({"completed","failed","recovered","rolled_back"}<=outcomes)
    def test_v06_python_runtime_is_unchanged(self):
        result=subprocess.run(["git","diff","--exit-code","v0.6","--","Personal-Secretary-Core-Meta-OS/personal_secretary_core"],cwd=REPOSITORY,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
if __name__=="__main__": unittest.main()
