# Ultra Brain Workspace Protection

## Purpose

This document prevents work on Ultra Brain from changing unrelated repositories, protected projects, user data, credentials, or Git history. It applies before, during, and after every workspace operation.

## Authorized workspace

The authorized repository root is the User-designated `Ultra Brain` workspace returned by `git rev-parse --show-toplevel`, connected to `https://github.com/CSY8515/Ultra-Brain.git`. Its exact machine path MUST be verified for each task and recorded as execution evidence rather than embedded in portable configuration. Authorization to work in this root does not authorize every child path: only paths explicitly included in the current Ultra Brain task may be changed.

## Protected and excluded scope

The following are protected and outside Ultra Brain ownership:

- `OS Ecosystem`, including any repositories beneath it;
- `Living OS`;
- `Universal Learning Engine` (ULE);
- any other project, repository, workspace, or user directory;
- credentials, authentication state, secrets, and unrelated personal data.

Protected content MUST NOT be edited, deleted, moved, renamed, copied, imported, staged, committed, or used as a source of implementation. Its presence does not make it part of Ultra Brain.

## Preflight controls

Before modifying files, the operator MUST:

1. resolve and verify the current path and Git root;
2. verify that `origin` is the canonical repository and that the intended branch is `main`;
3. review Git status and the relevant existing files;
4. enumerate the exact paths authorized for change;
5. confirm that no authorized path resolves into a protected directory or nested repository.

An unexpected root, origin, branch, nested `.git`, symlink or redirection into protected scope, or unclear ownership is a stop condition.

## Operation controls

Operations MUST use explicit, narrow paths. Broad recursive operations, unresolved path variables, or commands that can cross the workspace boundary MUST NOT be used. Existing artifacts MUST be preserved unless deletion is explicitly approved and recoverable.

Dependencies or tools MUST NOT be installed merely for convenience. Any required installation needs a scoped reason and MUST NOT alter protected projects or global user state without explicit approval.

## Git protections

The following are prohibited:

- force push;
- history rewriting;
- `reset --hard` or an equivalent destructive reset;
- changing a mismatched origin without first reporting it;
- staging with an unreviewed broad selection;
- committing ignored or protected project content;
- deleting or overwriting remote content to resolve an unrelated-history merge.

Remote and local content collisions MUST be inspected file by file. Valid remote README content, valid local design content, and `.gitignore` protections MUST be preserved and deliberately reconciled.

## Information protection

Secrets, tokens, API keys, private keys, session data, and unnecessary personal information MUST NOT appear in files, diffs, logs, registry records, commits, tags, or release notes. Suspected exposure requires an immediate stop, containment, and User notification; the exposed value MUST be treated as compromised.

## Verification and incident response

Before completion, the final diff and staged file list MUST show only authorized Ultra Brain paths. If an unintended change occurs, stop further work, preserve evidence, avoid destructive cleanup, and report the exact affected paths and recovery options to the User.

Compliance with this document is a release gate under [VALIDATION_FRAMEWORK.md](VALIDATION_FRAMEWORK.md), [COMPLETION_RULE.md](COMPLETION_RULE.md), and [RELEASE_FRAMEWORK.md](RELEASE_FRAMEWORK.md).
