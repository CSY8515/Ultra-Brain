# Collaboration & Connectivity Core Meta OS Requirements

| ID | Requirement | Evidence |
| --- | --- | --- |
| CON-API-001 | Enforce explicit connector operations and per-grant request budgets. | API management tests |
| CON-CNR-001 | Invoke only registered caller-supplied connector transports. | Connector tests |
| CON-CRD-001 | Store credential references only and resolve secret values only for a call. | Credential isolation tests |
| CON-IMP-001 | Import bounded JSON, JSONL, and CSV records with explicit rejection counts. | Import tests |
| CON-EXP-001 | Export deterministic bounded JSON, JSONL, and scalar CSV. | Export tests |
| CON-SYN-001 | Reconcile snapshots deterministically with explicit conflict policy. | Synchronization tests |
| CON-PLT-001 | Represent cross-platform exchange as validated neutral JSON. | Platform tests |
| CON-AI-001 | Gate external AI through typed connectors and explicit grant permission. | External AI tests |
| CON-REP-001 | Gate repository writes separately from repository reads. | Repository tests |
| CON-COM-001 | Gate communication separately and contain delivery errors. | Communication tests |
| CON-ECO-001 | Exchange through contracted ecosystem connectors without implementing an ecosystem. | Ecosystem tests |
| CON-REL-001 | Provide idempotency, sanitized events, bounded outputs, and fail-closed validation. | Reliability/adversarial tests |
| CON-SCP-001 | Safety, Enhancement, Automation, excluded domains, UI/UX, and deployment remain unchanged. | Frozen-scope tests |
