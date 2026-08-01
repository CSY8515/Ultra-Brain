# Collaboration & Connectivity Core Meta OS

## v0.5 Collaboration & Connectivity baseline

This Core Meta OS provides Ultra Brain's governed connectivity boundary. It
manages registered connector metadata, API request budgets, caller-resolved
credential references, bounded import/export, deterministic synchronization,
cross-platform exchanges, external AI calls, repository access, communication,
and ecosystem connections.

The runtime is dependency-free and caller-driven. It never discovers accounts,
stores credential values, opens a network connection by itself, polls, runs a
background worker, or interprets a connector response before validation. A
caller registers a connector transport and supplies a current, Safety-referenced
grant for every operation.

## Components

| Component | Responsibility | Boundary |
| --- | --- | --- |
| API management | Validate operations and enforce per-grant request budgets | No HTTP server, routing service, or autonomous retry |
| Connector registry | Bind declared connector specifications to caller functions | No dynamic import or connector discovery |
| Credentials | Resolve opaque credential references at call time | No secret value storage, logging, or serialization |
| Import/export | Convert bounded JSON, JSONL, and scalar CSV records | No filesystem watching or implicit persistence |
| Synchronization | Reconcile explicit snapshots with declared conflict policy | No continuous sync or hidden writes |
| Cross-platform | Exchange validated, platform-neutral JSON records | No platform-specific authority inference |
| External AI | Route only through an `external_ai` connector and explicit grant | No provider SDK, model autonomy, or retained prompt |
| Repository | Route repository reads and explicitly authorized writes | No Git command or repository mutation in the runtime |
| Communication | Route explicitly authorized message operations | No inbox collection, delivery daemon, or identity assumption |
| Ecosystem | Route contracted ecosystem exchanges | No OS Ecosystem implementation or adoption |

## Public API

The `connectivity_core` package exposes immutable records and
`ConnectivityCore`. Register a declared transport with `register_connector()`,
then use `invoke()` or the type-specific external-AI, repository,
communication, and ecosystem methods. `DataExchange` and `Synchronizer` are
pure local transformations.

## Safety and scope

Foundation v0.1, Safety v0.2, Enhancement v0.3, and Automation v0.4 remain
cumulative and unchanged. Registration is not authorization. A current grant
must allow the connector, operation, request count, and relevant sensitive
domain. Credential values exist only in caller memory during a transport call.
Errors expose stable codes rather than transport exception text.

This implementation contains no Personal Secretary, UI/UX, Streamlit, Core
Capability, OS Ecosystem, Living OS, Universal Learning Engine, Ultra Brain-
exclusive capability, deployment, daemon, or bundled third-party integration.

Run validation and tests from this directory:

```text
python validation/validate_connectivity_core.py
python -m unittest discover -s tests -v
```
