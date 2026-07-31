# Ultra Brain Development Standard

## Purpose and current applicability

This standard governs how approved Ultra Brain changes are prepared, developed, verified, and handed to release. For v0.1, “development” means Foundation documents, schemas, registries, and scope structure only. Runtime code, UI/UX, and v0.2+ features are outside scope.

## 1. Prepare

Before editing, the contributor MUST:

1. verify the workspace, Git root, branch, origin, and current status;
2. identify protected and unrelated paths;
3. define the target version, owned files, outcome, non-goals, and acceptance criteria;
4. inspect existing content and controlling decisions;
5. confirm that any material evolution has passed [EVOLUTION.md](EVOLUTION.md).

If the root or origin is unexpected, or the requested work would affect a protected project, work MUST stop before modification.

## 2. Design

Architecture and responsibility MUST precede implementation. The design MUST identify the owner layer, boundary, dependencies, data ownership, affected registries, interfaces, contracts, compatibility, failure behavior, security considerations, and validation plan.

Cross-boundary behavior MUST be interface-first and contract-governed. The design MUST favor reuse and the smallest coherent change.

## 3. Implement

Changes MUST remain within declared paths, preserve unrelated content, and follow [STANDARDS.md](STANDARDS.md). Generated or copied material MUST be reviewable and attributable; protected project content MUST NOT be copied into Ultra Brain.

Documentation MUST distinguish current fact, normative requirement, and future plan. Registry status and release claims MUST reflect actual state. Secrets and personal data MUST NOT be introduced.

## 4. Validate

The contributor MUST run all applicable checks in [VALIDATION_FRAMEWORK.md](VALIDATION_FRAMEWORK.md), including structural, document, JSON, schema, reference, identifier, path, boundary, sensitive-data, and Git-diff checks. A failure MUST be fixed or reported as a blocker; it MUST NOT be hidden by weakening a check.

Review MUST confirm that no UI, runtime, or later-version feature was implemented under a Foundation label.

## 5. Review

The final diff MUST be reviewed for intent, completeness, accidental changes, terminology, authority conflicts, stale references, and unsupported claims. Material architecture changes require decision traceability. Required User approval MUST be explicit.

## 6. Commit and publish

Publication is permitted only after completion and release gates pass. Immediately before commit and push, verify origin, branch, status, and diff summary. Commits MUST be cohesive and MUST NOT include protected or unrelated files. Force push and history rewriting are prohibited.

Each release MUST point to a verified commit, match its version records, and include accurate limitations. See [RELEASE_FRAMEWORK.md](RELEASE_FRAMEWORK.md) and [COMPLETION_RULE.md](COMPLETION_RULE.md).

## Evidence

A completed change MUST leave enough evidence to reproduce the validation result and determine what was created, changed, excluded, committed, pushed, and released. Known issues and skipped non-applicable checks MUST be stated plainly.
