# v0.2 Safety Core Meta OS Architecture Review

## 1. Decision

The v0.2 need is already assigned to the existing `safety-core-meta-os` entity.
No new Meta OS, OS Ecosystem, or Core Capability is created. The approved change
implements the narrowest useful Safety baseline inside `Safety-Core-Meta-OS/`
and retains the v0.1 authority hierarchy:

> User > Ultra Brain > Meta OS > OS Ecosystem > Capability > Project > Module

The User approved development and the minimum root release-integration changes
on 2026-08-01. Foundation authority instruments remain unchanged.

## 2. Reviewed need

Later Ultra Brain milestones require a reusable way to refuse unsafe execution,
verify evidence integrity, assess risk, preserve audit history, contain incidents,
and demonstrate recoverability. Documentation alone cannot establish that these
controls behave consistently. v0.2 therefore provides executable reference
controls and their machine-readable contracts.

## 3. Reuse tests

- Existing Meta OS reuse: **pass**. The need belongs to the reserved Safety Core
  Meta OS and does not justify another Meta OS.
- Existing Capability reuse: **not applicable**. The v0.1 capability registry is
  empty and creating a Core Capability is explicitly outside v0.2 scope.
- Foundation reuse: **pass**. Existing identity, precedence, boundaries,
  registry fields, interface/contract concepts, validation gates, and release
  discipline are inherited rather than redesigned.

## 4. Architecture choice

Use a local, dependency-free Python reference library with JSON artifacts and a
narrow CLI. All stateful operations are explicitly invoked. There is no daemon,
scheduler, database, network listener, connector, or UI.

The control flow is:

> Request -> Validate -> Verify integrity -> Assess risk -> Check incidents and
> recovery -> Decide -> Record evidence -> Return allow/deny/review

Only `allow` is executable evidence. `review` is fail-closed and grants no
execution authority. The library never performs the requested business action.

## 5. Six-axis impact

| Axis | Impact |
| --- | --- |
| Global Governance | Implements subordinate controls; does not alter precedence or user authority. |
| Global Memory | Adds minimal hash-chained safety evidence and append-oriented incident history. |
| Global Decision | Produces explainable safety decisions with reasons and control evidence. |
| Global Knowledge | Uses explicit risk inputs; does not claim inferred knowledge or learning. |
| Global Capability | Activates the registered Safety Meta OS baseline without creating a Core Capability. |
| Global Ecosystem | Publishes one local interface and contract; makes no external integration. |

## 6. Principal risks and containment

| Risk | Containment |
| --- | --- |
| Safety control becomes an executor | API returns decisions only; no arbitrary command execution exists. |
| Missing evidence is treated as success | Required evidence fails closed. |
| Audit history is silently edited | Sequence and SHA-256 hash-chain verification detects mutation/removal/reordering. |
| Backup archive escapes its boundary | Relative-path normalization rejects absolute paths, traversal, and symlinks. |
| Recovery destroys current data | Recovery refuses existing targets and never overwrites by design. |
| Monitoring becomes automation | It evaluates only caller-supplied observations and returns signals. |
| Incident shortcuts conceal failure | A constrained state machine rejects invalid transitions. |
| Logs collect sensitive values | Records use allowlisted fields and reject known sensitive-key names. |

## 7. Compatibility

The public Python and JSON contract version is `0.2.0`. Additive compatible
changes may remain within `0.2.x`; removing fields, weakening a mandatory gate,
or changing decision semantics requires architecture review and a new contract
version. v0.1 Foundation documents remain historical authority baselines.

## 8. Approval outcome

Architecture Review: **approved for v0.2 implementation** within the declared
boundary. Release remains conditional on validation, tests, exact-scope diff
review, registry/version coherence, commit, push, immutable tag, and GitHub
Release verification.
