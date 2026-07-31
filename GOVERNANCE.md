# Ultra Brain Governance

## 1. Purpose

This document defines how Ultra Brain exercises authority, makes decisions, manages exceptions, and changes governed artifacts. It operates under the [Constitution](CONSTITUTION.md) and applies across the hierarchy defined in [Architecture](ARCHITECTURE.md).

Governance is a control contract. v0.1 does not implement a governance engine, automated approval, or workflow service.

## 2. Governance principles

Governance MUST be:

- **user-sovereign:** authority ultimately derives from the User;
- **scope-bound:** each decision applies only to its declared entities and versions;
- **proportionate:** review depth follows impact and reversibility;
- **traceable:** evidence, rationale, approval, and outcome remain linked;
- **separated:** proposal, approval, execution, and validation are distinct responsibilities even when one person performs more than one role;
- **contract-driven:** cross-boundary action requires explicit obligations;
- **interruptible:** ambiguity, conflict, or failed validation can stop progression; and
- **evolutionary:** evaluation may produce controlled improvement, not silent mutation.

## 3. Governance participants

| Participant | Governance responsibility | Reserved authority |
| --- | --- | --- |
| User | Defines intent, accepts material tradeoffs, and gives final approval | Constitution, hierarchy, top-level boundary, new Meta OSs, major releases, and exceptions that exceed delegated authority |
| Ultra Brain | Maintains global coherence and prepares cross-system decisions | May govern only within ratified instruments and explicit User delegation |
| Owner layer | Accounts for an entity, artifact, or outcome | May decide within its registered boundary and delegated authority |
| Proposer | Frames a change and supplies evidence | Cannot approve merely by proposing |
| Reviewer | Tests consistency, impact, and alternatives | Cannot expand the proposal's scope silently |
| Executor | Performs an approved action | Cannot reinterpret approval to grant additional authority |
| Validator | Tests the result against declared criteria | Cannot waive failed mandatory criteria without an approved exception |

These are logical responsibilities, not staffing requirements. A single User MAY perform several responsibilities, but each responsibility and its evidence MUST remain explicit.

## 4. Decision classes

| Class | Examples | Minimum approval |
| --- | --- | --- |
| Constitutional | Identity, hierarchy, core axes, instrument precedence | Explicit User approval and constitutional amendment process |
| Architectural | System boundary, new Meta OS, repository topology, cross-layer contract model | User approval after architecture and six-axis impact review |
| Normative | New or changed rule, policy, or standard | Authority designated by the applicable higher-order instrument; User if no valid delegation exists |
| Registry | Entity creation, status, ownership, parent, or version update | Registered owner plus validation; higher approval when the underlying relationship changes |
| Release | Version completion, tag, publication, or rollback | Release authority defined by [Release Framework](RELEASE_FRAMEWORK.md); v0.1 requires User authorization |
| Local | Reversible implementation choice within one delegated boundary | Owner layer, subject to all higher instruments and contracts |

When classification is uncertain, the decision MUST be treated as the higher-impact class until resolved.

## 5. Governance lifecycle

Every material change MUST pass these states:

1. **Proposed** — scope, owner, need, evidence, and desired outcome are recorded.
2. **Reviewed** — affected layers, axes, instruments, alternatives, risks, and compatibility are assessed.
3. **Approved or Rejected** — the authorized participant records a decision and rationale.
4. **Planned** — approved execution, validation, containment, and recovery conditions are explicit.
5. **Executed** — the responsible layer performs only the approved action.
6. **Validated** — independent criteria determine conformance.
7. **Active, Superseded, Retired, or Reverted** — resulting state and relationships are recorded.
8. **Evaluated** — outcomes and lessons feed the governance loop.

Skipping a state requires a recorded exception. An urgent stop action MAY precede full review when needed to contain harm; resumption still requires ordinary approval and validation.

## 6. Decision record contract

A material governance decision MUST record at least:

- stable decision identity and title;
- status, scope, owner layer, and affected entities;
- initiating event or proposal;
- evidence and knowledge references;
- options, constraints, risks, and impact across the six axes;
- selected decision and rationale;
- approving authority and approval date;
- resulting rules, policies, standards, contracts, or registry updates;
- execution owner and authorization boundary;
- validation and evaluation criteria;
- effective version and supersession links.

The machine-readable representation, when used, is governed by [Registry Architecture](REGISTRY.md) and its schemas. The human-readable history belongs in [Decision Log](DECISION_LOG.md).

## 7. Conflict resolution

When instruments or layers conflict:

1. stop the affected decision, execution, or release;
2. identify the exact scopes and versions in conflict;
3. apply the precedence in the [Constitution](CONSTITUTION.md);
4. prefer the narrower applicable instruction only when it conforms to higher authority;
5. escalate to the nearest layer authorized to resolve the conflict;
6. escalate to the User when the conflict affects constitutional, architectural, or undelegated authority;
7. record the resolution and update every inconsistent artifact; and
8. re-run affected validation before resuming.

Silence, file recency, implementation convenience, and successful execution MUST NOT be used as conflict-resolution authority.

## 8. Exception governance

An exception is temporary permission to depart from a rule, policy, standard, or ordinary process. It MUST include:

- the exact requirement and scope affected;
- necessity and considered alternatives;
- approving authority;
- risks, compensating controls, and prohibited uses;
- start and expiry or review condition;
- validation and restoration plan; and
- a decision-log reference.

An exception MUST NOT override the User, amend the Constitution, authorize an unrelated repository change, permit secrets in the repository, or become permanent through repeated renewal. Constitutional change follows Article XII of the [Constitution](CONSTITUTION.md).

## 9. Change impact review

Before approval, a material proposal MUST answer:

1. Which hierarchy layers and registered entities are affected?
2. Which of the six core axes is primary, and what are the effects on the other five?
3. Which constitution, rule, policy, standard, interface, or contract applies?
4. Does the proposal cross a boundary or change ownership?
5. Is the need already satisfied by an existing Meta OS, ecosystem, or capability?
6. What evidence supports the proposal and what remains uncertain?
7. What is reversible, and how will failure be contained?
8. What validation establishes completion and what evaluation tests value?
9. Which version owns implementation, and is that version currently authorized?

## 10. Governance cadence

Individual decisions follow [Decision Flow](DECISION_FLOW.md). Recurring review follows [Governance Loop](GOVERNANCE_LOOP.md). A release review MUST also follow [Release Framework](RELEASE_FRAMEWORK.md).

Cadence does not authorize automatic action. Until a later version explicitly implements and approves automation, every lifecycle stage is satisfied through reviewed artifacts and explicit human authority.

## 11. Governance assurance

A governance change is conformant only when:

- decision classification and approval authority are correct;
- affected documents and registry entries agree;
- scope did not expand during execution;
- mandatory validation passed;
- exceptions are explicit and time-bounded;
- no protected workspace or unrelated project changed; and
- the outcome and next review condition are recorded.
