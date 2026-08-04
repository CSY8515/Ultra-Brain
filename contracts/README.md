# Contracts

## Purpose

This directory is reserved for explicit, versioned contracts that govern
interactions across Ultra Brain boundaries. Future contracts may define
preconditions, postconditions, invariants, data obligations, errors, permissions,
compatibility, ownership, and deprecation behavior.

A future contract must be traceable to architecture and governance, must name
its validating evidence, and must not grant authority beyond the applicable
policy. Contract changes require impact and compatibility review.

## v0.1 boundary

This README declares the contract namespace only. v0.1 contains no executable
contract, runtime enforcement, generated client, service integration, dependency,
or v0.2+ capability.

## v0.7 OS Ecosystem management contract

`os_ecosystem.contract.json` governs Ultra Brain's management of the independent
OS Ecosystem registration and operational-report flow. It preserves OS
Ecosystem, Living OS, and Universal Learning Engine ownership and requires
fail-closed, advisory-only handling with separate User approval for action.
