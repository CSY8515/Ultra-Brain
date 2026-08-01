# Tests

## Purpose

This directory is reserved for governed test specifications and, in later
milestones, their approved implementations. Tests must trace to requirements and
risks, distinguish expected from observed results, and produce reproducible
evidence for the applicable validation gate.

Future suites should separate unit, contract, integration, safety, accessibility,
and release verification concerns when those artifacts enter scope.

## v0.5 regression scope

`test_foundation.py` remains a dependency-free standard-library regression
suite for the preserved Foundation, cumulative Safety and Enhancement state,
v0.5 version and registry integration, and the scope-only state of Personal
Secretary Core Meta OS. Run it from the repository root:

```text
python -m unittest discover -s tests -v
```

Domain runtime and adversarial suites live under the Safety, Enhancement,
Automation, and Collaboration & Connectivity Core Meta OS directories. No UI
test, external dependency, Personal Secretary fixture, or deployment test is
included.
