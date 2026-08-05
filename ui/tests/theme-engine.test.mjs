import test from "node:test";
import assert from "node:assert/strict";
import { applyPreference, defaultPreference, resolveThemeProfile, validatePreference } from "../lib/theme-engine.js";

test("invalid preferences fall back to the official profile", () => {
  const safe = validatePreference({ theme: "unknown", accent: "javascript:bad", density: "tiny" });
  assert.equal(safe.theme, "official");
  assert.equal(safe.accent, "#c8a55d");
  assert.equal(safe.density, "comfortable");
});

test("OS Ecosystem lock blocks global propagation", () => {
  const profile = resolveThemeProfile({ ...defaultPreference, osEcosystemLocked: true });
  assert.equal(profile.propagation.status, "locked");
  assert.equal(profile.propagation.contract, "ultra-brain.ui/v1");
});

test("save creates a rollback point and increments revision", () => {
  const result = applyPreference(defaultPreference, { ...defaultPreference, theme: "dark" });
  assert.equal(result.rollback.preference.theme, "official");
  assert.equal(result.next.theme, "dark");
  assert.equal(result.next.revision, 2);
});
