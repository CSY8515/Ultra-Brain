export const THEME_STORAGE_KEY = "ultra-brain.ui/v1";

const shared = {
  surface: "rgba(6,15,16,.76)",
  surfaceStrong: "rgba(9,22,22,.94)",
  text: "#f1ede2",
  textSoft: "#aeb9af",
  border: "rgba(195,167,96,.34)",
  worldFilter: "brightness(.78) saturate(.82)",
  font: 'Pretendard, "Noto Sans KR", "Malgun Gothic", sans-serif',
  radius: "4px",
  shadow: "0 28px 90px rgba(0,0,0,.46)",
  texture: "radial-gradient(circle at 50% 42%, rgba(255,255,255,.03), transparent 46%)",
  lighting: "rgba(240,213,138,.16)",
  contrast: "1",
};

export const themeRegistry = Object.freeze({
  official: { ...shared, id: "ultra-brain-official", label: "Official", mode: "dark", accent: "#c8a55d", accentBright: "#f0d58a", description: "Antique gold / world-first", worldFilter: "brightness(.78) saturate(.82)", lighting: "rgba(240,213,138,.16)" },
  light: { ...shared, id: "ultra-brain-light", label: "Light", mode: "light", accent: "#7a5b25", accentBright: "#a47a2f", description: "Warm paper daylight", surface: "rgba(239,235,216,.84)", surfaceStrong: "rgba(246,243,226,.97)", text: "#20251f", textSoft: "#566057", border: "rgba(92,75,40,.32)", worldFilter: "brightness(1.16) saturate(.55) sepia(.28)", texture: "linear-gradient(145deg, rgba(255,255,255,.36), transparent 55%)", lighting: "rgba(164,122,47,.12)", contrast: ".94" },
  dark: { ...shared, id: "ultra-brain-dark", label: "Dark", mode: "dark", accent: "#83aa8c", accentBright: "#bcd3af", description: "Deep green / quiet focus", surface: "rgba(5,13,16,.82)", surfaceStrong: "rgba(8,19,23,.96)", text: "#eef2ed", textSoft: "#9eaaa5", border: "rgba(128,169,146,.3)", worldFilter: "brightness(.58) saturate(.58) hue-rotate(8deg)", lighting: "rgba(188,211,175,.1)" },
  universe: { ...shared, id: "ultra-brain-universe", label: "Universe", mode: "dark", accent: "#9d91e8", accentBright: "#d5ceff", description: "Indigo orbit / deep space", surface: "rgba(8,8,27,.8)", surfaceStrong: "rgba(14,12,39,.95)", text: "#f0efff", textSoft: "#aaa8c7", border: "rgba(157,145,232,.35)", worldFilter: "brightness(.64) saturate(.8) hue-rotate(22deg)", lighting: "rgba(157,145,232,.16)", radius: "7px" },
  galaxy: { ...shared, id: "ultra-brain-galaxy", label: "Galaxy", mode: "dark", accent: "#df86b8", accentBright: "#ffc7e5", description: "Rose nebula / luminous", surface: "rgba(24,8,25,.8)", surfaceStrong: "rgba(35,10,33,.95)", text: "#fff0f8", textSoft: "#c9a7bc", border: "rgba(223,134,184,.34)", worldFilter: "brightness(.74) saturate(1.05) hue-rotate(316deg)", lighting: "rgba(255,199,229,.16)", radius: "9px" },
  ecosystem: { ...shared, id: "ultra-brain-ecosystem", label: "Ecosystem", mode: "dark", accent: "#79b67b", accentBright: "#c4e6af", description: "Living canopy / healthy", surface: "rgba(5,19,12,.8)", surfaceStrong: "rgba(8,28,17,.95)", text: "#eff8e9", textSoft: "#a8c3aa", border: "rgba(121,182,123,.34)", worldFilter: "brightness(.76) saturate(1.14) hue-rotate(20deg)", lighting: "rgba(196,230,175,.16)", radius: "6px" },
  ocean: { ...shared, id: "ultra-brain-ocean", label: "Ocean", mode: "dark", accent: "#56b8cf", accentBright: "#b8f0fa", description: "Tide blue / clear depth", surface: "rgba(3,16,24,.82)", surfaceStrong: "rgba(4,25,36,.96)", text: "#edfaff", textSoft: "#9bc1cc", border: "rgba(86,184,207,.34)", worldFilter: "brightness(.7) saturate(.86) hue-rotate(168deg)", lighting: "rgba(184,240,250,.16)", radius: "5px" },
  grassland: { ...shared, id: "ultra-brain-grassland", label: "Grassland", mode: "light", accent: "#668744", accentBright: "#a9ce72", description: "Sunlit field / open", surface: "rgba(226,232,197,.82)", surfaceStrong: "rgba(243,246,222,.96)", text: "#26321f", textSoft: "#66735b", border: "rgba(102,135,68,.32)", worldFilter: "brightness(1.14) saturate(.78) hue-rotate(34deg)", lighting: "rgba(169,206,114,.18)", radius: "10px" },
  lava: { ...shared, id: "ultra-brain-lava", label: "Lava", mode: "dark", accent: "#e87943", accentBright: "#ffc08e", description: "Molten core / high energy", surface: "rgba(28,8,5,.82)", surfaceStrong: "rgba(43,12,7,.96)", text: "#fff1e7", textSoft: "#d2a897", border: "rgba(232,121,67,.38)", worldFilter: "brightness(.82) saturate(1.26) sepia(.12) hue-rotate(332deg)", lighting: "rgba(255,192,142,.18)", radius: "3px" },
  minimal: { ...shared, id: "ultra-brain-minimal", label: "Minimal", mode: "dark", accent: "#d2d7d0", accentBright: "#ffffff", description: "Neutral / signal first", surface: "rgba(14,17,17,.78)", surfaceStrong: "rgba(22,26,25,.96)", text: "#f5f7f3", textSoft: "#a7afaa", border: "rgba(210,215,208,.25)", worldFilter: "brightness(.68) saturate(.18)", lighting: "rgba(255,255,255,.1)", radius: "2px", shadow: "0 18px 42px rgba(0,0,0,.32)" },
  paper: { ...shared, id: "ultra-brain-paper", label: "Paper", mode: "light", accent: "#8b5e34", accentBright: "#bd8550", description: "Archive paper / tactile", surface: "rgba(246,240,222,.88)", surfaceStrong: "rgba(255,252,242,.98)", text: "#33281e", textSoft: "#756454", border: "rgba(139,94,52,.3)", worldFilter: "brightness(1.17) saturate(.38) sepia(.42)", texture: "repeating-linear-gradient(0deg, rgba(139,94,52,.025) 0 1px, transparent 1px 4px)", lighting: "rgba(189,133,80,.12)", radius: "1px" },
  archive: { ...shared, id: "ultra-brain-archive", label: "Archive", mode: "dark", accent: "#b49b78", accentBright: "#e6d7b8", description: "Bronze record / measured", surface: "rgba(22,17,12,.82)", surfaceStrong: "rgba(31,24,17,.96)", text: "#f2e9da", textSoft: "#b7a994", border: "rgba(180,155,120,.34)", worldFilter: "brightness(.66) saturate(.54) sepia(.25)", lighting: "rgba(230,215,184,.14)", radius: "2px" },
});

export const themeNames = Object.freeze(Object.keys(themeRegistry));

export const defaultPreference = Object.freeze({
  theme: "official",
  accent: "#c8a55d",
  density: "comfortable",
  motion: true,
  osEcosystemLocked: false,
  propagationOverride: false,
  scope: "global",
  revision: 1,
});

export function validatePreference(input = {}) {
  const theme = Object.hasOwn(themeRegistry, input.theme) ? input.theme : "official";
  const fallbackAccent = themeRegistry[theme].accent;
  const accent = /^#[0-9a-f]{6}$/i.test(input.accent || "") ? input.accent : fallbackAccent;
  return {
    ...defaultPreference,
    ...input,
    theme,
    accent,
    density: ["compact", "comfortable", "spacious"].includes(input.density) ? input.density : "comfortable",
    motion: input.motion !== false,
    osEcosystemLocked: input.osEcosystemLocked === true,
    propagationOverride: input.propagationOverride === true,
    scope: input.scope === "os-ecosystem" ? "os-ecosystem" : "global",
    revision: Number.isInteger(input.revision) && input.revision > 0 ? input.revision : 1,
  };
}

export function resolveThemeProfile(preference) {
  const safe = validatePreference(preference);
  const profile = themeRegistry[safe.theme] || themeRegistry.official;
  const blocked = safe.scope === "global" && safe.osEcosystemLocked && !safe.propagationOverride;
  return {
    ...profile,
    accent: safe.accent,
    accentBright: safe.accent,
    density: safe.density,
    motion: safe.motion,
    effectiveMode: profile.mode,
    propagation: {
      source: "Ultra Brain Global UI",
      target: "OS Ecosystem",
      status: blocked ? "locked" : safe.propagationOverride ? "override" : "compatible",
      contract: "ultra-brain.ui/v1",
      interfaceVersion: "1.0",
    },
  };
}

export function createRollbackPoint(current) {
  return { id: `ui-r${current.revision}-${Date.now()}`, createdAt: new Date().toISOString(), preference: validatePreference(current) };
}

export function applyPreference(current, candidate) {
  const safeCurrent = validatePreference(current);
  const rollback = createRollbackPoint(safeCurrent);
  const next = validatePreference({ ...candidate, revision: safeCurrent.revision + 1 });
  return { next, rollback };
}
