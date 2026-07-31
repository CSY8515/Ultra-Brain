# Ultra Brain Completion Rule

## Principle

Completion is an evidence-backed state, not an estimate or a declaration. Work MUST NOT be called complete while a required artifact, approval, check, publication step, or known blocker remains unresolved.

## Completion levels

Completion MUST be reported at the correct level:

1. **Artifact complete** — the artifact meets its acceptance criteria and applicable standards.
2. **Change complete** — all scoped artifacts are complete, integrated, reviewed, and validated in the repository.
3. **Release complete** — the change is committed, pushed to the verified canonical branch, tagged, and published as the intended release with matching evidence.

A lower level MUST NOT be reported as a higher one. “Implemented,” “validated,” “pushed,” and “released” each require separate evidence.

## Universal completion criteria

A change is complete only when:

- the target version, scope, non-goals, and acceptance criteria are explicit;
- every required artifact exists and contains substantive, internally consistent content;
- names, versions, ownership, paths, interfaces, contracts, registries, and decisions agree;
- all applicable mandatory requirements in [RULES.md](RULES.md), [POLICIES.md](POLICIES.md), and [STANDARDS.md](STANDARDS.md) are satisfied;
- all applicable validation checks pass and their limitations are recorded;
- the final diff contains no protected, unrelated, sensitive, or accidental change;
- required architecture review and User approval are recorded;
- known issues, residual risks, and deferred work are stated accurately.

## v0.1 Foundation definition of done

The v0.1 Foundation change additionally requires:

- the v0.1–v1.0 roadmap and MASTER Architecture are documented;
- Constitution, governance, rules, policies, standards, responsibilities, boundaries, core axes, decision flow, governance loop, evolution, and terminology are established;
- repository, workspace, development, validation, completion, and release frameworks are established;
- registry and schema structures exist, all JSON parses and validates, IDs are unique, and local paths match the repository;
- interface and contract principles are documented;
- all five Core Meta OS top-level directories contain scope-only README files;
- no v0.2+ function, runtime, UI/UX, integration, database, or deployment implementation is present;
- Markdown links, required-file presence, repository identity, branch, origin, Git status, and diff are verified.

## Release completion

Release completion requires a successful commit with the intended message, a successful non-force push to `origin/main`, a tag matching the release plan, and a non-prerelease GitHub release whose title and notes match the delivered contents. The tag MUST resolve to the reported commit.

For the v0.1 Foundation, the intended tag is `v0.1` and the release title is `Ultra Brain v0.1 Foundation`.

## Failure and partial completion

A mandatory failed or skipped check blocks completion unless the User has approved and recorded a narrowly scoped exception. If publication fails after validation, the change MAY be reported as validated but MUST be reported as not released.

The final report MUST contain actual results for workspace, Git root, origin, branch, files created, validation, commit hash, push, release tag, release URL, and known issues. Unknown or unperformed results MUST be labeled as such; they MUST NOT be inferred.
