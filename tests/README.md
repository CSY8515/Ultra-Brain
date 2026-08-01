# Tests

## Purpose

This directory is reserved for governed test specifications and, in later
milestones, their approved implementations. Tests must trace to requirements and
risks, distinguish expected from observed results, and produce reproducible
evidence for the applicable validation gate.

Future suites should separate unit, contract, integration, safety, accessibility,
and release verification concerns when those artifacts enter scope.

## v0.2 regression scope

`test_foundation.py` remains a dependency-free standard-library regression
suite for the preserved Foundation, v0.2 version and registry integration, and
the scope-only state of the four later Core Meta OS directories. Run it from
the repository root:

```text
python -m unittest discover -s tests -v
```

Safety runtime and adversarial tests live inside
`Safety-Core-Meta-OS/tests/`. No UI test, external dependency, later Core Meta
OS feature fixture, or deployment test is included.
