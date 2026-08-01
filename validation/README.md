# Validation Evidence

## Purpose

This directory is reserved for revision-addressed validation plans, manifests,
and evidence produced under `VALIDATION_FRAMEWORK.md`. Future evidence must make
the checked requirement, artifact revision, procedure, result, timestamp, and
accountable reviewer unambiguous while excluding secrets and personal data.

Validation evidence is not a substitute for governance approval, and approval
is not a substitute for passing evidence.

## v0.2 application

`validate_foundation.py` remains a dependency-free, standard-library check for
the preserved Foundation and now verifies the minimum v0.2 Safety release
integration: version, registries, decisions, references, local paths, Markdown
links, later-Meta-OS boundaries, and the delegated Safety validator. Run it from
the repository root:

```text
python validation/validate_foundation.py
```

The script is release tooling. It is not a production runtime, automation
service, monitoring daemon, or later-milestone capability.
