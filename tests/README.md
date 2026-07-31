# Tests

## Purpose

This directory is reserved for governed test specifications and, in later
milestones, their approved implementations. Tests must trace to requirements and
risks, distinguish expected from observed results, and produce reproducible
evidence for the applicable validation gate.

Future suites should separate unit, contract, integration, safety, accessibility,
and release verification concerns when those artifacts enter scope.

## v0.1 boundary

v0.1 includes `test_foundation.py`, a dependency-free standard-library
regression suite for the Foundation validator, JSON parsing, and canonical
version value. Run it from the repository root:

```text
python -m unittest discover -s tests -v
```

No product runtime test, UI test, external dependency, feature fixture, or
v0.2+ capability test is implemented. These executable checks concern only
documents, structure, structured-data validity, repository integrity, and scope
protection.
