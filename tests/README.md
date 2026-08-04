# Tests

## Purpose

This directory is reserved for governed test specifications and, in later
milestones, their approved implementations. Tests must trace to requirements and
risks, distinguish expected from observed results, and produce reproducible
evidence for the applicable validation gate.

Future suites should separate unit, contract, integration, safety, accessibility,
and release verification concerns when those artifacts enter scope.

## v0.7 regression scope

`test_foundation.py` remains a dependency-free standard-library regression
suite for the preserved Foundation and cumulative Core Meta OS state, plus v0.7
OS Ecosystem Registry, Interface, Contract, dependency, operational-flow,
navigation, and independence requirements. Run it from the repository root:

```text
python -m unittest discover -s tests -v
```

Domain runtime and adversarial suites live under the five Core Meta OS
directories. No UI, World, Theme, external network, or deployment test is
introduced by v0.7.
