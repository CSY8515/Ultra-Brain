# Release Framework

## Purpose

The Release Framework governs how a reviewed Ultra Brain revision becomes an
official, traceable release. A release is a verified snapshot with accountable
evidence, not merely a tag or uploaded archive.

## Release flow

1. **Plan** — confirm milestone scope, owners, acceptance criteria, dependencies,
   and risks.
2. **Prepare** — freeze the intended change set; align version, changelog,
   roadmap, and release notes.
3. **Validate** — execute every applicable gate in `VALIDATION_FRAMEWORK.md` and
   resolve or govern all findings.
4. **Approve** — record release readiness and accountable approval against the
   exact commit candidate.
5. **Publish** — commit, push without rewriting protected history, create the
   specified immutable tag, and publish the release from that tag.
6. **Verify** — confirm remote branch, tag target, release title, release notes,
   assets, and public availability; record the resulting URLs and identifiers.

## Mandatory release gates

| Gate | Evidence required | Pass condition |
| --- | --- | --- |
| R1 — Scope freeze | Final changed-file inventory and milestone mapping. | Only approved milestone work is present. |
| R2 — Validation | Complete evidence summary for V1–V8, including justified non-applicability. | All mandatory validation gates pass and no release-blocking finding remains. |
| R3 — Version coherence | `VERSION`, changelog entry, roadmap milestone, tag, title, and release notes comparison. | Every version reference identifies the intended milestone; any prescribed tag format is followed exactly. |
| R4 — Repository integrity | Repository root, branch, origin, status, reviewed diff, and commit identity. | Release is built from the correct repository and intended commit with no unreviewed change. |
| R5 — Approval | Accountable release decision linked to the exact commit and evidence set. | Approval is present, current, and within authority. |
| R6 — Publication | Push output, remote commit, tag target, release URL, and release metadata. | Remote objects match the approved commit and release specification. |
| R7 — Post-release verification | Independent retrieval or inspection of branch, tag, notes, and referenced artifacts. | The published release is accessible, coherent, and reproducible. |

## Evidence rules

- Evidence must identify the commit SHA it supports.
- Generated reports must record procedure, timestamp, environment, result, and
  responsible role.
- Release notes must summarize scope, validation status, known issues, and
  compatibility or migration impact.
- Failed attempts and approved exceptions remain linked to the release record.
- Credentials and secrets must never appear in logs, notes, commits, or assets.
- A tag must not be moved after publication. Corrections require a governed new
  release rather than history rewriting or force-pushing.

## Version and tag policy

`VERSION` contains the canonical milestone number without a `v` prefix. Git tags
prefix that exact value with `v`. The v0.1 milestone therefore uses `VERSION`
value `0.1` and tag `v0.1`. Later changes to the versioning scheme require a
governed standards decision and must preserve existing tag meanings.

## v0.1 release definition

The v0.1 release is a formal Foundation release, not a prerelease. Its title is
`Ultra Brain v0.1 Foundation`, and its release notes must include:

- Ultra Brain Foundation established
- Constitution and Governance baseline
- Rules, Policies, and Standards baseline
- MASTER Architecture
- Registry Architecture
- Validation Framework
- Release Framework
- Repository Strategy
- Workspace Protection
- v0.1 to v1.0 roadmap
- Five Core Meta OS scopes initialized

Before v0.1 publication, evidence must show that foundation documents and
applicable JSON artifacts validate, the five scope directories contain no
implementation, the intended diff has been reviewed, and the exact release
commit is present on the configured `main` branch and `origin`.

## Rollback and correction

If publication verification fails, stop further promotion and record the release
as affected. Do not delete or retarget a published tag to conceal the issue.
Contain impact, correct through a new reviewed commit, repeat invalidated gates,
and publish the governed corrective release or advisory. Repository recovery
must follow workspace protection and governance requirements.
