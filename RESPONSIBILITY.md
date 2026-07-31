# Ultra Brain Responsibility Model

## 1. Purpose

This document assigns accountability across the Ultra Brain hierarchy. It distinguishes governance authority from implementation responsibility so that the top-level Second Brain can maintain coherence without absorbing subordinate work.

It is subordinate to the [Constitution](CONSTITUTION.md) and complements [Governance](GOVERNANCE.md), [Architecture](ARCHITECTURE.md), and [Boundary](BOUNDARY.md).

## 2. Responsibility principles

1. Every governed entity and material artifact MUST have one accountable owner layer.
2. Work SHOULD be owned by the narrowest layer capable of fulfilling the outcome safely.
3. Authority MUST be delegated explicitly; access or technical ability does not imply responsibility.
4. Responsibility MAY be delegated, but accountability remains with the registered owner until ownership is formally transferred.
5. A layer MUST escalate needs outside its boundary and MUST NOT expand its own scope.
6. Cross-layer work MUST name provider, consumer, approver, executor, validator, and escalation path as applicable.
7. The same person MAY fulfill multiple logical roles, but the decision record MUST keep the roles and evidence distinct.

## 3. Layer responsibilities

### 3.1 User

The User MUST:

- define ultimate purpose and acceptable outcomes;
- approve constitutional and top-level architectural change;
- decide conflicts that exceed delegated authority;
- authorize creation of new Meta OSs and material boundary expansion; and
- accept or reject major release outcomes.

The User is not required to own each subordinate implementation decision. Delegation SHOULD remain sufficient for routine bounded work.

### 3.2 Ultra Brain

Ultra Brain MUST:

- maintain the global architecture, constitution, governance, and instrument coherence;
- preserve the six core axes and canonical hierarchy;
- maintain global registry, decision, validation, and release contracts;
- coordinate cross-Meta-OS concerns without taking over their implementations;
- surface unresolved conflicts, risks, and incomplete evidence to the User; and
- control evolution gates and global release readiness.

Ultra Brain MUST NOT implement a subordinate capability merely because it governs that capability.

### 3.3 Meta OS

A Meta OS MUST:

- govern one explicit major concern across its authorized ecosystems;
- define subordinate boundaries, contracts, and evidence requirements;
- coordinate its OS ecosystems and escalate cross-Meta-OS conflicts;
- conform to Ultra Brain instruments and global axes; and
- validate outcomes within its delegated scope.

A Meta OS MUST NOT redefine Ultra Brain's constitution, claim global ownership, or create another Meta OS without the evolution gate.

### 3.4 OS Ecosystem

An OS Ecosystem MUST:

- coordinate a coherent family of capabilities and projects;
- manage internal dependencies and integration boundaries;
- implement its Meta OS contract within delegated scope;
- expose health, outcomes, and exceptions upward; and
- keep unrelated ecosystems isolated.

An OS Ecosystem MUST NOT bypass its owning Meta OS or assume ownership of external workspace content.

### 3.5 Capability

A Capability MUST:

- provide one bounded, named outcome;
- declare consumers, owner, interface, contract, status, and fitness criteria;
- remain implementation-neutral at the governance layer; and
- use projects for time-bounded delivery changes.

A Capability MUST NOT grant itself governance authority or silently become an ecosystem.

### 3.6 Project

A Project MUST:

- deliver an approved, time-bounded result for one or more capabilities;
- declare scope, owner, dependencies, completion criteria, and handoff;
- preserve architectural and repository boundaries; and
- close, transfer, or archive its outputs explicitly.

A Project MUST NOT treat temporary delivery structure as permanent architecture without approval.

### 3.7 Module

A Module MUST:

- implement one cohesive technical responsibility;
- conform to its project's design and capability contract;
- expose only its declared interface;
- remain replaceable within its compatibility obligations; and
- produce the evidence required by its owning project.

A Module MUST NOT override project, capability, ecosystem, Meta OS, or Ultra Brain decisions.

## 4. Responsibility assignment contract

Every material assignment MUST identify:

- entity or artifact ID and type;
- accountable owner layer;
- responsible executor or maintainer, when applicable;
- approving authority;
- consumers and consulted layers;
- parent and dependency relationships;
- scope and explicit exclusions;
- interfaces and contracts;
- validation obligations;
- escalation route; and
- effective version and status.

Missing ownership blocks activation. Multiple collaborators MAY contribute, but shared accountability without one final owner is invalid.

## 5. Foundation artifact accountability

| Artifact class | Accountable layer | Required approval or assurance |
| --- | --- | --- |
| Constitution and canonical hierarchy | User | Explicit approval and constitutional change record |
| MASTER design and global architecture | Ultra Brain, under User authority | Architecture review and six-axis impact validation |
| Rules, policies, and standards | Layer that owns their declared scope | Conformance to higher instruments and correct delegated approval |
| Global registries and schemas | Ultra Brain | Structural validation and agreement with actual state |
| Meta OS scope | Relevant Meta OS under Ultra Brain | User approval for creation; no implementation before assigned version |
| Ecosystem, capability, project, and module artifacts | Their registered owner layer | Parent contract, boundary, and validation evidence |
| Releases | Releasing owner layer | [Release Framework](RELEASE_FRAMEWORK.md) and applicable User approval |

## 6. Cross-boundary responsibility

For every cross-boundary exchange:

- the **provider** owns correctness of the declared output;
- the **consumer** owns valid use within its own scope;
- the **contract owner** owns compatibility and escalation terms;
- the **approver** owns authorization of the bounded exchange; and
- the **validator** owns an evidence-based conformance result, not the business outcome itself.

Failure in one role MUST NOT be hidden by transferring blame to another role. An interface does not transfer ownership unless an approved governance decision explicitly does so.

## 7. Escalation

A layer MUST escalate when it encounters ambiguous authority, a higher-instrument conflict, unowned scope, cross-axis systemic impact, failed mandatory validation, or a requested action outside its boundary.

Escalation proceeds to the parent layer, then upward as needed. Matters involving constitutional identity, new Meta OS creation, global boundary change, or undelegated risk terminate at the User.

## 8. Transfer and retirement

Ownership transfer or retirement MUST be approved before registry state changes. The record MUST identify prior and new owners, affected contracts, continuity obligations, migration or archival action, validation, effective version, and unresolved liabilities.

No entity becomes unowned merely because its project ends or implementation is removed.

## 9. v0.1 boundary

At v0.1, responsibility assignments are documentary governance contracts only. They do not create automated actors, runtime delegation, user-interface roles, or implementations for v0.2 and later Core Meta OS capabilities. The five Core Meta OS owners and scopes MAY be identified for architectural continuity, but execution authority begins only in the version that separately approves, validates, and releases the relevant implementation.
