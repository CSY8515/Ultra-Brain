import test from "node:test";
import assert from "node:assert/strict";
import { applyPreference, applyThemePreset, defaultPreference, HIERARCHY, PROPAGATION_TARGETS, resolvePropagation, resolveThemeProfile, THEME_ADJUSTMENT_KEYS, UI_LOCK_KEYS, themeNames, themePackageRegistry, themePresets, themeRegistry, validatePreference } from "../lib/theme-engine.js";

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

test("official theme studio exposes the complete v0.93 registry", () => {
  assert.equal(themeNames.length, 12);
  assert.deepEqual(themeNames, ["official", "light", "dark", "universe", "galaxy", "ecosystem", "ocean", "grassland", "lava", "minimal", "paper", "archive"]);
  for (const name of themeNames) {
    assert.ok(themeRegistry[name].accent);
    assert.ok(themeRegistry[name].description);
    assert.ok(themeRegistry[name].worldFilter);
  }
});

test("UI lock settings are normalised and preserved", () => {
  const safe = validatePreference({ ...defaultPreference, uiLocks: { layout: true, color: true, unknown: true } });
  assert.equal(safe.uiLocks.layout, true);
  assert.equal(safe.uiLocks.color, true);
  assert.equal(Object.hasOwn(safe.uiLocks, "unknown"), false);
});

test("v0.95 exposes independent position, size, component, and layer locks", () => {
  assert.deepEqual(UI_LOCK_KEYS, ["position", "size", "background", "layout", "color", "texture", "lighting", "component", "layer"]);
  const safe = validatePreference({ ...defaultPreference, uiLocks: { position: true, size: true, component: true, layer: true } });
  assert.equal(safe.uiLocks.position, true);
  assert.equal(safe.uiLocks.size, true);
  assert.equal(safe.uiLocks.component, true);
  assert.equal(safe.uiLocks.layer, true);
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

test("official theme packages expose detail controls and import/export readiness", () => {
  assert.equal(THEME_ADJUSTMENT_KEYS.length, 10);
  for (const name of themeNames) {
    const themePackage = themePackageRegistry[name];
    assert.equal(themePackage.exportReady, true);
    assert.equal(themePackage.importReady, true);
    assert.deepEqual(themePackage.adjustmentKeys, THEME_ADJUSTMENT_KEYS);
  }
});

test("theme presets resolve bounded visual adjustments without changing world identity", () => {
  const luminous = applyThemePreset(defaultPreference, "luminous");
  assert.equal(luminous.theme, "official");
  assert.equal(luminous.themePreset, "luminous");
  assert.equal(luminous.themeAdjustments.glow, themePresets.luminous.adjustments.glow);
  assert.equal(luminous.themeAdjustments.blur, 0);
  const safe = validatePreference({ ...defaultPreference, themeAdjustments: { brightness: 99, hue: -99, blur: 99 } });
  assert.equal(safe.themeAdjustments.brightness, 1.3);
  assert.equal(safe.themeAdjustments.hue, -30);
  assert.equal(safe.themeAdjustments.blur, 8);
});

test("resolved theme profile carries package, preset, and adjustment payload", () => {
  const profile = resolveThemeProfile({ ...defaultPreference, theme: "universe", themePreset: "cinematic" });
  assert.equal(profile.package.id, "ultra-brain-theme-universe");
  assert.equal(profile.themePreset, "cinematic");
  assert.equal(profile.adjustments.contrast, themePresets.cinematic.adjustments.contrast);
});

test("official themes resolve a complete visual world engine", () => {
  for (const name of themeNames) {
    const profile = resolveThemeProfile({ ...defaultPreference, theme: name });
    assert.ok(profile.worldEngine.label);
    assert.ok(profile.worldEngine.background);
    assert.ok(profile.worldEngine.overlay);
    assert.ok(profile.worldEngine.texture);
    assert.ok(profile.worldEngine.motion);
    assert.equal(profile.package.world.id, profile.worldEngine.id);
  }
});

test("v0.96 theme packages retain concept art and builder metadata", () => {
  for (const name of themeNames) {
    const themePackage = themePackageRegistry[name];
    assert.equal(themePackage.worldAsset.source, "/ultra-brain-world.png");
    assert.ok(themePackage.layoutPreset);
    assert.ok(themePackage.componentSkin);
    assert.deepEqual(themePackage.responsive, ["desktop", "tablet", "mobile"]);
    assert.equal(themePackage.revisionPolicy, "every-save");
    assert.equal(themePackage.states.length, 9);
  }
});
