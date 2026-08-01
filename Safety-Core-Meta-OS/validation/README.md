# Safety Core Validation

`validate_safety_core.py` is the dependency-free v0.2 structural and contract
validator. It verifies required artifacts, strict JSON parsing, registry paths
and identities, interface/contract/policy version coherence, schema declarations,
Markdown links, Python syntax, prohibited runtime imports, cache absence, and
common secret signatures.

Run from `Safety-Core-Meta-OS/`:

```text
python -B validation/validate_safety_core.py
```

This validator does not authorize a release by itself. Automated behavioral and
adversarial tests must also pass, and root release integration must establish
version, registry, decision, Git, tag, and publication coherence.
