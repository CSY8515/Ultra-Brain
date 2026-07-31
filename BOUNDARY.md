# Ultra Brain Boundary

## 1. Purpose

This document defines what Ultra Brain governs, what v0.1 contains, what remains external, and how authority or information may cross a boundary. Boundaries prevent top-level governance from becoming unrestricted implementation ownership.

This contract must be read with [Architecture](ARCHITECTURE.md), [Responsibility](RESPONSIBILITY.md), and [Workspace Protection](WORKSPACE_PROTECTION.md).

## 2. System boundary

Ultra Brain includes the governance artifacts and registered relationships required to coordinate the hierarchy below the User:

> **Ultra Brain > Meta OS > OS Ecosystem > Capability > Project > Module**

The User is above the system boundary and remains its source of authority. A subordinate entity is inside the governed boundary only when the User or a validly delegated authority has approved its scope and it has an owner, parent, status, interface expectations, contract obligations, and registry identity.

Visibility, filesystem access, a shared repository, a hyperlink, or a dependency alone MUST NOT place an entity inside the boundary.

## 3. v0.1 included scope

v0.1 includes only:

- mission, vision, identity, principles, hierarchy, responsibilities, and boundaries;
- constitution, governance, rules, policies, and standards;
- MASTER design and structural architecture;
- six core-axis definitions;
- decision-flow, governance-loop, and evolution contracts;
- registry architecture, initial registries, and schemas;
- interface and contract principles;
- validation, testing scope, completion, and release frameworks;
- repository strategy, workspace protection, terminology, roadmap, version, changelog, and decision log; and
- five Core Meta OS directories containing scope README files only.

These are architecture and assurance artifacts. Their presence does not claim runtime capability.

## 4. v0.1 excluded scope

v0.1 MUST NOT include:

- implementation of Safety, Enhancement, Automation, Collaboration & Connectivity, or Personal Secretary capabilities;
- a decision engine, rule engine, memory service, knowledge service, analytics engine, scheduler, agent, or background process;
- UI/UX, pages, components, styles, dashboards, navigation, or a design-system implementation;
- API, external AI, credential, connector, synchronization, database, deployment, or production integration;
- user secrets, tokens, keys, private personal data, or generated credentials;
- speculative Ultra Brain-exclusive capability implementation;
- copied source or structure from Living OS, Universal Learning Engine, OS Ecosystem, or another project; or
- a nested clone, nested Git repository, or second Ultra-Brain root.

Roadmap descriptions of excluded items are non-executable future intent.

## 5. Protected external scope

The following remain external and protected unless the User separately authorizes a bounded adoption or integration decision:

- Living OS;
- Universal Learning Engine;
- any OS Ecosystem implementation or workspace content;
- other local projects and repositories;
- external accounts, services, and data; and
- paths outside the verified Ultra Brain repository root.

External content MUST NOT be edited, copied, moved, deleted, registered as owned, committed, or released as part of v0.1. A future interface MAY reference an external system without transferring ownership.

## 6. Layer boundaries

| Boundary | Permitted crossing | Prohibited crossing |
| --- | --- | --- |
| User ↔ Ultra Brain | Intent, approval, evidence, outcome, escalation | Inferred unlimited consent or concealed tradeoff |
| Ultra Brain ↔ Meta OS | Delegated scope, global constraints, contracts, validation evidence | Ultra Brain taking over implementation or Meta OS redefining global authority |
| Meta OS ↔ OS Ecosystem | Domain governance, required outcomes, risk and health evidence | Ecosystem bypass of owning Meta OS |
| OS Ecosystem ↔ Capability | Capability contract, dependencies, fitness evidence | Undeclared capability or ecosystem-wide authority claim |
| Capability ↔ Project | Approved change scope, acceptance criteria, handoff | Project scope becoming permanent architecture implicitly |
| Project ↔ Module | Technical contract, implementation and test evidence | Module overriding project or higher-layer decisions |

Every crossing MUST use the narrowest data, action, and authority required.

## 7. Interface boundary contract

Before a boundary is crossed, the interface and contract MUST identify:

1. parties, layers, owners, and purpose;
2. authorized direction and scope;
3. allowed inputs, outputs, and data classification;
4. applicable rules, policies, and standards;
5. validation, compatibility, and version conditions;
6. refusal, failure, timeout, and escalation semantics;
7. evidence and retention requirements; and
8. termination or revocation conditions.

No contract MAY authorize a party beyond its own delegated authority. Absence of a prohibition is not permission to cross a boundary.

## 8. Repository boundary

The Git root for Ultra Brain MUST be the repository root itself. Foundation files and approved root-level directories MAY be versioned there. A nested `Ultra-Brain` folder or nested `.git` directory MUST NOT be created.

Repository actions MUST target only the verified origin and branch defined by [Repository Strategy](REPOSITORY_STRATEGY.md). Untracked external workspace content MUST be treated as protected until its ownership and intended disposition are explicitly resolved; it MUST NOT be swept into a broad commit.

## 9. Version boundary

Version labels are capability boundaries:

- v0.1 authorizes foundation artifacts only;
- v0.2–v0.6 each authorize their named Core Meta OS only after the preceding release completes;
- v0.7–v0.9 reserve world and UI/UX work;
- v1.0 requires integrated stable evidence; and
- v1.1–v2.0 feature allocation remains undecided pending post-v1.0 review.

A future-version folder or roadmap line MUST NOT be interpreted as authority to implement that version.

## 10. Boundary change test

A proposal changes the boundary if it adds an owner, entity class, top-level directory, external system, data category, execution authority, repository, or capability not already approved.

Every boundary change MUST:

- follow [Governance](GOVERNANCE.md);
- identify the current and proposed boundary;
- assess all hierarchy layers and six axes;
- define ownership, interface, contract, validation, containment, and exit;
- pass the evolution gate when a Meta OS or major capability is involved; and
- receive explicit User approval when top-level or external scope changes.
