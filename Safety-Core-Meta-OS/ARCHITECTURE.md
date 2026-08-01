# Safety Core Meta OS Architecture

## 1. Authority and boundary

This architecture is subordinate to the Ultra Brain Constitution, Governance,
Rules, Policies, Standards, and global architecture. Safety Core Meta OS owns
validation, integrity, monitoring, risk, safety logging and audit, backup and
recovery controls, execution-safety decisions, and incident containment within
its registered Meta OS scope.

It does not own Ultra Brain governance, lower-layer business execution, other
Core Meta OS implementations, user-interface concerns, or external systems.

## 2. Layers

| Layer | Artifacts | Dependency direction |
| --- | --- | --- |
| Governance binding | architecture, requirements, threat model | Inherits Foundation authority |
| Contract | registry, interface, contract, policy, schemas | Defines observable obligations |
| Domain | risk, integrity, monitoring, audit, backup/recovery, incidents | Pure or bounded safety logic |
| Control | validation and execution gate | Composes domain findings fail-closed |
| Adapter | narrow CLI | Converts local JSON/filesystem input; adds no authority |
| Assurance | validator and tests | Verifies all layers and release boundary |

Dependencies point downward through declared Python imports. Domain modules do
not import the CLI. Audit does not alter domain outcomes. The CLI does not bypass
the control facade.

## 3. Public boundaries

The canonical interface is `interfaces/safety_core.interface.json`; obligations
are bound by `contracts/safety_core.contract.json`. The interface is local and
in-process/CLI only. It is not a network protocol.

The public package exports:

- `SafetyCore.assess_execution`;
- `RiskEngine.assess`;
- `IntegrityVerifier` manifest and verification operations;
- `AuditLedger.append`, `verify`, and `query`;
- `Monitor.evaluate`;
- `BackupManager.create` and `verify`;
- `RecoveryManager.recover`;
- `IncidentManager.create` and `transition`; and
- `validate_execution_request` and artifact validation.

## 4. State ownership

- callers own request payloads and source files;
- Safety Core owns only its decision/evidence representation;
- a ledger owner controls the ledger path but cannot obtain a valid verification
  result after mutating history;
- a backup source remains caller-owned; the archive and manifest are explicit
  output artifacts;
- recovery writes only new files under the caller-approved destination;
- incident records are caller-persisted values whose transitions are validated
  by Safety Core.

No implicit global state or database is created.

## 5. Trust boundaries

All JSON, paths, archive members, timestamps, hashes, permissions, approvals,
and incident records supplied by a caller are untrusted until validated. A
filesystem path is authorized only relative to an explicit root. Symlinks are
rejected for backup and recovery inputs because their resolved authority may
differ from their visible path.

Hashing establishes integrity relative to known evidence; it does not establish
identity, authorization, confidentiality, or truth.

## 6. Decision semantics

- `allow`: every mandatory gate passed; the caller may separately decide to
  execute under its own authority.
- `deny`: one or more mandatory controls forbid execution.
- `review`: human approval or accepted-risk authority is required. It is
  non-executable and therefore fail-closed.

The decision includes ordered reason codes, risk evidence, policy version, and
request identity. No caller-provided result field can override these semantics.

## 7. Change and compatibility

Contract and schema files use semantic version `0.2.0`. Additive compatible
changes may remain within `0.2.x`; removing fields, weakening a mandatory gate,
or changing decision semantics requires architecture review and a new contract
version.

## 8. Exclusions

There is no RBAC service, authentication provider, encryption service, secret
store, malware scanner, SIEM, remote backup, workflow engine, scheduler, notifier,
agent, connector, database, deployment, UI/UX, or Streamlit application in v0.2.
