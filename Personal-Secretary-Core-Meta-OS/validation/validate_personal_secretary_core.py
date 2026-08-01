"""Validate the isolated v0.6 Personal Secretary Core."""
import ast,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; REPOSITORY=ROOT.parent; VERSION="0.6.0"
REQUIRED=("README.md","REQUIREMENTS.md","ARCHITECTURE_REVIEW.md","MASTER_DESIGN.md","CHANGELOG.md","VERSION","personal_secretary_core/__init__.py","personal_secretary_core/__main__.py","personal_secretary_core/models.py","personal_secretary_core/validation.py","personal_secretary_core/core.py","interfaces/personal_secretary_core.interface.json","contracts/personal_secretary_core.contract.json","registry/personal_secretary_core_registry.json","schemas/secretary_grant.schema.json","schemas/task.schema.json","schemas/briefing.schema.json","schemas/decision_analysis.schema.json","schemas/schedule_plan.schema.json","tests/test_personal_secretary_core.py","tests/test_artifacts_scope.py")
FORBIDDEN={"asyncio","http","importlib","requests","socket","subprocess","threading","tkinter","streamlit","urllib"}
def load(path):
    def unique(pairs):
        value={}
        for key,item in pairs:
            if key in value: raise ValueError(f"duplicate key {key}")
            value[key]=item
        return value
    return json.loads(path.read_text(encoding="utf-8"),object_pairs_hook=unique)
def main():
    errors=[]
    for relative in REQUIRED:
        path=ROOT/relative
        if not path.is_file() or not path.read_text(encoding="utf-8").strip(): errors.append(f"missing or empty artifact: {relative}")
    if (ROOT/"VERSION").read_text().strip()!="0.6": errors.append("VERSION must be 0.6")
    values={}
    for path in ROOT.rglob("*.json"):
        try: values[path.relative_to(ROOT).as_posix()]=load(path)
        except (json.JSONDecodeError,ValueError) as exc: errors.append(f"{path.relative_to(ROOT)}: {exc}")
    interface=values.get("interfaces/personal_secretary_core.interface.json",{}); contract=values.get("contracts/personal_secretary_core.contract.json",{}); registry=values.get("registry/personal_secretary_core_registry.json",{})
    if interface.get("version")!=VERSION or contract.get("version")!=VERSION or registry.get("version")!=VERSION: errors.append("registry/interface/contract version mismatch")
    if registry.get("interface")!=interface.get("id") or registry.get("contract")!=contract.get("id"): errors.append("registry references do not resolve")
    for item in registry.get("entities",[]):
        if not (ROOT/item.get("path","")).is_file(): errors.append(f"registry path missing: {item.get('path')}")
    for relative,value in values.items():
        if relative.startswith("schemas/") and (value.get("$schema")!="https://json-schema.org/draft/2020-12/schema" or value.get("type")!="object"): errors.append(f"{relative}: invalid schema declaration")
    for path in (ROOT/"personal_secretary_core").glob("*.py"):
        try: tree=ast.parse(path.read_text())
        except SyntaxError as exc: errors.append(str(exc)); continue
        imports=set()
        for node in ast.walk(tree):
            if isinstance(node,ast.Import): imports.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node,ast.ImportFrom) and node.module: imports.add(node.module.split(".")[0])
        if imports&FORBIDDEN: errors.append(f"{path.name}: forbidden imports")
    protected=["Safety-Core-Meta-OS","Enhancement-Core-Meta-OS","Automation-Core-Meta-OS","Collaboration-Connectivity-Core-Meta-OS","OS Ecosystem"]
    if subprocess.run(["git","diff","--exit-code","v0.5","--",*protected],cwd=REPOSITORY,capture_output=True).returncode: errors.append("prior domains differ from v0.5")
    tests=subprocess.run([sys.executable,"-B","-m","unittest","discover","-s","tests"],cwd=ROOT,capture_output=True,text=True)
    if tests.returncode: errors.append(f"automatic tests failed: {(tests.stdout+tests.stderr).strip()}")
    if errors:
        print("Personal Secretary Core Meta OS v0.6 validation: FAILED")
        for error in errors: print(f"- {error}")
        return 1
    print("Personal Secretary Core Meta OS v0.6 validation: PASSED"); print(f"- Required artifacts: {len(REQUIRED)}"); print(f"- JSON artifacts: {len(values)}"); print("- Registered assistance boundary: coherent at 0.6.0"); print("- Prior Core domains and OS Ecosystem: unchanged from v0.5"); return 0
if __name__=="__main__": sys.exit(main())
