# Ultra Brain Repository Strategy

## Canonical repository

Ultra Brain uses one canonical Git repository:

- repository: `https://github.com/CSY8515/Ultra-Brain.git`
- local workspace rule: the User-designated `Ultra Brain` directory itself is the repository root
- release branch: `main`
- remote name: `origin`

The workspace root itself is the Git root. A nested `Ultra-Brain` directory, a nested Git repository, an alternate origin, or a separately cloned copy inside this workspace MUST NOT be created. Machine-specific absolute paths belong in execution evidence, not in portable repository configuration.

## One-repository model

The Foundation, five Core Meta OS scopes, registries, schemas, interfaces, contracts, validation guidance, and release records are versioned together. This provides one traceable governance baseline while preserving responsibility through top-level boundaries.

A Core Meta OS directory is an ownership boundary, not a repository boundary. It MUST NOT contain its own `.git` directory or independently managed release history. A proposal to split a repository is a material architecture change and MUST pass [EVOLUTION.md](EVOLUTION.md) and explicit User approval.

## Top-level layout

Foundation documents live at the repository root. Shared structural artifacts use these root directories:

- `registry/` for discoverable entity records;
- `schemas/` for machine-validatable data contracts;
- `interfaces/` for interaction-surface specifications;
- `contracts/` for cross-boundary obligations;
- `validation/` for validation guidance and evidence conventions;
- `tests/` for test scope and future test assets permitted by a target release.

The five Core Meta OS domains are separate top-level directories:

| Directory | Planned scope version | v0.1 content |
| --- | --- | --- |
| `Safety-Core-Meta-OS/` | v0.2 | Scope README only |
| `Enhancement-Core-Meta-OS/` | v0.3 | Scope README only |
| `Automation-Core-Meta-OS/` | v0.4 | Scope README only |
| `Collaboration-Connectivity-Core-Meta-OS/` | v0.5 | Scope README only |
| `Personal-Secretary-Core-Meta-OS/` | v0.6 | Scope README only |

No executable feature, runtime, dependency bundle, UI, page, component, or integration belongs in these directories for v0.1.

## Protected local content

`OS Ecosystem` is pre-existing protected local content and is not part of the Ultra Brain repository even if it is physically present beneath the workspace. `Living OS`, `Universal Learning Engine` (ULE), and all other repositories are likewise external. Their content MUST NOT be modified, copied, staged, committed, or included in an Ultra Brain release. See [WORKSPACE_PROTECTION.md](WORKSPACE_PROTECTION.md).

## Branch and publication policy

The `main` branch represents the integrated release line. Before commit, push, tag, or release, the Git root, current branch, origin URL, worktree status, and diff summary MUST be verified. Force push and history rewriting are prohibited.

A release tag MUST identify one reachable commit on the intended history. Release notes and registry metadata MUST match the tagged contents. See [RELEASE_FRAMEWORK.md](RELEASE_FRAMEWORK.md).

## Ownership and change placement

A change belongs at the narrowest top-level boundary that owns its responsibility. Cross-domain requirements belong in Foundation governance or an explicit interface and contract, not as duplicated files in multiple domains. Registry entries MUST point to canonical paths and MUST NOT imply ownership of protected external projects.

## v0.1 constraint

v0.1 establishes this structure and its governance only. Repository splitting, deployment configuration, runtime packaging, UI structure, and implementation for later roadmap versions are outside the v0.1 scope.
