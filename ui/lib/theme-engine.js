export const THEME_STORAGE_KEY = "ultra-brain.ui/v1";

export const themeRegistry = Object.freeze({
  official: { id: "ultra-brain-official", mode: "dark", accent: "#c8a55d", accentBright: "#f0d58a", surface: "rgba(6,15,16,.72)", surfaceStrong: "rgba(9,22,22,.92)", text: "#f1ede2", textSoft: "#aeb9af", border: "rgba(195,167,96,.34)", worldFilter: "brightness(.72) saturate(.78)" },
  dark: { id: "ultra-brain-dark", mode: "dark", accent: "#83aa8c", accentBright: "#bcd3af", surface: "rgba(5,13,16,.78)", surfaceStrong: "rgba(8,19,23,.94)", text: "#eef2ed", textSoft: "#9eaaa5", border: "rgba(128,169,146,.3)", worldFilter: "brightness(.58) saturate(.58) hue-rotate(8deg)" },
  light: { id: "ultra-brain-light", mode: "light", accent: "#7a5b25", accentBright: "#a47a2f", surface: "rgba(239,235,216,.82)", surfaceStrong: "rgba(246,243,226,.95)", text: "#20251f", textSoft: "#566057", border: "rgba(92,75,40,.32)", worldFilter: "brightness(1.16) saturate(.55) sepia(.28)" },
});

export const defaultPreference = Object.freeze({ theme: "official", accent: "#c8a55d", density: "comfortable", motion: true, osEcosystemLocked: false, scope: "global", revision: 1 });

export function validatePreference(input = {}) {
  const theme = Object.hasOwn(themeRegistry, input.theme) ? input.theme : "official";
  const accent = /^#[0-9a-f]{6}$/i.test(input.accent || "") ? input.accent : themeRegistry[theme].accent;
  return { ...defaultPreference, ...input, theme, accent, density: ["compact", "comfortable", "spacious"].includes(input.density) ? input.density : "comfortable", motion: input.motion !== false, osEcosystemLocked: input.osEcosystemLocked === true, scope: input.scope === "os-ecosystem" ? "os-ecosystem" : "global", revision: Number.isInteger(input.revision) && input.revision > 0 ? input.revision : 1 };
}

export function resolveThemeProfile(preference) {
  const safe = validatePreference(preference);
  const profile = themeRegistry[safe.theme] || themeRegistry.official;
  const blocked = safe.scope === "global" && safe.osEcosystemLocked;
  return { ...profile, accent: safe.accent, accentBright: safe.accent, density: safe.density, motion: safe.motion, effectiveMode: profile.mode, propagation: { source: "Ultra Brain Global UI", target: "OS Ecosystem", status: blocked ? "locked" : "compatible", contract: "ultra-brain.ui/v1", interfaceVersion: "1.0" } };
}

export function createRollbackPoint(current) {
  return { id: `ui-r${current.revision}-${Date.now()}`, createdAt: new Date().toISOString(), preference: validatePreference(current) };
}

export function applyPreference(current, candidate) {
  const rollback = createRollbackPoint(current);
  const next = validatePreference({ ...candidate, revision: current.revision + 1 });
  return { next, rollback };
}
