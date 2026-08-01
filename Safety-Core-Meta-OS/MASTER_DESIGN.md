# Safety Core Meta OS MASTER Design

## 1. Mission

Safety Core Meta OS is the mandatory safety control plane beneath Ultra Brain
governance. It converts declared rules, evidence, risk, integrity, recovery, and
incident state into deterministic safety findings while leaving execution with
the authorized lower layer.

## 2. Design principles

1. **Fail closed:** absent, invalid, stale, or contradictory mandatory evidence
   cannot produce `allow`.
2. **Separate decision from execution:** the core evaluates; it never performs
   the requested business action.
3. **Evidence before claims:** validation, integrity, recovery, and audit claims
   carry reproducible evidence.
4. **Least authority:** operations are bounded to explicit roots and inputs.
5. **Non-destructive recovery:** archives are verified before extraction and
   any destination path that already exists is rejected.
6. **Determinism:** equal canonical inputs and policy produce equal control
   results, apart from explicit record IDs and timestamps.
7. **Data minimization:** safety records exclude payloads and sensitive keys.
8. **Human authority:** high-risk or critical work requires explicit approval;
   the reference core does not invent consent.

## 3. Component model

| Component | Responsibility | Explicit non-responsibility |
| --- | --- | --- |
| Validation | Validate artifacts and execution requests | Approval or execution |
| Integrity | Hash files, manifests, archives, and ledgers | Confidentiality or identity proof |
| Monitoring | Evaluate one supplied observation against thresholds | Polling, scheduling, notification |
| Risk | Calculate deterministic likelihood-impact risk | Prediction, learning, hidden inference |
| Logging | Append minimal hash-chained records | General application logging |
| Audit | Verify and filter safety records | Editing or deleting evidence |
| Backup | Create verified archives beneath an explicit source root | Retention scheduling or remote storage |
| Recovery | Verify and restore into a new, non-existing destination | In-place overwrite or destructive rollback |
| Execution Safety | Return `allow`, `deny`, or `review` from mandatory gates | Running the requested operation |
| Incident Management | Enforce incident lifecycle and containment state | Paging, messaging, external coordination |

## 4. Control topology

`SafetyCore` is the facade. It accepts an `ExecutionRequest`, a validated policy,
integrity evidence, active incident information, and optional recovery evidence.
It delegates to the validation and risk components, applies execution gates,
records the result when a ledger is configured, and returns a `SafetyDecision`.

The execution gate order is fixed:

1. contract validation;
2. prohibited operation and scope checks;
3. required permission checks;
4. integrity evidence checks;
5. deterministic risk classification;
6. active-incident containment checks;
7. reversibility and recovery-plan checks;
8. explicit approval checks;
9. final decision and audit evidence.

A denial at an earlier gate is preserved; a later control cannot convert it to
allow. Multiple reasons may be returned for completeness.

## 5. Information model

The core uses JSON-compatible records with stable lower-kebab-case identifiers,
UTC timestamps, and semantic contract versions. Canonical JSON uses sorted keys
and compact separators before hashing. Audit records contain metadata and control
outcomes, not user content or operation payloads.

Primary records are:

- `ExecutionRequest` and `SafetyDecision`;
- `RiskAssessment`;
- `Observation` and `MonitorSignal`;
- `AuditRecord`;
- `BackupManifest` and `RecoveryResult`; and
- `Incident` with append-only transition history.

## 6. Failure semantics

- malformed input: reject with a typed validation error;
- missing mandatory execution evidence: return `deny` or `review`, never allow;
- ledger corruption: verification fails and affected evidence is unusable;
- unsafe path or archive entry: stop before write;
- backup verification failure: produce no successful recovery result;
- existing recovery target: refuse without modification;
- failure after exclusive recovery-target creation: fail closed, but a partial
  newly-created destination may remain for explicit inspection and cleanup;
- invalid incident transition: reject and retain the prior state;
- unsupported schema or contract version: reject explicitly.

## 7. Operational boundary

The package uses only the Python standard library. It performs no networking,
credential discovery, subprocess execution, dynamic code loading, background
work, or telemetry. All filesystem mutations are direct caller requests limited
to ledger append, archive creation, and recovery into a new destination. ZIP
archive size, member count, per-file size, total logical size, manifest size,
path depth, and compression methods are bounded. Recovery-held file and
directory handles are therefore finite under those quotas; actual handle
capacity and ZIP parser resource behavior remain operating-system and runtime
boundaries, and exhaustion fails closed.

## 8. Assurance model

Release evidence combines:

- artifact and local-link validation;
- JSON parsing and controlled-field validation;
- registry path and identifier checks;
- policy, interface, and contract coherence checks;
- unit and adversarial tests;
- v0.1-to-v0.2 regression protection for frozen paths;
- secret-pattern and prohibited-scope scans; and
- exact Git diff, version, registry, tag, and release verification.

The requirement-to-test mapping is maintained in [Requirements](REQUIREMENTS.md).
