# Ultra Brain Policies

## Purpose and scope

These policies translate the [CONSTITUTION.md](CONSTITUTION.md), [GOVERNANCE.md](GOVERNANCE.md), and [RULES.md](RULES.md) into repeatable controls. They govern v0.1 Foundation work only and authorize no runtime, UI/UX, or later-version implementation.

## P-01 — Change control

Every change MUST have a stated purpose, target version, path scope, owner layer, acceptance criteria, and rollback or recovery approach appropriate to its risk. Material architecture or governance changes require an entry in [DECISION_LOG.md](DECISION_LOG.md).

A change MUST be paused when its actual impact exceeds its approved scope, when evidence is insufficient, or when a higher-authority instruction is ambiguous.

## P-02 — Scope isolation

Work MUST remain inside the canonical Ultra Brain repository and the paths authorized for the task. Protected projects—including `OS Ecosystem`, `Living OS`, and `Universal Learning Engine`—MUST be treated as external even if they appear beneath or beside the workspace. They MUST NOT be used as an implementation source or altered as a side effect.

## P-03 — Preservation and recovery

Existing valid artifacts MUST be inspected before change. Merges MUST preserve distinct valid intent, particularly for `README.md` and `.gitignore`. Destructive changes require explicit User approval and a verified recovery path. Git history MUST NOT be rewritten and force push MUST NOT be used.

## P-04 — Sensitive information

Repositories and releases MUST contain no credentials, access tokens, private keys, authentication artifacts, or unnecessary personal information. Examples and registry records MUST use non-secret placeholders. Suspected exposure MUST stop publication until containment and review are complete.

## P-05 — Architecture and dependency

Dependencies MUST follow the layer model and boundaries defined in [ARCHITECTURE.md](ARCHITECTURE.md), [MASTER_DESIGN.md](MASTER_DESIGN.md), and [BOUNDARY.md](BOUNDARY.md). Cross-layer or cross-domain coupling MUST be explicit, minimal, and mediated by documented interfaces and contracts.

New dependencies, Meta OS domains, or capabilities MUST pass the [EVOLUTION.md](EVOLUTION.md) gate. Reuse is the default outcome unless evidence shows that existing scopes cannot satisfy the need.

## P-06 — Interface and contract lifecycle

An interface defines the interaction surface; a contract defines the obligations of all parties. Each approved interface or contract MUST have a stable identifier, owner, version, scope, compatibility statement, validation criteria, and lifecycle status. A breaking change requires architecture review, migration intent, User approval when material, and a new version.

No v0.1 interface or contract document constitutes executable integration.

## P-07 — Registry integrity

Registries MUST be machine-readable, conform to their applicable schemas, use unique identifiers, and refer only to known repository paths or explicitly external entities. Registry status MUST reflect actual lifecycle state; planned work MUST NOT be marked implemented or released.

## P-08 — Validation evidence

Validation MUST be reproducible and proportional to change risk. Evidence MUST identify what was checked, the command or method, the result, and any limitation. A skipped mandatory check is a failure unless the User has recorded an exception.

## P-09 — Release control

Only a complete, validated, traceable state MAY be released. Before commit, push, or release, the repository root, origin, branch, status, and diff summary MUST be verified. Publication MUST use the intended version and release notes and MUST follow [RELEASE_FRAMEWORK.md](RELEASE_FRAMEWORK.md).

## P-10 — Decision traceability

Decisions that establish scope, authority, architecture, exceptions, release readiness, or evolution MUST be recorded. Records are append-oriented: corrections supersede earlier decisions instead of silently rewriting their meaning.

## Exceptions and enforcement

Exceptions follow [RULES.md](RULES.md). A policy violation blocks completion under [COMPLETION_RULE.md](COMPLETION_RULE.md) until corrected or explicitly accepted by the User with recorded residual risk.
