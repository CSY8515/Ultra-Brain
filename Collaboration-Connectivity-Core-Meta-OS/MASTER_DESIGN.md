# Collaboration & Connectivity Core Meta OS MASTER Design

## Mission

Provide one governed exchange plane for APIs, connectors, data portability,
synchronization, platforms, external AI, repositories, communication, and
ecosystem relationships while preserving explicit authority, provenance,
boundedness, secret isolation, and failure containment.

## Invariants

1. Every external operation uses a locally registered connector specification and transport.
2. Every operation requires a current approved Safety-referenced grant.
3. Registration, visibility, or platform identity never implies authorization.
4. Credential values are supplied by a caller resolver and are never stored, logged, serialized, or returned.
5. Inputs and outputs are bounded JSON; import/export formats are explicit.
6. Request and record budgets fail closed before an external operation.
7. External AI, repository writes, and communication require separate grant flags.
8. Synchronization is deterministic, snapshot-based, and conflict-policy-driven.
9. Transport exceptions expose stable sanitized failure evidence only.
10. No daemon, polling, UI, deployment, dynamic connector loading, or lower-layer product exists.

## Component topology

`ConnectivityCore` owns a local connector allowlist and idempotency ledger.
`ApiManager` checks connector, operation, sensitive-domain, and request budgets.
`DataExchange` imports and exports bounded JSON, JSONL, and scalar CSV.
`Synchronizer` reconciles immutable exchange records using revisions and explicit
conflict policy. Type-specific facade methods enforce external-AI, repository,
communication, and ecosystem connector kinds.

## Information model

- `CredentialReference`: opaque identifier, provider, and requested scopes; no secret.
- `ConnectorSpec`: connector kind, platform, API version, operations, and payload limit.
- `ConnectionGrant`: Safety reference, validity, allowlists, budgets, and sensitive-domain permissions.
- `OperationRequest`: connector operation, bounded JSON payload, and optional idempotency key.
- `OperationResult`: sanitized state, digest, validated output, timestamps, and events.
- `ExchangeRecord`: stable identity, revision, timestamp, source, tombstone, and data.
- `SyncResult`: deterministic merged snapshot and explicit conflict resolutions.

## Operation lifecycle

1. Locate the explicitly registered connector.
2. Validate request, connector specification, payload size, and grant currency.
3. Check connector and operation allowlists, request budget, and sensitive-domain flags.
4. Resolve an opaque credential reference through the caller when required.
5. Invoke the registered transport exactly once and immediately discard the local secret reference.
6. Validate and bound the returned JSON value.
7. Return immutable audit state and retain only a digest/result for an idempotent request.

## Data portability and synchronization

Import and export do not touch the filesystem. Callers provide text and receive
records or text. Synchronization accepts two explicit snapshots. Higher
revisions win; equal-revision divergence follows `local_wins`, `remote_wins`,
`latest`, or `reject`. Ambiguous `latest` conflicts fail closed.

## Compatibility

The Python and JSON contract version is `0.5.0`. Additive changes may remain in
`0.5.x`. Persistent credentials, autonomous discovery, background sync,
unregistered network clients, platform SDKs, or weakened authorization require
a new architecture and contract review.
