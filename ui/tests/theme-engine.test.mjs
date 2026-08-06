import test from "node:test";
import assert from "node:assert/strict";
import { applyPreference, defaultPreference, HIERARCHY, PROPAGATION_TARGETS, resolvePropagation, resolveThemeProfile, themeNames, themeRegistry, validatePreference } from "../lib/theme-engine.js";

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

test("hierarchy propagation covers every governed level and target", () => {
  const propagation = resolvePropagation(defaultPreference);
  assert.deepEqual(propagation.hierarchy.map((node) => node.label), HIERARCHY.map((node) => node.label));
  assert.equal(propagation.targets.length, 18);
  assert.deepEqual(propagation.targets, PROPAGATION_TARGETS);
  assert.equal(propagation.childEditorsEnabled, false);
  assert.equal(propagation.owner, "Ultra Brain UI Studio");
});

test("unlocked descendants automatically receive the UI payload", () => {
  const propagation = resolvePropagation(defaultPreference);
  const feature = propagation.hierarchy.find((node) => node.id === "feature");
  assert.equal(feature.status, "applied");
  assert.equal(feature.automatic, true);
  assert.equal(feature.appliedTargets.length, PROPAGATION_TARGETS.length);
  assert.equal(feature.editableHere, false);
});

test("target-level lock preserves a descendant target", () => {
  const preference = validatePreference({ ...defaultPreference, propagationLocks: { "living-os": ["background", "layout"] } });
  const livingOs = resolvePropagation(preference).hierarchy.find((node) => node.id === "living-os");
  assert.equal(livingOs.status, "applied");
  assert.deepEqual(livingOs.lockedTargets, ["background", "layout"]);
  assert.equal(livingOs.appliedTargets.includes("background"), false);
  assert.equal(livingOs.appliedTargets.includes("layout"), false);
});

test("target-level override is explicit at the selected hierarchy level", () => {
  const preference = validatePreference({ ...defaultPreference, propagationOverrides: { module: ["animation"] } });
  const moduleNode = resolvePropagation(preference).hierarchy.find((node) => node.id === "module");
  assert.equal(moduleNode.status, "override");
  assert.deepEqual(moduleNode.overriddenTargets, ["animation"]);
  assert.equal(moduleNode.appliedTargets.includes("animation"), false);
});
