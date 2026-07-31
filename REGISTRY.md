# Registry Architecture

## Purpose

The Ultra Brain registry is the authoritative index of governed entities. It records identity, ownership, hierarchy, repository location, lifecycle state, interface references, contract references, and version information without implementing runtime discovery or orchestration.

The registry is declarative in v0.1. JSON files under [`registry/`](registry/) are source-controlled records; schemas under [`schemas/`](schemas/) define their structural contracts.

## Registry domains

| Registry | Authority | v0.1 population |
| --- | --- | --- |
| Meta OS | Top-level Meta OS identity and scope | Five Core Meta OS entries |
| Ecosystem | OS Ecosystem identity | Empty until an ecosystem is admitted |
| Capability | Reusable capability identity | Empty until a capability is admitted |
| Project | Governed project identity | Empty until a project is admitted |
| Repository | Repository identity and location | `CSY8515/Ultra-Brain` |
| Rule | Enforceable rule references | Foundation rules baseline |
| Policy | Decision-guidance references | Foundation policies baseline |
| Standard | Conformance references | Foundation standards baseline |
| Decision | Durable architecture and governance decisions | v0.1 foundation decisions |
| Release | Version and release state | Ultra Brain v0.1 Foundation |
| Interface | Published interaction boundaries | Empty until an interface is approved |
| Contract | Versioned behavioral obligations | Empty until a contract is approved |

## Common record contract

Every entity record contains:

- `id`: globally unique, stable, lower-kebab-case identifier;
- `entity_type`: controlled entity category;
- `name`: human-readable canonical name;
- `scope`: concise responsibility statement;
- `status`: lifecycle state;
- `owner_layer`: accountable hierarchy layer;
- `parent`: parent entity ID or `null`;
- `repository`: canonical repository URL;
- `path`: repository-relative path;
- `interface`: interface IDs used or an empty array;
- `contract`: contract IDs used or an empty array;
- `current_version`: current governed version;
- `created_date` and `updated_date`: ISO 8601 calendar dates.

Registry version fields use normalized three-part semantic versions. The v0.1 milestone is therefore represented as `0.1.0` inside registry records while the repository `VERSION` and prescribed Git tag remain `0.1` and `v0.1`.

Registry documents additionally declare `registry_version`, `schema_version`, registry identity, repository, and an `entities` array.

## Identity and lifecycle

IDs are immutable after publication. Names and paths may change only through a recorded decision and coordinated registry update. Deleting an admitted record is prohibited; retired entities remain registered with status `retired` and an explanatory decision reference.

Allowed v0.1 lifecycle states are `planned`, `defined`, `active`, `deprecated`, `retired`, and `released`. A status transition requires evidence appropriate to the entity type and must preserve parent-child integrity.

## Ownership and hierarchy

Ownership follows the hierarchy defined in [`ARCHITECTURE.md`](ARCHITECTURE.md): User > Ultra Brain > Meta OS > OS Ecosystem > Capability > Project > Module. A child record cannot broaden the authority of its owner layer or contradict a parent rule, policy, standard, interface, or contract.

## Interface and contract references

Interface and contract arrays contain stable IDs, never free-form implementation descriptions. An entity may be registered without references in v0.1, but it cannot become executable solely because it appears in a registry. Publication, compatibility, and change rules are defined in [`interfaces/README.md`](interfaces/README.md) and [`contracts/README.md`](contracts/README.md).

## Change control

Registry changes must:

1. have a stated reason and accountable owner;
2. conform to [`schemas/registry.schema.json`](schemas/registry.schema.json);
3. preserve global ID uniqueness and valid parent references;
4. reference real repository paths where a local artifact is declared;
5. pass the foundation validator;
6. be reviewed as part of the same release that depends on them.

The registry is not a substitute for approval. New Meta OS creation is also subject to the Evolution Gate in [`EVOLUTION.md`](EVOLUTION.md).
