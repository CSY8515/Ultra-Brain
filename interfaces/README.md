# Interfaces

## Purpose

This directory is reserved for governed interface definitions between Ultra
Brain components, external systems, and human-facing boundaries. Future entries
may specify message shapes, protocols, capability surfaces, compatibility rules,
and lifecycle status.

Every future interface must identify its owner, consumers, version, stability,
security boundary, governing contract, and validation method. Definitions must
be reviewed before an implementation depends on them.

## v0.1 boundary

This README is structural documentation only. v0.1 defines no executable API,
protocol adapter, SDK, network endpoint, user interface, dependency, or runtime
integration. Interface implementation belongs only to an approved later
milestone.

## v0.7 OS Ecosystem management interface

`os_ecosystem.interface.json` is the approved declarative boundary between
Ultra Brain and independent OS Ecosystem v0.73. It exchanges registry,
release-health, dependency, structural navigation, and evidence-linked advisory
report information only. It is not a network API, runtime adapter, UI, or
authority transfer.
