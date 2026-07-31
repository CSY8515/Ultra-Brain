# Ultra Brain Registries

This directory contains the declarative v0.1 registry set described in [`../REGISTRY.md`](../REGISTRY.md). Registries index governed entities; they do not load modules, execute workflows, or grant authority.

## Files

- `meta_os_registry.json`: five Core Meta OS definitions;
- `ecosystem_registry.json`, `capability_registry.json`, and `project_registry.json`: valid empty admission queues;
- `repository_registry.json`: the canonical Ultra Brain repository;
- `rule_registry.json`, `policy_registry.json`, and `standard_registry.json`: foundation governance baselines;
- `decision_registry.json`: accepted v0.1 architecture decisions;
- `release_registry.json`: the v0.1 Foundation release record;
- `interface_registry.json` and `contract_registry.json`: valid empty publication indexes.

All records use repository-relative paths and the exact canonical repository URL. Changes require schema validation, global ID uniqueness, path verification, and release review.
