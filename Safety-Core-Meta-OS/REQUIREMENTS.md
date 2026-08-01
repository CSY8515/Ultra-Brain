# Safety Core Meta OS Requirements

## Functional requirements

| ID | Requirement | Evidence |
| --- | --- | --- |
| SAF-VAL-001 | Reject malformed, incomplete, or unsupported records. | Validator and malformed-input tests |
| SAF-INT-001 | Produce and verify SHA-256 manifests for bounded regular files. | Integrity tests |
| SAF-MON-001 | Evaluate only caller-supplied observations against explicit thresholds. | Monitoring tests |
| SAF-RSK-001 | Classify risk deterministically from likelihood and impact values 1-5. | Boundary-value tests |
| SAF-LOG-001 | Append minimal records with sequence, previous hash, and record hash. | Ledger tests |
| SAF-AUD-001 | Detect record mutation, removal, insertion, and reordering. | Tamper tests |
| SAF-BKP-001 | Create a verified archive without following symlinks or escaping the source root. | Backup tests |
| SAF-REC-001 | Verify before recovery and refuse existing targets or unsafe members. | Recovery adversarial tests |
| SAF-EXE-001 | Return allow only after all mandatory gates pass. | Execution matrix tests |
| SAF-INC-001 | Enforce the incident lifecycle and containment execution block. | State-machine tests |

## Safety requirements

| ID | Requirement |
| --- | --- |
| SAF-SAF-001 | `review` MUST be non-executable. |
| SAF-SAF-002 | Unknown operations and missing policy fields MUST fail closed. |
| SAF-SAF-003 | High/critical risk MUST require explicit approval; critical risk is denied by default policy. |
| SAF-SAF-004 | High/critical mutating work MUST provide a verified recovery plan. |
| SAF-SAF-005 | An active critical incident or explicit containment block MUST deny execution. |
| SAF-SAF-006 | Logs MUST reject sensitive-key names and MUST NOT store request payloads. |
| SAF-SAF-007 | Backup and recovery MUST reject symlinks, absolute paths, traversal, and overwrite. |
| SAF-SAF-008 | Safety Core MUST NOT execute arbitrary commands, network requests, or background work. |

## Release requirements

| ID | Requirement |
| --- | --- |
| SAF-REL-001 | All Safety validator checks and automated tests pass. |
| SAF-REL-002 | Frozen Foundation authority documents and other Core Meta OS directories are unchanged. |
| SAF-REL-003 | Root and local versions, registries, decision, changelog, tag, and release title agree on v0.2. |
| SAF-REL-004 | Commit, remote branch, immutable tag, and GitHub Release resolve to one reviewed revision. |
