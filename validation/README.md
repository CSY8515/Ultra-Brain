# Validation Evidence

## Purpose

This directory is reserved for revision-addressed validation plans, manifests,
and evidence produced under `VALIDATION_FRAMEWORK.md`. Future evidence must make
the checked requirement, artifact revision, procedure, result, timestamp, and
accountable reviewer unambiguous while excluding secrets and personal data.

Validation evidence is not a substitute for governance approval, and approval
is not a substitute for passing evidence.

## v0.1 boundary

v0.1 includes `validate_foundation.py`, a dependency-free, standard-library
check for required artifacts, registry fields and identifiers, JSON schemas,
repository-relative paths, Markdown links, and the scope-only Core Meta OS
boundaries. Run it from the repository root:

```text
python validation/validate_foundation.py
```

The script is release tooling for declarative Foundation artifacts. It is not a
production runtime, automation service, monitoring system, or later-milestone
capability.
