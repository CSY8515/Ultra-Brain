export const THEME_STORAGE_KEY = "ultra-brain.ui/v1";

export const PROPAGATION_TARGETS = Object.freeze([
  "theme",
  "background",
  "color",
  "brightness",
  "contrast",
  "saturation",
  "hue",
  "texture",
  "lighting",
  "shadow",
  "glow",
  "transparency",
  "blur",
  "layout",
  "componentPosition",
  "componentSize",
  "visibility",
  "animation",
]);

export const HIERARCHY = Object.freeze([
  { id: "ultra-brain", label: "Ultra Brain", kind: "source" },
  { id: "os-ecosystem", label: "OS Ecosystem", kind: "registered-child" },
  { id: "living-os", label: "Living OS", kind: "downstream" },
  { id: "universal-learning-engine", label: "Universal Learning Engine", kind: "downstream" },
  { id: "project", label: "Project", kind: "downstream" },
  { id: "module", label: "Module", kind: "downstream" },
  { id: "feature", label: "Feature", kind: "downstream" },
]);

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

export const THEME_ADJUSTMENT_KEYS = Object.freeze(["brightness", "contrast", "saturation", "hue", "lighting", "shadow", "glow", "texture", "blur", "transparency"]);
export const UI_LOCK_KEYS = Object.freeze(["position", "size", "background", "layout", "color", "texture", "lighting", "component", "layer"]);
export const defaultLocks = Object.freeze(Object.fromEntries(UI_LOCK_KEYS.map((key) => [key, false])));
export const THEME_ADJUSTMENT_RANGES = Object.freeze({
  brightness: { min: 0.7, max: 1.3, step: 0.01, unit: "x" },
  contrast: { min: 0.7, max: 1.4, step: 0.01, unit: "x" },
  saturation: { min: 0.5, max: 1.5, step: 0.01, unit: "x" },
  hue: { min: -30, max: 30, step: 1, unit: "°" },
  lighting: { min: 0, max: 1.5, step: 0.01, unit: "x" },
  shadow: { min: 0.4, max: 1.6, step: 0.01, unit: "x" },
  glow: { min: 0, max: 1.8, step: 0.01, unit: "x" },
  texture: { min: 0, max: 1.5, step: 0.01, unit: "x" },
  blur: { min: 0, max: 8, step: 1, unit: "px" },
  transparency: { min: 0.45, max: 1, step: 0.01, unit: "x" },
});

const balancedAdjustments = Object.freeze({ brightness: 1, contrast: 1, saturation: 1, hue: 0, lighting: 1, shadow: 1, glow: 1, texture: 1, blur: 0, transparency: 1 });
export const themePresets = Object.freeze({
  balanced: { id: "balanced", label: "균형", description: "테마 기본값", adjustments: { ...balancedAdjustments } },
  luminous: { id: "luminous", label: "발광", description: "밝기와 빛을 강조", adjustments: { ...balancedAdjustments, brightness: 1.08, lighting: 1.3, glow: 1.45, shadow: 0.82 } },
  cinematic: { id: "cinematic", label: "시네마틱", description: "깊은 명암과 질감", adjustments: { ...balancedAdjustments, brightness: 0.92, contrast: 1.18, saturation: 1.08, lighting: 1.12, shadow: 1.3, texture: 1.2 } },
  quiet: { id: "quiet", label: "차분", description: "부드러운 초점과 안정감", adjustments: { ...balancedAdjustments, brightness: 0.96, contrast: 0.9, saturation: 0.82, lighting: 0.86, glow: 0.65, blur: 1, transparency: 0.9 } },
  custom: { id: "custom", label: "사용자 지정", description: "상세 값을 직접 조정", adjustments: { ...balancedAdjustments } },
});

export const themePackageRegistry = Object.freeze(Object.fromEntries(Object.entries(themeRegistry).map(([name, item]) => [name, {
  id: `ultra-brain-theme-${name}`,
  version: "1.0",
  name: item.label,
  category: name === "official" || name === "light" || name === "dark" ? "foundation" : "official",
  worldStyle: item.description,
  mode: item.mode,
  palette: { accent: item.accent, accentBright: item.accentBright, surface: item.surface, border: item.border },
  detail: { background: item.surfaceStrong, font: item.font, radius: item.radius, texture: item.texture, lighting: item.lighting, shadow: item.shadow, contrast: item.contrast },
  adjustmentKeys: [...THEME_ADJUSTMENT_KEYS],
  exportReady: true,
  importReady: true,
}])));

export const themeNames = Object.freeze(Object.keys(themeRegistry));

export const defaultPreference = Object.freeze({
  theme: "official",
  accent: "#c8a55d",
  density: "comfortable",
  motion: true,
  osEcosystemLocked: false,
  propagationOverride: false,
  themePreset: "balanced",
  themeAdjustments: { ...balancedAdjustments },
  uiLocks: { ...defaultLocks },
  propagationTargets: [...PROPAGATION_TARGETS],
  propagationLocks: {},
  propagationOverrides: {},
  scope: "global",
  revision: 1,
});

function normaliseTargets(value) {
  if (!Array.isArray(value)) return [...PROPAGATION_TARGETS];
  const targets = value.filter((target) => PROPAGATION_TARGETS.includes(target));
  return targets.length ? [...new Set(targets)] : [...PROPAGATION_TARGETS];
}

function normaliseThemeAdjustments(value) {
  const source = value && typeof value === "object" && !Array.isArray(value) ? value : {};
  return Object.fromEntries(THEME_ADJUSTMENT_KEYS.map((key) => {
    const range = THEME_ADJUSTMENT_RANGES[key];
    const candidate = Number(source[key]);
    const fallback = balancedAdjustments[key];
    const next = Number.isFinite(candidate) ? candidate : fallback;
    return [key, Math.min(range.max, Math.max(range.min, next))];
  }));
}

function normaliseNodeMap(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return {};
  return Object.fromEntries(Object.entries(value).flatMap(([nodeId, targets]) => {
    if (!HIERARCHY.some((node) => node.id === nodeId) || !Array.isArray(targets)) return [];
    return [[nodeId, [...new Set(targets.filter((target) => PROPAGATION_TARGETS.includes(target)))]]];
  }));
}

function normaliseLocks(value) {
  const source = value && typeof value === "object" && !Array.isArray(value) ? value : {};
  return Object.fromEntries(UI_LOCK_KEYS.map((key) => [key, source[key] === true]));
}

export function validatePreference(input = {}) {
  const theme = Object.hasOwn(themeRegistry, input.theme) ? input.theme : "official";
  const fallbackAccent = themeRegistry[theme].accent;
  const accent = /^#[0-9a-f]{6}$/i.test(input.accent || "") ? input.accent : fallbackAccent;
  const propagationTargets = normaliseTargets(input.propagationTargets);
  const propagationLocks = normaliseNodeMap(input.propagationLocks);
  const propagationOverrides = normaliseNodeMap(input.propagationOverrides);
  const uiLocks = normaliseLocks(input.uiLocks);
  if (input.osEcosystemLocked === true) {
    propagationLocks["os-ecosystem"] = [...propagationTargets];
  }
  if (input.propagationOverride === true) {
    propagationOverrides["os-ecosystem"] = [...propagationTargets];
  }
  const themePreset = Object.hasOwn(themePresets, input.themePreset) ? input.themePreset : "balanced";
  const requestedAdjustments = normaliseThemeAdjustments(input.themeAdjustments);
  const shouldUsePresetAdjustments = themePreset !== "custom" && THEME_ADJUSTMENT_KEYS.every((key) => requestedAdjustments[key] === balancedAdjustments[key]);
  return {
    ...defaultPreference,
    ...input,
    theme,
    accent,
    density: ["compact", "comfortable", "spacious"].includes(input.density) ? input.density : "comfortable",
    motion: input.motion !== false,
    osEcosystemLocked: input.osEcosystemLocked === true,
    propagationOverride: input.propagationOverride === true,
    themePreset,
    themeAdjustments: shouldUsePresetAdjustments ? { ...themePresets[themePreset].adjustments } : requestedAdjustments,
    uiLocks,
    propagationTargets,
    propagationLocks,
    propagationOverrides,
    scope: input.scope === "os-ecosystem" ? "os-ecosystem" : "global",
    revision: Number.isInteger(input.revision) && input.revision > 0 ? input.revision : 1,
  };
}

export function applyThemePreset(preference, preset = "balanced") {
  const safe = validatePreference(preference);
  const selected = themePresets[preset] || themePresets.balanced;
  return validatePreference({ ...safe, themePreset: selected.id, themeAdjustments: selected.adjustments });
}

export function resolvePropagation(preference) {
  const safe = validatePreference(preference);
  const sourcePayload = {
    revision: safe.revision,
    theme: safe.theme,
    accent: safe.accent,
    density: safe.density,
    motion: safe.motion,
    themePreset: safe.themePreset,
    adjustments: safe.themeAdjustments,
    package: themePackageRegistry[safe.theme] || themePackageRegistry.official,
    targets: [...safe.propagationTargets],
  };
  const hierarchy = HIERARCHY.map((node) => {
    if (node.kind === "source") {
      return {
        ...node,
        status: "source",
        automatic: false,
        owner: "Ultra Brain UI Studio",
        editableHere: true,
        sourceRevision: safe.revision,
        appliedTargets: [...safe.propagationTargets],
        lockedTargets: [],
        overriddenTargets: [],
        preservedTargets: [],
      };
    }
    const lockedTargets = (safe.propagationLocks[node.id] || []).filter((target) => safe.propagationTargets.includes(target));
    const overriddenTargets = (safe.propagationOverrides[node.id] || []).filter((target) => safe.propagationTargets.includes(target));
    const appliedTargets = safe.propagationTargets.filter((target) => !lockedTargets.includes(target) && !overriddenTargets.includes(target));
    const status = overriddenTargets.length ? "override" : lockedTargets.length === safe.propagationTargets.length ? "locked" : "applied";
    return {
      ...node,
      status,
      automatic: appliedTargets.length > 0,
      owner: "Ultra Brain UI Studio",
      editableHere: false,
      sourceRevision: safe.revision,
      appliedTargets,
      lockedTargets,
      overriddenTargets,
      preservedTargets: [...lockedTargets],
    };
  });
  return {
    source: "Ultra Brain",
    owner: "Ultra Brain UI Studio",
    contract: "ultra-brain.ui/v1",
    interfaceVersion: "1.0",
    revision: safe.revision,
    automatic: true,
    childEditorsEnabled: false,
    targets: [...safe.propagationTargets],
    payload: sourcePayload,
    hierarchy,
  };
}

export function resolveThemeProfile(preference) {
  const safe = validatePreference(preference);
  const profile = themeRegistry[safe.theme] || themeRegistry.official;
  const propagation = resolvePropagation(safe);
  const ecosystemNode = propagation.hierarchy.find((node) => node.id === "os-ecosystem");
  return {
    ...profile,
    accent: safe.accent,
    accentBright: safe.accent,
    density: safe.density,
    motion: safe.motion,
    themePreset: safe.themePreset,
    adjustments: safe.themeAdjustments,
    package: themePackageRegistry[safe.theme] || themePackageRegistry.official,
    effectiveMode: profile.mode,
    propagation: {
      source: "Ultra Brain Global UI",
      target: "OS Ecosystem",
      status: ecosystemNode?.status === "locked" ? "locked" : ecosystemNode?.status === "override" ? "override" : "compatible",
      ...propagation,
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
