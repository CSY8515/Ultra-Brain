# Ultra Brain Roadmap

## Purpose

This roadmap fixes the milestone sequence from the v0.1 Foundation through the
v1.0 Core Stable release. A milestone may refine its internal design, but it may
not silently absorb the implementation scope of a later milestone.

## Current milestone

v0.3 Enhancement is the current release milestone. The v0.1 Foundation and v0.2
Safety controls remain cumulative; v0.4 and later capability milestones remain
future scope.

## Milestone sequence

| Version | Milestone | Committed outcome | Explicit boundary |
| --- | --- | --- | --- |
| v0.1 | Foundation | Establish the constitution, governance, rules, policies, standards, MASTER Architecture, registry structure, validation and release frameworks, repository strategy, workspace protection, and scope declarations for the five Core Meta OS domains. | Documentation, schemas, registries, and structural baselines only; no runtime, UI/UX, dependencies, or v0.2+ feature code. |
| v0.2 | Safety | Define and implement the approved Safety Core Meta OS baseline, including enforceable trust, risk, permission, audit, and recovery controls. | Enhancement, automation, collaboration/connectivity, and secretary capabilities remain out of scope. |
| v0.3 | Enhancement | Add the approved Enhancement Core Meta OS baseline for governed assistance and capability augmentation. | Does not implement autonomous workflow execution or later-domain capabilities. |
| v0.4 | Automation | Add the approved Automation Core Meta OS baseline for controlled, observable, and recoverable workflows. | Does not implement the later collaboration/connectivity or secretary milestones. |
| v0.5 | Collaboration & Connectivity | Add the approved Collaboration & Connectivity Core Meta OS baseline for governed interaction among people, agents, services, and systems. | Personal Secretary capabilities and official product UI/UX remain out of scope. |
| v0.6 | Personal Secretary | Add the approved Personal Secretary Core Meta OS baseline for consent-aware personal coordination and assistance. | World/IA/UI architecture and official UI/UX remain later milestones. |
| v0.7 | World / IA / UI architecture and design-system baseline | Define the product world model, information architecture, UI architecture, and design-system baseline. | No claim of official end-to-end UI/UX completion. |
| v0.8 | Navigation, dashboard, governance, and registry UX | Implement and validate the primary navigation, dashboard, governance, and registry experiences on the v0.7 baseline. | Final accessibility, integration, and official UI/UX readiness remain v0.9 work. |
| v0.9 | Official UI/UX, accessibility, and integration | Complete the official UI/UX baseline, accessibility verification, and integrated system validation. | Core Stable status is not granted until v1.0 gates pass. |
| v1.0 | Core Stable | Stabilize the integrated core, close release-critical findings, publish support and compatibility commitments, and satisfy all Core Stable release gates. | New capability families are excluded from stabilization scope. |

## Milestone rules

1. Every milestone must satisfy the Constitution, Governance, Rules, Policies,
   Standards, Validation Framework, and Release Framework then in force.
2. Safety constraints are cumulative. A later milestone cannot weaken an
   earlier safety or governance decision without an approved, traceable change.
3. Entry into a milestone requires acceptance criteria, accountable ownership,
   dependencies, risks, and validation evidence to be recorded.
4. Exit requires all mandatory gates to pass or an explicitly governed
   exception that is permitted by the Constitution. A deferred mandatory gate
   is not a passed gate.
5. Version labels describe verified outcomes, not target dates or aspirations.

## Post-v1.0 candidate horizon

Capabilities for v1.1 through v2.0 are candidates only. Their content, order,
architecture, and release allocation will be decided exclusively through a
post-v1.0 architecture review using operational evidence from Core Stable.
Nothing in the current repository commits those versions to a feature, date,
compatibility promise, or implementation approach.
