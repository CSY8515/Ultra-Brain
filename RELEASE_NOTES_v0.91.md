# Ultra Brain v0.91 Hierarchy Propagation Final

## Scope

v0.91 completes the governed UI propagation layer on the existing v0.9 Official
UI/UX foundation. Ultra Brain UI Studio remains the single editing surface.

## Included

- Seven-level hierarchy: Ultra Brain, OS Ecosystem, Living OS, Universal Learning Engine, Project, Module, and Feature.
- Eighteen propagation targets covering theme, visual tokens, layout, component geometry, visibility, and animation.
- Automatic application for every unlocked descendant.
- Target-level Lock to preserve a descendant's current UI and target-level Override for explicit exceptions.
- Propagation preview payload with revision and applied, locked, and overridden counts.
- Child editor disabled state with ownership retained by Ultra Brain UI Studio.
- Production redeployment and worker-log validation with no runtime errors observed.

## Compatibility

No Living OS, Universal Learning Engine, OS Ecosystem, Project, Module, or Feature
source was changed. Propagation remains a presentation contract and does not
transfer repository, runtime, or ownership authority.

## Validation

- Vinext production build passed.
- UI regression suite passed: 11 tests.
- Foundation validator passed.
- Root Python regression suite passed: 10 tests.
- Production deployment succeeded; browser verification is sign-in gated by the private site access policy.

## Release

Tag: `v0.91`
