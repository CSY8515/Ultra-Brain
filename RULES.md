# Ultra Brain Rules

## Purpose

This document states the mandatory rules for work governed by Ultra Brain. The v0.1 release establishes these rules as documentation; it does not implement a runtime, a user interface, or any v0.2+ capability.

## Authority and precedence

When two instructions conflict, apply the first applicable authority in this order:

1. an explicit, current decision of the User;
2. [CONSTITUTION.md](CONSTITUTION.md);
3. [GOVERNANCE.md](GOVERNANCE.md);
4. this document;
5. [POLICIES.md](POLICIES.md);
6. [STANDARDS.md](STANDARDS.md);
7. approved architecture, interfaces, and contracts;
8. plans, guidance, and implementation details.

A lower authority MUST NOT silently reinterpret a higher authority. An unresolved conflict MUST stop the affected work and be submitted to the User through the decision process in [DECISION_LOG.md](DECISION_LOG.md).

## Mandatory rules

### R-01 — Declare scope

Every change MUST identify its target version, owned paths, intended outcome, and explicit non-goals before modification. Work outside that declaration is out of scope.

### R-02 — Respect repository identity

The canonical repository is `https://github.com/CSY8515/Ultra-Brain.git`, with `main` as its release branch. The existing workspace root is the repository root. A nested `Ultra-Brain` repository or a second origin MUST NOT be created. See [REPOSITORY_STRATEGY.md](REPOSITORY_STRATEGY.md).

### R-03 — Protect boundaries

Only Ultra Brain artifacts explicitly included in the current scope MAY be changed. `OS Ecosystem`, `Living OS`, `Universal Learning Engine` (ULE), other repositories, and personal data are protected and MUST NOT be modified, imported, copied, staged, or committed. See [WORKSPACE_PROTECTION.md](WORKSPACE_PROTECTION.md) and [BOUNDARY.md](BOUNDARY.md).

### R-04 — Prefer the smallest safe change

A change MUST preserve existing valid content and MUST NOT delete, overwrite, or restructure unrelated artifacts. Existing content and incoming content MUST be reviewed and deliberately reconciled when they collide.

### R-05 — Do not expose sensitive material

Secrets, tokens, credentials, private keys, and unnecessary personal data MUST NOT be stored in source, documentation, registries, fixtures, logs, commits, or releases.

### R-06 — Govern interfaces and contracts

Cross-boundary behavior MUST be described by a versioned interface and an explicit contract before implementation. Ownership, inputs, outputs, invariants, failure behavior, compatibility, and validation obligations MUST be stated. An implementation MUST NOT create an undocumented dependency across Meta OS, ecosystem, capability, project, or module boundaries.

### R-07 — Keep records consistent

Architecture, registries, schemas, interfaces, contracts, decisions, and release metadata MUST describe the same names, versions, ownership, paths, and status. A change that creates a known contradiction MUST NOT pass validation.

### R-08 — Pass the Evolution Gate

A proposed Meta OS, Core Meta OS, or material capability MUST pass every stage in [EVOLUTION.md](EVOLUTION.md): need test, existing Meta OS reuse test, existing Capability reuse test, architecture review, User approval, and only then development.

### R-09 — Validate before completion

Required documentation, structure, JSON, schemas, links, scope boundaries, Git state, and release evidence MUST pass the applicable checks in [VALIDATION_FRAMEWORK.md](VALIDATION_FRAMEWORK.md). Failed or missing evidence MUST be reported; it MUST NOT be represented as success.

### R-10 — Release deliberately

A release MUST satisfy [COMPLETION_RULE.md](COMPLETION_RULE.md) and [RELEASE_FRAMEWORK.md](RELEASE_FRAMEWORK.md). Force push, history rewriting, and bypass of required review or validation are prohibited.

## v0.1 restriction

For v0.1, work is limited to the Foundation structure, governance documents, registries, schemas, interface and contract guidance, validation guidance, release guidance, and scope-only README files for the five Core Meta OS domains. Runtime code, UI/UX, integrations, databases, AI APIs, BYOK, automation, and v0.2+ feature implementation are prohibited.

## Exceptions

Only the User may approve an exception. The exception MUST name the rule, scope, reason, risk, duration, and compensating controls, and MUST be recorded in [DECISION_LOG.md](DECISION_LOG.md) before use.
