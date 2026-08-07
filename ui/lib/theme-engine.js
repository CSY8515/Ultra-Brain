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
  official: { ...shared, id: "ultra-brain-official", label: "Official", mode: "dark", accent: "#c8a55d", accentBright: "#f0d58a", description: "우주를 품은 생태계 · 태양 중심", worldFilter: "brightness(.78) saturate(.82)", lighting: "rgba(240,213,138,.16)" },
  light: { ...shared, id: "ultra-brain-light", label: "Light", mode: "light", accent: "#7a5b25", accentBright: "#a47a2f", description: "따뜻한 햇빛 · 밝은 세계", surface: "rgba(239,235,216,.84)", surfaceStrong: "rgba(246,243,226,.97)", text: "#20251f", textSoft: "#566057", border: "rgba(92,75,40,.32)", worldFilter: "brightness(1.03) saturate(.92)", texture: "linear-gradient(145deg, rgba(255,255,255,.36), transparent 55%)", lighting: "rgba(164,122,47,.12)", contrast: ".94" },
  dark: { ...shared, id: "ultra-brain-dark", label: "Dark", mode: "dark", accent: "#83aa8c", accentBright: "#bcd3af", description: "고요한 심야 · 집중의 세계", surface: "rgba(5,13,16,.82)", surfaceStrong: "rgba(8,19,23,.96)", text: "#eef2ed", textSoft: "#9eaaa5", border: "rgba(128,169,146,.3)", worldFilter: "brightness(.72) saturate(.72)", lighting: "rgba(188,211,175,.1)" },
  universe: { ...shared, id: "ultra-brain-universe", label: "Universe", mode: "dark", accent: "#9d91e8", accentBright: "#d5ceff", description: "암흑 물질 신경망 · 심우주", surface: "rgba(8,8,27,.8)", surfaceStrong: "rgba(14,12,39,.95)", text: "#f0efff", textSoft: "#aaa8c7", border: "rgba(157,145,232,.35)", worldFilter: "brightness(.78) saturate(.95)", lighting: "rgba(157,145,232,.16)", radius: "7px" },
  galaxy: { ...shared, id: "ultra-brain-galaxy", label: "Galaxy", mode: "dark", accent: "#df86b8", accentBright: "#ffc7e5", description: "장미빛 성운 지능 · 은하", surface: "rgba(24,8,25,.8)", surfaceStrong: "rgba(35,10,33,.95)", text: "#fff0f8", textSoft: "#c9a7bc", border: "rgba(223,134,184,.34)", worldFilter: "brightness(.82) saturate(1.05)", lighting: "rgba(255,199,229,.16)", radius: "9px" },
  ecosystem: { ...shared, id: "ultra-brain-ecosystem", label: "Ecosystem", mode: "dark", accent: "#79b67b", accentBright: "#c4e6af", description: "다층 생명 군락 · 생태계", surface: "rgba(5,19,12,.8)", surfaceStrong: "rgba(8,28,17,.95)", text: "#eff8e9", textSoft: "#a8c3aa", border: "rgba(121,182,123,.34)", worldFilter: "brightness(.82) saturate(1.05)", lighting: "rgba(196,230,175,.16)", radius: "6px" },
  ocean: { ...shared, id: "ultra-brain-ocean", label: "Ocean", mode: "dark", accent: "#56b8cf", accentBright: "#b8f0fa", description: "산호 신경망 · 심해 생태계", surface: "rgba(3,16,24,.82)", surfaceStrong: "rgba(4,25,36,.96)", text: "#edfaff", textSoft: "#9bc1cc", border: "rgba(86,184,207,.34)", worldFilter: "brightness(.78) saturate(1.05)", lighting: "rgba(184,240,250,.16)", radius: "5px" },
  grassland: { ...shared, id: "ultra-brain-grassland", label: "Grassland", mode: "light", accent: "#668744", accentBright: "#a9ce72", description: "꽃가루 신경망 · 열린 초원", surface: "rgba(226,232,197,.82)", surfaceStrong: "rgba(243,246,222,.96)", text: "#26321f", textSoft: "#66735b", border: "rgba(102,135,68,.32)", worldFilter: "brightness(1) saturate(.95)", lighting: "rgba(169,206,114,.18)", radius: "10px" },
  lava: { ...shared, id: "ultra-brain-lava", label: "Lava", mode: "dark", accent: "#e87943", accentBright: "#ffc08e", description: "마그마 신경핵 · 화산 세계", surface: "rgba(28,8,5,.82)", surfaceStrong: "rgba(43,12,7,.96)", text: "#fff1e7", textSoft: "#d2a897", border: "rgba(232,121,67,.38)", worldFilter: "brightness(.88) saturate(1.12)", lighting: "rgba(255,192,142,.18)", radius: "3px" },
  minimal: { ...shared, id: "ultra-brain-minimal", label: "Minimal", mode: "dark", accent: "#d2d7d0", accentBright: "#ffffff", description: "핵심 연결만 남긴 절제된 세계", surface: "rgba(14,17,17,.78)", surfaceStrong: "rgba(22,26,25,.96)", text: "#f5f7f3", textSoft: "#a7afaa", border: "rgba(210,215,208,.25)", worldFilter: "brightness(.68) saturate(.18)", lighting: "rgba(255,255,255,.1)", radius: "2px", shadow: "0 18px 42px rgba(0,0,0,.32)" },
  paper: { ...shared, id: "ultra-brain-paper", label: "Paper", mode: "light", accent: "#8b5e34", accentBright: "#bd8550", description: "종이 구조물 · 손으로 만든 기록 세계", surface: "rgba(246,240,222,.88)", surfaceStrong: "rgba(255,252,242,.98)", text: "#33281e", textSoft: "#756454", border: "rgba(139,94,52,.3)", worldFilter: "brightness(1) saturate(.7)", texture: "repeating-linear-gradient(0deg, rgba(139,94,52,.025) 0 1px, transparent 1px 4px)", lighting: "rgba(189,133,80,.12)", radius: "1px" },
  archive: { ...shared, id: "ultra-brain-archive", label: "Archive", mode: "dark", accent: "#b49b78", accentBright: "#e6d7b8", description: "지식 보관 장치 · 기록 세계", surface: "rgba(22,17,12,.82)", surfaceStrong: "rgba(31,24,17,.96)", text: "#f2e9da", textSoft: "#b7a994", border: "rgba(180,155,120,.34)", worldFilter: "brightness(.78) saturate(.75)", lighting: "rgba(230,215,184,.14)", radius: "2px" },
  calm: { ...shared, id: "ultra-brain-calm", label: "Calm", mode: "light", accent: "#547b8c", accentBright: "#365f72", description: "고요한 새벽 · 안개 습지 · 물방울 생태계", surface: "rgba(218,228,232,.86)", surfaceStrong: "rgba(238,243,244,.97)", text: "#17262e", textSoft: "#435c67", border: "rgba(62,94,108,.45)", worldFilter: "brightness(1) contrast(.92) saturate(.86)", texture: "radial-gradient(ellipse at 50% 70%, rgba(255,255,255,.16), transparent 58%)", lighting: "rgba(207,225,232,.12)", radius: "8px", shadow: "0 20px 60px rgba(44,67,77,.2)", contrast: ".92" },
});

// A theme owns a visual world, not just a palette.  The existing concept art is
// the source image for every official world; these layers reinterpret it with
// world-specific atmosphere, texture, lighting, layout language and motion.
export const themeWorldRegistry = Object.freeze({
  official: { id: "sun-world", label: "태양 중심 세계", description: "중앙 태양과 생명의 나무를 기준으로 한 기본 세계", layout: "solar", motion: "orbit", background: "radial-gradient(circle at 50% 44%, rgba(255,183,65,.2), transparent 22%), linear-gradient(180deg, rgba(3,8,12,.22), rgba(36,18,5,.35))", overlay: "radial-gradient(circle at 50% 43%, rgba(255,191,81,.18), transparent 26%), radial-gradient(circle at 50% 100%, rgba(91,57,17,.34), transparent 58%)", texture: "radial-gradient(circle at 50% 40%, rgba(255,224,145,.16) 0 1px, transparent 2px), repeating-radial-gradient(circle at 50% 43%, transparent 0 22px, rgba(232,183,88,.035) 23px 24px)", lighting: "rgba(255,203,108,.24)", assetLabel: "공식 태양 컨셉아트" },
  light: { id: "paper-daylight-world", label: "따뜻한 낮의 세계", description: "컨셉아트를 따뜻한 종이광과 낮의 시야로 재해석", layout: "editorial", motion: "paper-drift", background: "linear-gradient(180deg, rgba(255,252,238,.7), rgba(207,184,129,.26)), radial-gradient(circle at 50% 35%, rgba(255,255,255,.55), transparent 42%)", overlay: "linear-gradient(145deg, rgba(255,248,215,.34), transparent 56%)", texture: "repeating-linear-gradient(0deg, rgba(128,93,47,.06) 0 1px, transparent 1px 4px)", lighting: "rgba(255,240,184,.3)", assetLabel: "낮빛 컨셉아트" },
  dark: { id: "quiet-canopy-world", label: "고요한 숲의 세계", description: "컨셉아트의 숲과 우주를 깊은 녹색 정적 속에 배치", layout: "canopy", motion: "nebula", background: "radial-gradient(circle at 50% 42%, rgba(74,126,91,.16), transparent 34%), linear-gradient(180deg, rgba(1,7,8,.54), rgba(3,20,14,.42))", overlay: "radial-gradient(ellipse at 50% 0%, rgba(96,145,102,.12), transparent 56%)", texture: "radial-gradient(circle at 15% 25%, rgba(150,190,133,.11) 0 1px, transparent 2px), radial-gradient(circle at 82% 67%, rgba(150,190,133,.1) 0 1px, transparent 2px)", lighting: "rgba(137,184,145,.15)", assetLabel: "고요한 숲 컨셉아트" },
  universe: { id: "indigo-orbit-world", label: "인디고 궤도 세계", description: "행성·궤도·별빛을 강조한 깊은 우주 세계", layout: "cosmic", motion: "orbit", background: "radial-gradient(circle at 50% 42%, rgba(109,95,226,.28), transparent 26%), radial-gradient(circle at 15% 18%, rgba(75,128,235,.15), transparent 25%), #05051a", overlay: "repeating-radial-gradient(ellipse at 50% 45%, transparent 0 30px, rgba(150,142,255,.08) 31px 32px), radial-gradient(circle at 50% 42%, rgba(166,156,255,.16), transparent 24%)", texture: "radial-gradient(circle, rgba(216,220,255,.28) 0 1px, transparent 1.5px) 0 0 / 72px 64px", lighting: "rgba(157,145,232,.28)", assetLabel: "인디고 궤도 컨셉아트" },
  galaxy: { id: "rose-nebula-world", label: "장미 성운 세계", description: "성운의 흐름과 발광을 중심으로 한 은하 세계", layout: "nebula", motion: "nebula", background: "radial-gradient(ellipse at 52% 42%, rgba(239,137,194,.3), transparent 30%), radial-gradient(ellipse at 18% 70%, rgba(102,70,185,.28), transparent 35%), #17091e", overlay: "conic-gradient(from 210deg at 52% 43%, transparent, rgba(245,155,220,.14), transparent 38%, rgba(113,89,220,.16), transparent 76%)", texture: "repeating-radial-gradient(ellipse at 52% 43%, transparent 0 26px, rgba(242,157,216,.07) 27px 30px)", lighting: "rgba(255,177,226,.28)", assetLabel: "장미 성운 컨셉아트" },
  ecosystem: { id: "living-canopy-world", label: "생명 캐노피 세계", description: "생명의 나무와 잎, 빛방울을 전면에 둔 생태 세계", layout: "canopy", motion: "wind", background: "radial-gradient(ellipse at 50% 54%, rgba(108,190,100,.26), transparent 38%), linear-gradient(180deg, rgba(3,20,12,.35), rgba(20,72,27,.34))", overlay: "radial-gradient(ellipse at 50% 0%, rgba(196,230,175,.17), transparent 57%)", texture: "radial-gradient(ellipse at 18% 26%, rgba(188,234,143,.16) 0 2px, transparent 3px), radial-gradient(ellipse at 82% 40%, rgba(188,234,143,.13) 0 2px, transparent 3px)", lighting: "rgba(196,230,175,.27)", assetLabel: "생명 캐노피 컨셉아트" },
  ocean: { id: "deep-tide-world", label: "깊은 조류 세계", description: "컨셉아트를 깊은 바다·수면·파동의 세계로 재해석", layout: "oceanic", motion: "ripple", background: "linear-gradient(180deg, rgba(7,46,76,.42), rgba(2,18,34,.7)), radial-gradient(ellipse at 50% 74%, rgba(71,192,210,.22), transparent 40%)", overlay: "repeating-radial-gradient(ellipse at 50% 82%, transparent 0 18px, rgba(123,228,241,.1) 19px 21px), linear-gradient(180deg, rgba(93,202,220,.14), transparent 35%)", texture: "repeating-linear-gradient(165deg, rgba(149,232,243,.07) 0 1px, transparent 1px 10px)", lighting: "rgba(139,231,246,.26)", assetLabel: "깊은 조류 컨셉아트" },
  grassland: { id: "sunlit-field-world", label: "햇살 들판 세계", description: "컨셉아트를 바람 부는 들판과 열린 하늘로 확장", layout: "field", motion: "wind", background: "linear-gradient(180deg, rgba(226,235,190,.68), rgba(136,177,85,.42) 58%, rgba(53,91,39,.4)), radial-gradient(circle at 50% 28%, rgba(255,255,223,.5), transparent 32%)", overlay: "linear-gradient(180deg, rgba(255,252,205,.28), transparent 55%)", texture: "repeating-linear-gradient(102deg, rgba(89,122,48,.1) 0 2px, transparent 2px 14px)", lighting: "rgba(220,242,159,.3)", assetLabel: "햇살 들판 컨셉아트" },
  lava: { id: "molten-core-world", label: "용융 핵 세계", description: "중앙 구체를 화산과 용암의 고열 세계로 재구성", layout: "molten", motion: "flow", background: "radial-gradient(circle at 50% 48%, rgba(255,184,82,.36), transparent 22%), linear-gradient(180deg, rgba(37,7,2,.52), rgba(123,29,8,.46) 62%, rgba(20,3,2,.68))", overlay: "repeating-linear-gradient(118deg, transparent 0 26px, rgba(255,112,40,.12) 27px 29px), radial-gradient(circle at 50% 48%, rgba(255,207,118,.2), transparent 26%)", texture: "repeating-linear-gradient(8deg, rgba(255,148,66,.12) 0 2px, transparent 2px 13px)", lighting: "rgba(255,151,81,.34)", assetLabel: "용융 핵 컨셉아트" },
  minimal: { id: "signal-world", label: "신호 중심 세계", description: "컨셉아트의 핵심 구조만 남긴 절제된 세계", layout: "minimal", motion: "still", background: "linear-gradient(180deg, rgba(22,27,27,.72), rgba(5,8,8,.82)), radial-gradient(circle at 50% 42%, rgba(229,235,225,.14), transparent 28%)", overlay: "linear-gradient(90deg, transparent 18%, rgba(255,255,255,.06) 50%, transparent 82%)", texture: "linear-gradient(rgba(255,255,255,.035) 1px, transparent 1px) 0 0 / 22px 22px", lighting: "rgba(255,255,255,.16)", assetLabel: "신호 중심 컨셉아트" },
  paper: { id: "archive-paper-world", label: "기록지 세계", description: "컨셉아트를 오래된 종이 기록과 인쇄 질감으로 표현", layout: "editorial", motion: "paper-drift", background: "linear-gradient(180deg, rgba(250,244,222,.7), rgba(199,164,106,.36)), #dfcfaa", overlay: "repeating-linear-gradient(90deg, rgba(139,94,52,.08) 0 1px, transparent 1px 8px)", texture: "repeating-linear-gradient(0deg, rgba(107,75,43,.11) 0 1px, transparent 1px 5px), repeating-linear-gradient(90deg, rgba(107,75,43,.04) 0 1px, transparent 1px 8px)", lighting: "rgba(255,235,176,.24)", assetLabel: "기록지 컨셉아트" },
  archive: { id: "bronze-record-world", label: "청동 기록 세계", description: "컨셉아트를 청동 장치와 보관 기록의 분위기로 압축", layout: "archive", motion: "orbit", background: "radial-gradient(circle at 50% 42%, rgba(190,153,92,.2), transparent 28%), linear-gradient(180deg, rgba(28,20,12,.62), rgba(8,7,5,.8))", overlay: "repeating-radial-gradient(circle at 50% 42%, transparent 0 34px, rgba(204,167,107,.09) 35px 36px)", texture: "repeating-linear-gradient(0deg, rgba(215,186,137,.06) 0 1px, transparent 1px 6px)", lighting: "rgba(230,215,184,.22)", assetLabel: "청동 기록 컨셉아트" },
  calm: { id: "calm-wetland-world", label: "고요한 새벽 습지", description: "안개 낀 물가와 물방울 생태 돔이 이어지는 낮은 대비의 고요한 세계", layout: "wetland", motion: "still", background: "linear-gradient(180deg, rgba(190,211,222,.2), rgba(101,133,148,.14) 58%, rgba(34,58,69,.18)), radial-gradient(ellipse at 50% 72%, rgba(232,241,243,.18), transparent 48%)", overlay: "linear-gradient(180deg, rgba(226,237,241,.08), transparent 42%, rgba(94,122,134,.08))", texture: "radial-gradient(ellipse at 28% 74%, rgba(236,245,246,.08), transparent 28%), radial-gradient(ellipse at 72% 68%, rgba(236,245,246,.06), transparent 26%)", lighting: "rgba(207,225,232,.14)", assetLabel: "고요한 새벽·안개 습지 컨셉아트" },
});

// Official themes use their own visual world asset. The default solar world
// remains the approved Ultra Brain concept art; other worlds are true subject
// changes (ocean, meadow, volcano, nebula, archive, and living ecosystem).
export const THEME_WORLD_ASSETS = Object.freeze({
  official: "/ultra-brain-world.png",
  calm: "/world-calm.png",
  light: "/world-light.png",
  dark: "/world-dark.png",
  universe: "/world-universe.png",
  ecosystem: "/world-ecosystem.png",
  ocean: "/world-ocean.png",
  grassland: "/world-grassland.png",
  lava: "/world-lava.png",
  galaxy: "/world-galaxy.png",
  minimal: "/world-minimal.png",
  paper: "/world-paper.png",
  archive: "/world-archive.png",
});

// Official keeps the approved solar concept art. Every other world package
// owns a subject-specific concept image while preserving the same hierarchy,
// composition slots, atmosphere, layout language and component skin.
export const OFFICIAL_WORLD_ASSET = Object.freeze({
  id: "ultra-brain-official-concept-art",
  source: "/ultra-brain-world.png",
  type: "background/world",
  owner: "official",
  immutable: true,
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
  worldStyle: themeWorldRegistry[name]?.description || item.description,
  world: themeWorldRegistry[name] || themeWorldRegistry.official,
  worldAsset: { ...OFFICIAL_WORLD_ASSET, source: THEME_WORLD_ASSETS[name] || OFFICIAL_WORLD_ASSET.source, worldId: (themeWorldRegistry[name] || themeWorldRegistry.official).id },
  assetIds: [THEME_WORLD_ASSETS[name] || OFFICIAL_WORLD_ASSET.source],
  layoutPreset: (themeWorldRegistry[name] || themeWorldRegistry.official).layout,
  navigationStyle: (themeWorldRegistry[name] || themeWorldRegistry.official).layout,
  componentSkin: `${name}-world-skin`,
  states: ["Default", "Hover", "Focus", "Active", "Selected", "Disabled", "Loading", "Error", "Success"],
  animation: (themeWorldRegistry[name] || themeWorldRegistry.official).motion,
  responsive: ["desktop", "tablet", "mobile"],
  lockable: true,
  revisionPolicy: "every-save",
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
    worldEngine: {
      ...(themeWorldRegistry[safe.theme] || themeWorldRegistry.official),
      // 현재 승인된 컨셉아트를 월드 엔진의 기준 에셋으로 연결한다.
      assetSource: THEME_WORLD_ASSETS[safe.theme] || OFFICIAL_WORLD_ASSET.source,
      alt: (themeWorldRegistry[safe.theme] || themeWorldRegistry.official).assetLabel,
    },
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
