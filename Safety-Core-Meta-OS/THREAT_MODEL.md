# Safety Core Meta OS Threat Model

## Protected properties

- user authority and Foundation precedence;
- accuracy and explainability of safety decisions;
- integrity and ordering of audit evidence;
- repository and filesystem boundary containment;
- recoverability without destructive overwrite; and
- truthful incident and validation status.

## Trust assumptions

The Python runtime, operating system, and caller-granted filesystem permissions
are outside this baseline. Callers, JSON input, paths, archives, existing logs,
approval claims, integrity claims, and incident records are untrusted inputs.

## Threats and controls

| Threat | Control | Residual boundary |
| --- | --- | --- |
| Fabricated approval | Structured approval fields plus policy gate and audit reason | Identity proof requires an external authority contract |
| Risk downgrade | Engine computes level from bounded numeric inputs | Input truth remains caller/evidence responsibility |
| Log mutation | Hash chain and sequence verification | A fully replaced ledger needs an external trusted anchor |
| Audit resource exhaustion | Canonical audit data is capped at 256 KiB, depth 32 from root depth 0, and 10,000 nodes including object keys; each JSONL record including newline is capped at 512 KiB, and each ledger at 64 MiB or 100,000 records | Limits bound one local ledger but do not provide an availability or retention service |
| Input resource exhaustion | Policy and request JSON files are limited to stable regular files of at most 1 MiB; public permissions, incident inputs, and incident history are capped at 64 items; field and sensitive-key walks are bounded before expensive processing | Limits bound individual calls but do not provide service-level availability guarantees |
| Sensitive data in logs | Unicode NFKC-normalized key denylist, allowlisted decision fields, payload exclusion | Free-text reasons remain caller responsibility outside public append API |
| Path traversal | Canonical relative paths and root containment | OS/runtime compromise is out of scope |
| Symlink escape | Symlinks rejected in protected filesystem operations | Platform-specific reparse points rely on runtime path resolution |
| Malicious archive | Physical and logical ZIP quotas, pre-hash source file/directory-entry limits, bounded member count/path depth, compression allowlist, duplicate rejection, and manifest/hash verification | ZIP parser and operating-system handle capacity remain platform boundaries; secure publication fails closed where guarded Windows handles or POSIX `O_TMPFILE`/`linkat` are unavailable; malware inspection is out of scope |
| Destructive restore | Any existing destination is rejected; directories and files are created exclusively; a final bounded traversal compares both files and directories with the verified manifest | Failure after destination creation may leave a partial new tree for caller inspection and cleanup; no pre-existing destination is modified |
| Incident bypass | Active containment included in execution gate | Incident truth depends on supplied current record |
| Safety core used as executor | No command/subprocess/network execution API | Caller remains accountable for its own executor |

## Non-claims

v0.2 does not claim confidentiality, authentication, authorization-provider
identity, cryptographic signatures, malware detection, availability guarantees,
distributed consensus, secure deletion, remote attestation, or autonomous
incident response.
