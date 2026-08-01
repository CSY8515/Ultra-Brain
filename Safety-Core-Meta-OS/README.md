# Safety Core Meta OS

Safety Core Meta OS is the v0.2 safety control plane for Ultra Brain. It turns
the v0.1 governance and assurance obligations into explicit, testable controls
without changing the Foundation architecture.

## v0.2 status

Version `0.2` implements a dependency-free reference core for:

- validation and integrity verification;
- explicit, caller-driven monitoring;
- deterministic risk assessment;
- append-only, hash-chained logging and audit queries;
- verified backup and non-destructive recovery;
- fail-closed execution-safety decisions; and
- governed incident lifecycle management.

The implementation is a Meta OS control surface. It does not execute approved
business actions, schedule work, monitor in the background, send notifications,
connect to external services, or provide a user interface.

## Start here

1. [Architecture Review](ARCHITECTURE_REVIEW.md)
2. [MASTER Design](MASTER_DESIGN.md)
3. [Architecture](ARCHITECTURE.md)
4. [Requirements](REQUIREMENTS.md)
5. [Threat Model](THREAT_MODEL.md)

Machine-readable definitions are under `registry/`, `interfaces/`, `contracts/`,
`policies/`, and `schemas/`. The Python package is `safety_core/`.

## Validate and test

Run from this directory:

```text
python -B validation/validate_safety_core.py
python -B -m unittest discover -s tests -v
```

The command-line surface is intentionally narrow:

```text
python -B -m safety_core.cli validate
python -B -m safety_core.cli assess request.json
python -B -m safety_core.cli verify-log audit.jsonl --expected-count 2 --expected-head <independent-head-hash>
python -B -m safety_core.cli backup SOURCE BACKUP.zip
python -B -m safety_core.cli recover BACKUP.zip DESTINATION
```

Recovery rejects any destination path that already exists. If recovery fails
after exclusive destination creation, a partial newly-created tree may remain
for caller inspection and cleanup; no pre-existing destination is modified.
ZIP processing bounds physical and logical archive size, member count, per-file
size, manifest size, path depth, and compression methods. Recovery-held handles
are finite under those quotas, while actual operating-system handle capacity and
ZIP parser resource behavior remain platform boundaries and exhaustion fails
closed. Source traversal is also bounded before hashing, including files and
directory entries, and recovery compares the final file and directory tree to
the verified manifest. Secure archive publication requires the guarded Windows
handle path or POSIX `O_TMPFILE`/`linkat` primitives and fails closed when those
primitives are unavailable. Audit data is limited to 256 KiB of canonical
UTF-8, nesting depth 32 (root depth 0), and 10,000 nodes including object keys.
Policy and request JSON inputs must be stable regular files no larger than 1
MiB. Public collections such as permissions, active incidents, and incident
history are capped at 64 items, and sensitive-key matching applies Unicode NFKC
normalization before comparison. Each canonical JSONL record, including its
trailing newline, is limited to 512 KiB; a ledger is
limited to 64 MiB and 100,000 records. Limit violations fail closed. Monitoring
evaluates only the observation supplied by the caller. Reopening an existing
audit ledger for append requires its independently retained expected head hash
and record count. An `allow` decision is evidence, not the execution itself.

## Boundary

The following remain out of scope: Foundation redesign, other Core Meta OS
implementation, Core Capability, OS Ecosystem, Living OS, Universal Learning
Engine, Ultra Brain-exclusive features, UI/UX, Streamlit, networking, external
AI, connectors, schedulers, agents, and background automation.
