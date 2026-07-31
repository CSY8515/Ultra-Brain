# Ultra Brain Standards

## Purpose

This document defines the minimum quality conventions for v0.1 Foundation artifacts. It is subordinate to [RULES.md](RULES.md) and [POLICIES.md](POLICIES.md).

## Normative language

`MUST` and `MUST NOT` are mandatory. `SHOULD` and `SHOULD NOT` describe the expected default and require recorded rationale when departed from. `MAY` is optional. Definitions in [TERMINOLOGY.md](TERMINOLOGY.md) apply throughout the repository.

## S-01 — Documentation

A normative document MUST state its purpose and scope, use one unambiguous term for each concept, distinguish current state from future intent, and link to the controlling documents it depends on. Markdown headings MUST be hierarchical and links MUST be repository-relative.

Claims MUST be testable or traceable. Planned v0.2+ work MUST be labeled as scope or roadmap, never as implemented behavior.

## S-02 — Names and identifiers

Official product and domain names MUST match [TERMINOLOGY.md](TERMINOLOGY.md). Repository document names use uppercase `SNAKE_CASE.md` where established. Registry and schema file names use lowercase `snake_case.json`. Stable entity identifiers SHOULD use lowercase, hyphen-separated values with an `ultra-brain` or entity-type namespace when needed to avoid ambiguity.

Identifiers MUST be unique within their registry and MUST NOT be recycled for a different entity.

## S-03 — Versions and dates

Version values MUST follow their applicable schema and the repository release convention. The `VERSION` milestone value is `0.1`, its tag is `v0.1`, and registry or schema fields that require semantic versions use three components such as `0.1.0`. A single field MUST NOT mix prefixed and unprefixed forms. Dates MUST use ISO 8601 `YYYY-MM-DD`; timestamps, when required, MUST include a timezone.

## S-04 — JSON and schemas

JSON MUST be UTF-8, syntactically valid, free of comments and trailing commas, and formatted with two-space indentation. Each registry MUST identify its registry version and schema version. Required fields, types, enumerations, and reference rules MUST be defined by the applicable schema.

A JSON artifact MUST validate against its declared schema before release. Empty registries MUST use a valid empty collection, not an invented placeholder record.

## S-05 — Registries

Each entity record MUST provide, directly or through an unambiguous envelope: entity ID, entity type, name, scope, status, owner layer, parent, repository, path, interface references, contract references, current version, created date, and updated date. Nullable fields MUST be represented consistently with their schema.

Paths MUST be repository-relative and MUST resolve when they describe local artifacts. Repository references MUST distinguish canonical local ownership from external or protected scope. See [REGISTRY.md](REGISTRY.md).

## S-06 — Interfaces and contracts

Every interface specification MUST identify its ID, version, owner, consumers, operations or exchanged information, inputs, outputs, errors, security boundary, compatibility, and validation method.

Every contract MUST identify its parties, preconditions, obligations, invariants, success criteria, failure behavior, data ownership, version, compatibility, and validation evidence. An interface or contract with status `draft` MUST NOT be presented as operational.

## S-07 — Architecture decisions

A material decision record MUST contain a stable ID, date, status, decision, rationale, consequences, authority, and related artifacts. Later changes MUST supersede earlier records explicitly. See [DECISION_LOG.md](DECISION_LOG.md).

## S-08 — Validation

Validation MUST cover the changed artifact and its references. At minimum, v0.1 release validation includes required-file presence, Markdown link resolution, JSON parsing, schema validation, identifier uniqueness, path consistency, scope-boundary checks, secret review, repository identity, and Git diff review.

Results MUST be reported as pass, fail, or not applicable with a reason. See [VALIDATION_FRAMEWORK.md](VALIDATION_FRAMEWORK.md).

## S-09 — Git and release

Commits SHOULD be cohesive and use an imperative summary. Before publication, the canonical origin, `main` branch, cleanly understood status, and intended diff MUST be verified. Force push and history rewriting are prohibited. A release MUST be traceable to one commit and one release record.

## Conformance

An artifact conforms only when all applicable `MUST` requirements pass. A justified deviation from a `SHOULD` requirement MUST be recorded in the relevant decision or validation evidence.
