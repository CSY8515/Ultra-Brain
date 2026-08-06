import test from "node:test";
import assert from "node:assert/strict";
import { applyPreference, defaultPreference, resolveThemeProfile, themeNames, themeRegistry, validatePreference } from "../lib/theme-engine.js";

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

test("official theme studio exposes the complete v0.9 registry", () => {
  assert.equal(themeNames.length, 12);
  assert.deepEqual(themeNames, ["official", "light", "dark", "universe", "galaxy", "ecosystem", "ocean", "grassland", "lava", "minimal", "paper", "archive"]);
  for (const name of themeNames) {
    assert.ok(themeRegistry[name].accent);
    assert.ok(themeRegistry[name].description);
    assert.ok(themeRegistry[name].worldFilter);
  }
});

test("propagation override is explicit and visible in the resolved profile", () => {
  const profile = resolveThemeProfile({ ...defaultPreference, osEcosystemLocked: true, propagationOverride: true });
  assert.equal(profile.propagation.status, "override");
});
