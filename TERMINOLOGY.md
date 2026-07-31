# Ultra Brain Terminology

## Purpose

These definitions are normative for v0.1 Foundation documents. A document that needs a different meaning MUST declare it and obtain approval through governance rather than silently overloading a term.

## Authority and organization

| Term | Definition |
| --- | --- |
| **User** | The highest decision authority for Ultra Brain. The User approves material scope, exceptions, architecture evolution, and releases when required. |
| **Ultra Brain** | The User's top-level operating and second-brain governance system that creates, governs, connects, validates, coordinates, optimizes, evolves, and archives subordinate systems. It is not itself a substitute implementation for every subordinate function. |
| **Layer** | A level of responsibility in the hierarchy: User, Ultra Brain, Meta OS, OS Ecosystem, Capability, Project, then Module. |
| **Owner layer** | The single layer accountable for an entity's scope, lifecycle, decisions, and boundary. Ownership does not imply permission to violate higher authority. |
| **Constitution** | The highest repository-level statement of enduring identity, principles, authority, and inviolable constraints, subordinate only to the User. |
| **Governance** | The system of roles, decision rights, review paths, escalation, accountability, and lifecycle control. |
| **Rule** | A mandatory constraint or required behavior. A rule answers what must or must not occur. |
| **Policy** | A repeatable control or decision approach used to satisfy rules. A policy answers how a class of situations is governed. |
| **Standard** | A measurable convention or minimum quality criterion used to demonstrate conformity. |

## Architecture and scope

| Term | Definition |
| --- | --- |
| **Meta OS** | A governed system domain that owns and coordinates a coherent class of responsibilities across lower-level ecosystems and capabilities. |
| **Core Meta OS** | One of the five planned Meta OS domains required for the v1.0 core: Safety, Enhancement, Automation, Collaboration & Connectivity, and Personal Secretary. Its v0.1 directory is a scope placeholder, not an implementation. |
| **OS Ecosystem** | A subordinate collection of related capabilities, projects, and modules coordinated within a defined operating domain. The pre-existing local `OS Ecosystem` project is protected external content, not part of this repository. |
| **Capability** | A reusable, bounded ability with an owner, explicit inputs and outputs, lifecycle state, and contract. |
| **Project** | A time- or outcome-bounded body of work that creates or changes governed artifacts. A project is not automatically a reusable capability. |
| **Module** | The smallest named implementation or documentation unit with a focused responsibility inside a project or capability. |
| **Core Axis** | One of Ultra Brain's cross-cutting concerns: Global Governance, Global Memory, Global Decision, Global Knowledge, Global Capability, or Global Ecosystem. In v0.1 these are architectural concepts, not runtime engines. |
| **Scope** | The explicit set of outcomes, versions, responsibilities, entities, and paths included in work, together with stated exclusions. |
| **Boundary** | The point at which ownership or responsibility changes and an interface or governance decision is required. |
| **Foundation** | The v0.1 governance, architecture, repository, registry, schema, validation, and release baseline. It excludes runtime and UI implementation. |

## Interaction and records

| Term | Definition |
| --- | --- |
| **Interface** | A versioned description of how one entity may interact with another, including the surface, inputs, outputs, and errors. |
| **Contract** | A versioned agreement defining the obligations, invariants, ownership, success, failure, compatibility, and validation conditions that govern an interface or relationship. |
| **Registry** | A machine-readable authoritative index of governed entities and their identity, ownership, scope, version, status, location, and references. A registry is not the entity itself. |
| **Schema** | A machine-readable definition of permitted structure, types, required fields, and constraints for data such as a registry record. |
| **Decision record** | An append-oriented record of an authoritative choice, its rationale, consequences, status, and related artifacts. |
| **Status** | A controlled lifecycle label that states an entity's actual condition, such as draft, approved, active, deprecated, or retired. Planned does not mean implemented. |

## Lifecycle and assurance

| Term | Definition |
| --- | --- |
| **Evolution Gate** | The mandatory sequence: need test → reuse an existing Meta OS? → reuse an existing Capability? → architecture review → User approval → development. |
| **Validation** | Reproducible evaluation of an artifact or state against explicit criteria. Validation provides evidence; it does not by itself authorize release. |
| **Release Gate** | The required set of scope, quality, safety, evidence, approval, repository, and publication checks that must pass before a release is declared complete. |
| **Release** | A named, immutable publication of a verified repository commit with a version tag, metadata, notes, and known limitations. |
| **Completion** | The evidence-backed satisfaction of every applicable acceptance criterion and gate at the artifact, change, or release level. |
| **Runtime** | Executable behavior that processes events or data. v0.1 defines no production runtime. |
| **UI/UX** | User-interface artifacts and the designed user experience. Their implementation begins only in the roadmap versions assigned to them, not in v0.1. |

## Repository terms

| Term | Definition |
| --- | --- |
| **Workspace** | The local directory opened for the current Ultra Brain work. It may contain protected local content that is not repository-owned. |
| **Repository root** | The top-level directory returned by Git for the canonical Ultra Brain repository; it is the workspace root, not a nested folder. |
| **Canonical origin** | `https://github.com/CSY8515/Ultra-Brain.git`, configured with remote name `origin`. |
| **Protected project** | A project that is outside Ultra Brain's authorized change scope, including `OS Ecosystem`, `Living OS`, and Universal Learning Engine (ULE). |

Normative requirement words (`MUST`, `SHOULD`, and `MAY`) have the meanings defined in [STANDARDS.md](STANDARDS.md).
