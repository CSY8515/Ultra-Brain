# Personal Secretary Core Meta OS

Personal Secretary Core Meta OS is the consent-aware, person-directed assistance
plane introduced by Ultra Brain v0.6. It prepares daily briefings, weekly and
monthly reviews, reminder views, recommendations, priority plans, decision
support, assistance plans, context retrieval, and scheduling proposals from
bounded caller-supplied records.

The reference implementation is local, deterministic, dependency-free, and
non-executing. It does not read calendars, messages, files, contacts, or accounts;
store a profile or memory; send reminders; book time; contact people; invoke
Automation or Connectivity; or make decisions for the user.

## Authority boundary

Every operation requires a current approved `SecretaryGrant` with a Safety
decision reference, explicit operation and context-category allowlists, and item
and time-horizon limits. Sensitive context requires a separate grant flag. All
recommendations cite caller-provided evidence. Priority and option rankings are
advisory; the person remains the decision and action authority.

## Package

The `personal_secretary_core` package exposes immutable records and
`PersonalSecretaryCore`. See [Requirements](REQUIREMENTS.md), [Architecture
Review](ARCHITECTURE_REVIEW.md), and [MASTER Design](MASTER_DESIGN.md) for the
governed v0.6 contract.

Run validation from this directory:

```text
python validation/validate_personal_secretary_core.py
```

## Explicit exclusions

No UI/UX, dashboard UI, Streamlit, deployment, background scheduler, autonomous
agent, personal-data persistence, provider SDK, network or filesystem I/O, Core
Capability, OS Ecosystem, Living OS, ULE, or Ultra Brain-exclusive capability is
implemented.
