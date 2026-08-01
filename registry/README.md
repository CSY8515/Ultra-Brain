# Ultra Brain Registries

This directory contains the declarative registry set established by v0.1 and
extended through the approved v0.4 Automation release. Registries index governed
entities; they do not load modules, execute workflows, or grant authority.

## Files

- `meta_os_registry.json`: five Core Meta OS definitions;
- `ecosystem_registry.json`, `capability_registry.json`, and `project_registry.json`: valid empty admission queues;
- `repository_registry.json`: the canonical Ultra Brain repository;
- `rule_registry.json`, `policy_registry.json`, and `standard_registry.json`: foundation governance baselines;
- `decision_registry.json`: accepted Foundation and v0.2-v0.4 decisions;
- `release_registry.json`: immutable v0.1 through v0.4 release records;
- `interface_registry.json` and `contract_registry.json`: approved Safety,
  Enhancement, and Automation publication indexes.

All records use repository-relative paths and the exact canonical repository URL. Changes require schema validation, global ID uniqueness, path verification, and release review.
