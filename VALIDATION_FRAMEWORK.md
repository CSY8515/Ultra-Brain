# Validation Framework

## Purpose

The Validation Framework defines how Ultra Brain demonstrates that a proposed
change conforms to its scope, architecture, governance, and release obligations.
Validation is evidence-based: an assertion without reproducible evidence is not
a passed check.

## Principles

- **Risk proportionality:** validation depth increases with impact and
  irreversibility.
- **Traceability:** every requirement maps to a check, result, and accountable
  decision.
- **Reproducibility:** another reviewer can repeat the check from recorded
  inputs and instructions.
- **Independence:** a release decision considers both implementation evidence
  and governance evidence.
- **Fail closed:** missing, stale, ambiguous, or contradictory mandatory
  evidence fails the affected gate.
- **Scope integrity:** passing technical checks does not legitimize work outside
  the approved milestone.

## Validation gates

| Gate | Required checks | Minimum evidence | Pass condition |
| --- | --- | --- | --- |
| V1 — Scope | Change matches the current milestone; prohibited paths and later capabilities are absent. | Reviewed change inventory, milestone mapping, and prohibited-scope scan. | Every changed item is authorized and every exclusion is satisfied. |
| V2 — Structure | Required files and directories exist; naming and references are coherent; no accidental nested repository exists. | File inventory, link/reference check, and repository-root check. | Required structure is complete and internally consistent. |
| V3 — Document | Normative language is unambiguous; terms, ownership, decisions, and boundaries agree across documents. | Document review record and consistency findings. | No unresolved blocking ambiguity or contradiction remains. |
| V4 — Data and schema | Structured files parse; declared schemas validate; identifiers, versions, and references are unique and resolvable. | Parser/schema output showing tool, input, and result. | All applicable structured artifacts pass with zero errors. |
| V5 — Architecture and governance | Architecture invariants, Constitution, Governance, Rules, Policies, and Standards are satisfied. | Traceability matrix or review record with decision references. | All mandatory controls pass and permitted exceptions are explicitly approved. |
| V6 — Safety and protection | Workspace boundaries, sensitive-data controls, reversibility, and non-destructive behavior are verified. | Path-scope review, secret scan, recovery/rollback evidence where applicable. | No unauthorized modification, credential exposure, or unresolved critical risk exists. |
| V7 — Test and quality | Applicable automated and manual checks pass at the required level. | Commands or procedures, environment, outputs, and result summary. | Required checks pass and residual findings are within approved thresholds. |
| V8 — Repository and release readiness | Correct root, branch, origin, clean intended diff, version, changelog, commit, tag, and release metadata are verified. | Git inspection output, diff review, version comparison, and release checklist. | Release inputs are complete, consistent, and point to the same reviewed revision. |

If a gate is not applicable, the evidence must state why, who accepted that
determination, and which governing rule permits it. “Not run” is not equivalent
to “not applicable.”

## Evidence record

Each validation record must contain:

1. evidence identifier and validation gate;
2. requirement or risk being checked;
3. exact artifact revision and relevant input paths;
4. procedure or command and tool version;
5. execution environment and timestamp in ISO 8601 form;
6. expected result and observed result;
7. pass, fail, blocked, or not-applicable status;
8. output, log, report, or review reference;
9. reviewer or accountable role; and
10. approved exception, remediation, and retest reference when relevant.

Evidence must be immutable or revision-addressed once used for a release. Secrets,
tokens, personal data, and machine-specific credentials must be redacted without
removing the information needed to reproduce the conclusion.

## Failure handling

1. Stop the affected promotion or release when a mandatory gate fails.
2. Record the finding, severity, affected requirements, and containment action.
3. Correct the artifact through the normal governed change process.
4. Repeat the failed gate and every downstream gate invalidated by the change.
5. Preserve both the failed and successful evidence for auditability.

No reviewer may convert a failed result into a pass by editing the output. Any
exception must be explicitly allowed, time-bounded, owned, risk-assessed, and
linked to its approval.

## v0.1 application

For v0.1, validation is limited to foundation artifacts. Required evidence
includes repository identity, file inventory, Markdown/reference review, JSON
parsing and schema validation for applicable structured files, prohibited-scope
review, diff review, and release metadata consistency. There are no runtime,
dependency, UI/UX, performance, or v0.2+ feature checks because those artifacts
must not exist in this milestone.
