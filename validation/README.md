# Validation Evidence

## Purpose

This directory is reserved for revision-addressed validation plans, manifests,
and evidence produced under `VALIDATION_FRAMEWORK.md`. Future evidence must make
the checked requirement, artifact revision, procedure, result, timestamp, and
accountable reviewer unambiguous while excluding secrets and personal data.

Validation evidence is not a substitute for governance approval, and approval
is not a substitute for passing evidence.

## v0.4 application

`validate_foundation.py` remains a dependency-free, standard-library check for
the preserved Foundation and verifies cumulative v0.2 Safety, v0.3 Enhancement,
and v0.4 Automation release integration: version, registries, decisions,
references, local paths, Markdown links, later-Meta-OS boundaries, and delegated
domain validators. Run it from the repository root:

```text
python validation/validate_foundation.py
```

The script is release tooling. It is not a production runtime, background
automation service, monitoring daemon, or later-milestone capability.
