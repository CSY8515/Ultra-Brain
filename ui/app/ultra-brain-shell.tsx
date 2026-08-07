"use client";

import type { ChangeEvent, CSSProperties, PointerEvent as ReactPointerEvent } from "react";
import { useEffect, useMemo, useRef, useState } from "react";
import { CanvasEditor } from "./canvas-editor";
import {
  THEME_STORAGE_KEY,
  THEME_ADJUSTMENT_KEYS,
  THEME_ADJUSTMENT_RANGES,
  UI_LOCK_KEYS,
  PROPAGATION_TARGETS,
  applyThemePreset,
  applyPreference,
  createRollbackPoint,
  defaultPreference,
  resolveThemeProfile,
  resolvePropagation,
  themeNames,
  themePackageRegistry,
  themePresets,
  themeRegistry,
  validatePreference,
} from "../lib/theme-engine";

const OS_ECOSYSTEM_URL = "https://8javbq85jtappi6tkdhkt7g.streamlit.app/";
const CURRENT_UI_VERSION = "0.982";
const ACCENT_SWATCHES = ["#c8a55d", "#83aa8c", "#56b8cf", "#9d91e8", "#df86b8", "#e87943", "#d2d7d0"];
const LAYOUT_LABELS = { topbar: "상단 바", center: "중앙 타이틀", seed: "OS Ecosystem", rail: "탐색 레일" } as const;
const PROPAGATION_TARGET_LABELS: Record<string, string> = {
  theme: "테마",
  background: "배경",
  color: "색상",
  brightness: "밝기",
  contrast: "명암",
  saturation: "채도",
  hue: "색조",
  texture: "질감",
  lighting: "광원",
  shadow: "그림자",
  glow: "발광",
  transparency: "투명도",
  blur: "흐림",
  layout: "배치",
  componentPosition: "컴포넌트 위치",
  componentSize: "컴포넌트 크기",
  visibility: "표시 여부",
  animation: "애니메이션",
};
const THEME_ADJUSTMENT_LABELS: Record<ThemeAdjustmentKey, string> = {
  brightness: "밝기",
  contrast: "명암",
  saturation: "채도",
  hue: "색조",
  lighting: "광원",
  shadow: "그림자",
  glow: "발광",
  texture: "질감",
  blur: "흐림",
  transparency: "투명도",
};
const UI_LOCK_LABELS: Record<string, string> = {
  position: "위치 잠금",
  size: "크기 잠금",
  layout: "배치 잠금",
  background: "배경 잠금",
  component: "컴포넌트 잠금",
  color: "색상 잠금",
  texture: "질감 잠금",
  lighting: "광원 잠금",
  layer: "레이어 잠금",
};

type Panel = null | "studio";
type StudioTab = "adjustments" | "themes" | "custom" | "layout" | "propagation";
type LayoutKey = keyof typeof LAYOUT_LABELS;
type LayoutItem = { x: number; y: number; scale: number; visible: boolean; pinned: boolean; group: "core" | "navigation" | "ecosystem" };
type LayoutOffsets = Record<LayoutKey, LayoutItem>;
type Preference = ReturnType<typeof validatePreference>;
type RollbackPoint = ReturnType<typeof createRollbackPoint>;
type ThemeAdjustmentKey = "brightness" | "contrast" | "saturation" | "hue" | "lighting" | "shadow" | "glow" | "texture" | "blur" | "transparency";

const DEFAULT_LAYOUT: LayoutOffsets = {
  topbar: { x: 0, y: 0, scale: 1, visible: true, pinned: true, group: "core" },
  center: { x: 0, y: 0, scale: 1, visible: true, pinned: false, group: "core" },
  seed: { x: 0, y: 0, scale: 1, visible: true, pinned: false, group: "ecosystem" },
  rail: { x: 0, y: 0, scale: 1, visible: true, pinned: false, group: "navigation" },
};

function normaliseLayout(value: unknown): LayoutOffsets {
  const source = value && typeof value === "object" ? value as Partial<Record<LayoutKey, Partial<LayoutItem>>> : {};
  return Object.fromEntries((Object.keys(DEFAULT_LAYOUT) as LayoutKey[]).map((key) => {
    const candidate = source[key] || {};
    return [key, {
      ...DEFAULT_LAYOUT[key],
      x: clamp(Number(candidate.x) || 0, -80, 80),
      y: clamp(Number(candidate.y) || 0, -60, 60),
      scale: clamp(Number(candidate.scale) || 1, .72, 1.32),
      visible: candidate.visible !== false,
      pinned: candidate.pinned === true || DEFAULT_LAYOUT[key].pinned,
      group: candidate.group === "navigation" || candidate.group === "ecosystem" ? candidate.group : "core",
    }];
  })) as LayoutOffsets;
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function hexFromRgb(r: number, g: number, b: number) {
  return `#${[r, g, b].map((value) => Math.round(value).toString(16).padStart(2, "0")).join("")}`;
}

function buildEcosystemUrl(preference: Preference, worldId: string) {
  const url = new URL(OS_ECOSYSTEM_URL);
  const params = url.searchParams;
  params.set("source", "ultra-brain");
  params.set("theme", preference.theme);
  params.set("world", worldId);
  params.set("revision", String(preference.revision));
  for (const key of THEME_ADJUSTMENT_KEYS) params.set(key, String(preference.themeAdjustments[key]));
  return url.toString();
}

export function UltraBrainShell() {
  const [loaded, setLoaded] = useState(false);
  const [hydrated, setHydrated] = useState(false);
  const [panel, setPanel] = useState<Panel>(null);
  const [studioTab, setStudioTab] = useState<StudioTab>("adjustments");
  const [preference, setPreference] = useState<Preference>(defaultPreference);
  const [draftPreference, setDraftPreference] = useState<Preference>(defaultPreference);
  const [layout, setLayout] = useState<LayoutOffsets>(DEFAULT_LAYOUT);
  const [draftLayout, setDraftLayout] = useState<LayoutOffsets>(DEFAULT_LAYOUT);
  const [rollbackStack, setRollbackStack] = useState<(RollbackPoint & { layout?: LayoutOffsets; customBackground?: string | null })[]>([]);
  const [customBackground, setCustomBackground] = useState<string | null>(null);
  const [toast, setToast] = useState("");
  const [layoutSelection, setLayoutSelection] = useState<LayoutKey>("topbar");
  const [propagationSelection, setPropagationSelection] = useState("os-ecosystem");
  const dragRef = useRef<{ key: LayoutKey; startX: number; startY: number; originX: number; originY: number } | null>(null);

  useEffect(() => {
    try {
      const stored = JSON.parse(window.localStorage.getItem(THEME_STORAGE_KEY) || "null");
      if (stored?.releaseVersion === CURRENT_UI_VERSION && stored?.preference) setPreference(validatePreference(stored.preference));
      if (stored?.releaseVersion === CURRENT_UI_VERSION && stored?.layout) setLayout(normaliseLayout(stored.layout));
      if (stored?.releaseVersion === CURRENT_UI_VERSION && stored?.customBackground) setCustomBackground(stored.customBackground);
      if (stored?.releaseVersion === CURRENT_UI_VERSION && stored?.rollbackStack) setRollbackStack(stored.rollbackStack);
    } catch {
      // Local preferences are optional; the official profile remains safe.
    }
    setHydrated(true);
  }, []);

  const activePreference = panel === "studio" ? draftPreference : preference;
  const locks = activePreference.uiLocks;
  const profile = useMemo(() => resolveThemeProfile(activePreference), [activePreference]);
  const ecosystemUrl = useMemo(() => buildEcosystemUrl(preference, resolveThemeProfile(preference).worldEngine.id), [preference]);
  const propagation = useMemo(() => resolvePropagation(activePreference), [activePreference]);
  const selectedPropagationNode = propagation.hierarchy.find((node: { id: string }) => node.id === propagationSelection) || propagation.hierarchy[1];

  useEffect(() => {
    const root = document.documentElement;
    root.dataset.theme = activePreference.theme;
    root.dataset.density = activePreference.density;
    root.dataset.motion = activePreference.motion ? "on" : "off";
    root.style.setProperty("--accent", profile.accent);
    root.style.setProperty("--accent-bright", profile.accentBright);
    root.style.setProperty("--surface", profile.surface);
    root.style.setProperty("--surface-strong", profile.surfaceStrong);
    root.style.setProperty("--text", profile.text);
    root.style.setProperty("--text-soft", profile.textSoft);
    root.style.setProperty("--line", profile.border);
    root.style.setProperty("--world-filter", profile.worldFilter);
    root.style.setProperty("--ui-font", profile.font);
    root.style.setProperty("--ui-radius", profile.radius);
    root.style.setProperty("--ui-shadow", profile.shadow);
    root.style.setProperty("--ui-texture", profile.texture);
    root.style.setProperty("--ui-lighting", profile.lighting);
    root.style.setProperty("--theme-brightness", String(profile.adjustments.brightness));
    root.style.setProperty("--theme-contrast", String(profile.adjustments.contrast));
    root.style.setProperty("--theme-saturation", String(profile.adjustments.saturation));
    root.style.setProperty("--theme-hue", `${profile.adjustments.hue}deg`);
    root.style.setProperty("--theme-lighting", String(profile.adjustments.lighting));
    root.style.setProperty("--theme-shadow", String(profile.adjustments.shadow));
    root.style.setProperty("--theme-glow", String(profile.adjustments.glow));
    root.style.setProperty("--theme-texture", String(profile.adjustments.texture));
    root.style.setProperty("--theme-blur", `${profile.adjustments.blur}px`);
    root.style.setProperty("--theme-transparency", String(profile.adjustments.transparency));
    root.style.setProperty("--world-background", profile.worldEngine.background);
    root.style.setProperty("--world-overlay", profile.worldEngine.overlay);
    root.style.setProperty("--world-texture", profile.worldEngine.texture);
    root.style.setProperty("--world-lighting", profile.worldEngine.lighting);
    root.dataset.worldLayout = profile.worldEngine.layout;
    root.dataset.worldMotion = profile.worldEngine.motion;
  }, [activePreference, profile]);

  useEffect(() => {
    if (!toast) return undefined;
    const timeout = window.setTimeout(() => setToast(""), 3200);
    return () => window.clearTimeout(timeout);
  }, [toast]);

  function openStudio(tab: StudioTab = "adjustments") {
    setDraftPreference(preference);
    setDraftLayout(normaliseLayout(layout));
    setStudioTab(tab);
    if (tab === "propagation") setPropagationSelection("os-ecosystem");
    setPanel("studio");
  }

  function closePanel() {
    setDraftPreference(preference);
    setDraftLayout(normaliseLayout(layout));
    setPanel(null);
  }

  function updateDraft(partial: Partial<Preference>) {
    setDraftPreference((current) => validatePreference({ ...current, ...partial }));
  }

  function toggleUiLock(key: string) {
    if (!UI_LOCK_KEYS.includes(key as never)) return;
    setDraftPreference((current) => validatePreference({ ...current, uiLocks: { ...current.uiLocks, [key]: !current.uiLocks[key as keyof typeof current.uiLocks] } }));
  }

  function togglePropagationTarget(nodeId: string, mode: "lock" | "override", target: string) {
    setDraftPreference((current) => {
      const key = mode === "lock" ? "propagationLocks" : "propagationOverrides";
      const sourceMap = current[key] || {};
      const selectedTargets = Array.isArray(sourceMap[nodeId]) ? sourceMap[nodeId] : [];
      const nextTargets = selectedTargets.includes(target) ? selectedTargets.filter((item: string) => item !== target) : [...selectedTargets, target];
      const nextMap = { ...sourceMap };
      if (nextTargets.length) nextMap[nodeId] = nextTargets;
      else delete nextMap[nodeId];
      const aliases = nodeId === "os-ecosystem" ? {
        osEcosystemLocked: mode === "lock" ? nextTargets.length === current.propagationTargets.length : current.osEcosystemLocked,
        propagationOverride: mode === "override" ? nextTargets.length === current.propagationTargets.length : current.propagationOverride,
      } : {};
      return validatePreference({ ...current, [key]: nextMap, ...aliases });
    });
  }

  function toggleEcosystemLock() {
    setDraftPreference((current) => {
      const nextLocked = !current.osEcosystemLocked;
      const propagationLocks = { ...current.propagationLocks };
      if (nextLocked) propagationLocks["os-ecosystem"] = [...current.propagationTargets];
      else delete propagationLocks["os-ecosystem"];
      return validatePreference({ ...current, osEcosystemLocked: nextLocked, propagationLocks });
    });
  }

  function toggleEcosystemOverride() {
    setDraftPreference((current) => {
      const nextOverride = !current.propagationOverride;
      const propagationOverrides = { ...current.propagationOverrides };
      if (nextOverride) propagationOverrides["os-ecosystem"] = [...current.propagationTargets];
      else delete propagationOverrides["os-ecosystem"];
      return validatePreference({ ...current, propagationOverride: nextOverride, propagationOverrides });
    });
  }

  function selectTheme(theme: string) {
    // 기본 조정값은 테마와 독립적으로 유지한다. 테마는 월드 패키지만 교체한다.
    updateDraft({ theme: theme as Preference["theme"], accent: themeRegistry[theme].accent });
    setToast(`${themeRegistry[theme].label} 미리보기`);
  }

  function updateThemeAdjustment(key: ThemeAdjustmentKey, value: number) {
    const locked = key === "texture" ? locks.texture : key === "lighting" || key === "shadow" || key === "glow" ? locks.lighting : locks.color;
    if (locked) {
      setToast("이 설정은 잠겨 있습니다");
      return;
    }
    updateDraft({ themePreset: "custom", themeAdjustments: { ...draftPreference.themeAdjustments, [key]: value } });
  }

  function selectThemePreset(preset: string) {
    setDraftPreference((current) => applyThemePreset(current, preset));
    setToast(`${themePresets[preset].label} 프리셋 미리보기`);
  }

  function exportThemePackage() {
    const packageData = {
      format: "ultra-brain.theme/v1",
      exportedAt: new Date().toISOString(),
      package: themePackageRegistry[draftPreference.theme],
      preference: { theme: draftPreference.theme, accent: draftPreference.accent, themePreset: draftPreference.themePreset, themeAdjustments: draftPreference.themeAdjustments },
    };
    const url = URL.createObjectURL(new Blob([JSON.stringify(packageData, null, 2)], { type: "application/json" }));
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${draftPreference.theme}-theme-package.json`;
    anchor.click();
    URL.revokeObjectURL(url);
    setToast("테마 패키지를 내보냈습니다");
  }

  function importThemePackage(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const data = JSON.parse(String(reader.result));
        const source = data.preference || data;
        const imported = validatePreference({ ...draftPreference, theme: source.theme, accent: source.accent, themePreset: source.themePreset, themeAdjustments: source.themeAdjustments });
        setDraftPreference(imported);
        setToast("테마 패키지를 미리보기에 적용했습니다");
      } catch {
        setToast("테마 패키지를 읽을 수 없습니다");
      }
    };
    reader.readAsText(file);
    event.target.value = "";
  }

  function persist(nextPreference: Preference, nextLayout: LayoutOffsets, nextRollbacks: RollbackPoint[], background = customBackground) {
    window.localStorage.setItem(THEME_STORAGE_KEY, JSON.stringify({ releaseVersion: CURRENT_UI_VERSION, preference: nextPreference, layout: nextLayout, rollbackStack: nextRollbacks, customBackground: background }));
  }

  function saveStudio() {
    const result = applyPreference(preference, draftPreference);
    setPreference(result.next);
    const nextLayout = normaliseLayout(draftLayout);
    setLayout(nextLayout);
    const rollback = { ...result.rollback, layout: normaliseLayout(layout), customBackground };
    const nextRollbacks = [rollback, ...rollbackStack].slice(0, 6);
    setRollbackStack(nextRollbacks);
    persist(result.next, nextLayout, nextRollbacks, customBackground);
    setPanel(null);
    setToast(`UI 저장 · 리비전 ${result.next.revision}`);
  }

  function rollbackLast() {
    const [point, ...rest] = rollbackStack;
    if (!point) {
      setToast("되돌릴 지점이 없습니다");
      return;
    }
    const next = validatePreference(point.preference);
    setPreference(next);
    setDraftPreference(next);
    setLayout(normaliseLayout(point.layout || DEFAULT_LAYOUT));
    setDraftLayout(normaliseLayout(point.layout || DEFAULT_LAYOUT));
    setCustomBackground(point.customBackground || null);
    setRollbackStack(rest);
    persist(next, normaliseLayout(point.layout || DEFAULT_LAYOUT), rest, point.customBackground || null);
    setToast("이전 UI 상태로 되돌렸습니다");
  }

  function resetLayout() {
    if (locks.layout) {
      setToast("배치가 잠겨 있습니다");
      return;
    }
    setDraftLayout(DEFAULT_LAYOUT);
    setToast("배치를 초기화했습니다");
  }

  function updateLayout(key: LayoutKey, patch: Partial<LayoutOffsets[LayoutKey]>) {
    const fields = Object.keys(patch);
    const positionChange = fields.some((field) => ["x", "y"].includes(field));
    const sizeChange = fields.includes("scale");
    const layerChange = fields.some((field) => ["visible", "pinned", "group"].includes(field));
    if (locks.layout || (positionChange && locks.position) || (sizeChange && locks.size) || (layerChange && locks.layer) || (layerChange && locks.component)) {
      setToast(locks.layout ? "배치가 잠겨 있습니다" : "컴포넌트가 잠겨 있습니다");
      return;
    }
    setDraftLayout((current) => ({ ...current, [key]: { ...current[key], ...patch } }));
  }

  function alignSelected(axis: "x" | "y") {
    if (locks.layout) {
      setToast("배치가 잠겨 있습니다");
      return;
    }
    updateLayout(layoutSelection, { [axis]: 0 });
  }

  function onLayoutPointerDown(key: LayoutKey, event: ReactPointerEvent<HTMLButtonElement>) {
    if (locks.layout || locks.position || draftLayout[key].pinned) return;
    event.currentTarget.setPointerCapture(event.pointerId);
    setLayoutSelection(key);
    const origin = draftLayout[key];
    dragRef.current = { key, startX: event.clientX, startY: event.clientY, originX: origin.x, originY: origin.y };
  }

  function onLayoutPointerMove(event: ReactPointerEvent<HTMLButtonElement>) {
    const drag = dragRef.current;
    if (!drag) return;
    updateLayout(drag.key, { x: clamp(Math.round(drag.originX + (event.clientX - drag.startX) / 2), -80, 80), y: clamp(Math.round(drag.originY + (event.clientY - drag.startY) / 2), -60, 60) });
  }

  function onLayoutPointerUp() {
    dragRef.current = null;
  }

  function importBackground(event: ChangeEvent<HTMLInputElement>) {
    if (locks.background) {
      setToast("배경이 잠겨 있습니다");
      event.target.value = "";
      return;
    }
    const file = event.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const source = String(reader.result);
      setCustomBackground(source);
      const image = new Image();
      image.onload = () => {
        const canvas = document.createElement("canvas");
        canvas.width = 1;
        canvas.height = 1;
        const context = canvas.getContext("2d");
        if (!context) return;
        context.drawImage(image, 0, 0, 1, 1);
        const pixel = context.getImageData(0, 0, 1, 1).data;
        updateDraft({ accent: hexFromRgb(pixel[0], pixel[1], pixel[2]) });
        setToast("이미지를 가져오고 대표 색상을 추출했습니다");
      };
      image.src = source;
    };
    reader.readAsDataURL(file);
  }

  function applyUserCustomTheme(preview: string, name: string) {
    if (locks.background) {
      setToast("배경이 잠겨 있습니다");
      return;
    }
    setCustomBackground(preview);
    updateDraft({ themePreset: "custom" });
    setToast(`${name} 사용자 UI를 미리보기에 적용했습니다`);
  }

  const shellStyle = { "--ui-contrast": profile.adjustments.contrast } as CSSProperties;
  const topbarStyle = { translate: `${layout.topbar.x}px ${layout.topbar.y}px`, scale: layout.topbar.scale } as CSSProperties;
  const centerStyle = { translate: `calc(-50% + ${layout.center.x}px) calc(-50% + ${layout.center.y}px)`, scale: layout.center.scale, visibility: layout.center.visible ? "visible" : "hidden" } as CSSProperties;
  const seedStyle = { left: `calc(50% + ${layout.seed.x}px)`, bottom: `calc(12.5% + ${layout.seed.y}px)`, scale: layout.seed.scale, visibility: layout.seed.visible ? "visible" : "hidden" } as CSSProperties;
  const railStyle = { right: `calc(25px - ${layout.rail.x}px)`, top: `calc(50% + ${layout.rail.y}px)`, scale: layout.rail.scale, visibility: layout.rail.visible ? "visible" : "hidden" } as CSSProperties;
  const statusStyle = { left: "22px", bottom: "18px" } as CSSProperties;

  if (!hydrated) return <div className="world-loading" aria-label="Ultra Brain 로딩"><div className="loading-mark" /><p>Ultra Brain을 여는 중</p><span className="loading-line" /></div>;

  return (
    <main className={`world-shell world-layout-${profile.worldEngine.layout} world-motion-${profile.worldEngine.motion}`} aria-label="Ultra Brain" style={shellStyle}>
      <img className={`world-art ${loaded ? "is-loaded" : ""}`} src={profile.worldEngine.assetSource || "/ultra-brain-world.png"} alt={profile.worldEngine.alt || "중앙 태양과 생명의 나무가 있는 세계"} onLoad={() => setLoaded(true)} />
      {customBackground && <div className="custom-world-art is-user-custom" style={{ backgroundImage: `url(${customBackground})` }} aria-hidden="true" />}
      <div className="world-atmosphere" aria-hidden="true" />
      <div className="world-ambient" aria-hidden="true" />
      <div className="world-theme-texture" aria-hidden="true" />
      <div className="world-theme-lighting" aria-hidden="true" />
      <div className="world-vignette" aria-hidden="true" />
      <div className="world-texture" aria-hidden="true" />

      <header className="orientation-bar" style={topbarStyle}>
        <div className="topbar-left">
          <a className="brand" href="#ultra-brain" aria-label="Ultra Brain home">
            <span className="brand-sigil" aria-hidden="true">✦</span>
            <span><strong>Ultra Brain</strong><small>Official UI</small></span>
          </a>
          <button className="studio-launch" type="button" onClick={() => openStudio("adjustments")} aria-label="UI 스튜디오 열기">
            <span aria-hidden="true">✦</span><span><strong>UI 스튜디오</strong><small>화면 설정</small></span>
          </button>
        </div>
        <nav className="world-path" aria-label="Current location"><span>Ultra Brain</span><i>/</i><span aria-current="page">OS Ecosystem</span></nav>
        <div className="top-actions">
          <button className="icon-button" type="button" onClick={() => setPanel("notifications")} aria-label="Open notifications">◌<span className="notice-dot" /></button>
          <button className="icon-button" type="button" onClick={() => openStudio("adjustments")} aria-label="UI 스튜디오 열기">◈</button>
        </div>
      </header>

      <section id="ultra-brain" className="world-center" style={centerStyle} aria-labelledby="ultra-brain-title">
        <span className="title-rule title-rule-top" aria-hidden="true" />
        <h1 id="ultra-brain-title">Ultra Brain</h1>
        <span className="title-rule" aria-hidden="true" />
      </section>

      <a className="ecosystem-seed" style={seedStyle} href={ecosystemUrl} target="_blank" rel="noreferrer" aria-label="Open OS Ecosystem in a new tab">
        <span className="seed-aura" aria-hidden="true" />
        <span className="seed-copy"><strong>OS Ecosystem</strong></span>
      </a>
      <img className="world-focus-art" src={profile.worldEngine.assetSource || "/ultra-brain-world.png"} alt="" aria-hidden="true" />

      <nav className="world-rail" style={railStyle} aria-label="System navigation">
        <a className="rail-item is-current" href={ecosystemUrl} target="_blank" rel="noreferrer" aria-label="Open OS Ecosystem"><b>⌂</b><span>OS Ecosystem</span></a>
        <span className="rail-line" aria-hidden="true" />
        <button className="rail-item rail-studio" type="button" onClick={() => openStudio("propagation")} aria-label="Open propagation controls"><b>↯</b><span>Propagation</span></button>
      </nav>

      <aside className="status-dock" style={statusStyle} aria-label="System status">
        <div><span className="health-dot" /> <strong>정상</strong></div><i /><span>OS Ecosystem 연결됨</span><i /><span>v0.982</span><button type="button" onClick={() => openStudio("adjustments")}>기본 조정</button>
      </aside>

      {panel === "notifications" && <section className="notice-panel floating-panel" aria-label="Notifications">
        <div className="panel-heading"><div><small>시스템 알림</small><h2>모두 정상</h2></div><button type="button" onClick={closePanel} aria-label="알림 닫기">×</button></div>
        <div className="notice-card"><span className="health-dot" /><div><strong>OS Ecosystem 정상</strong><p>연결된 하위 시스템이 준비되어 있습니다.</p></div></div>
        <p className="empty-note">해결되지 않은 UI·자동 적용 알림이 없습니다.</p>
      </section>}

      {panel === "studio" && <>
        <div className="drawer-scrim" onClick={closePanel} aria-hidden="true" />
        <aside className={`settings-drawer is-open ${studioTab === "custom" ? "is-canvas" : ""}`} aria-label="UI 스튜디오">
          <div className="drawer-topline"><span className="eyebrow">UI 스튜디오</span><button type="button" onClick={closePanel} aria-label="UI 스튜디오 닫기">×</button></div>
          <h2>화면 만들고 관리하기</h2>
          <p className="drawer-intro">바꾼 내용은 먼저 미리 보고 저장할 수 있습니다. 저장 전에는 현재 화면에 적용되지 않습니다.</p>
          <div className="studio-tabs" role="tablist" aria-label="UI Studio sections">
            {(["adjustments", "themes", "custom", "layout", "propagation"] as StudioTab[]).map((tab) => <button key={tab} type="button" role="tab" aria-selected={studioTab === tab} className={studioTab === tab ? "is-selected" : ""} onClick={() => setStudioTab(tab)}>{tab === "adjustments" ? "기본 조정" : tab === "themes" ? "테마" : tab === "custom" ? "사용자 지정 UI" : tab === "layout" ? "배치·잠금" : "자동 적용"}</button>)}
          </div>

          {studioTab === "adjustments" && <div className="studio-pane">
            <div className="studio-section-intro"><strong>전체 화면 기본 조정</strong><span>테마와 관계없이 모든 화면에 적용됩니다.</span></div>
            <fieldset><legend>빛·색·질감</legend><div className="adjustment-grid">{THEME_ADJUSTMENT_KEYS.map((key: ThemeAdjustmentKey) => { const range = THEME_ADJUSTMENT_RANGES[key]; const value = activePreference.themeAdjustments[key]; const locked = key === "texture" ? locks.texture : key === "lighting" || key === "shadow" || key === "glow" ? locks.lighting : locks.color; return <label key={key} className={locked ? "is-locked" : ""}><span>{THEME_ADJUSTMENT_LABELS[key]}</span><input type="range" min={range.min} max={range.max} step={range.step} value={value} disabled={locked} onChange={(event) => updateThemeAdjustment(key, Number(event.target.value))} aria-label={`${THEME_ADJUSTMENT_LABELS[key]} 조정`} /><output>{Number(value).toFixed(range.step < 1 ? 2 : 0)}{range.unit === "x" ? "×" : range.unit}</output></label>; })}</div></fieldset>
            <div className="studio-action-row"><button type="button" onClick={() => { setDraftPreference((current) => validatePreference({ ...current, themePreset: "balanced", themeAdjustments: themePresets.balanced.adjustments })); setToast("기본 조정을 처음 값으로 되돌렸습니다"); }}>기본값으로 되돌리기</button><button type="button" onClick={() => setToast("현재 조정값을 미리 보고 있습니다")}>미리보기</button></div>
          </div>}

          {studioTab === "themes" && <div className="studio-pane">
            <div className="theme-mode-switch"><button type="button" className="is-selected">공식 테마</button><button type="button" onClick={() => setStudioTab("custom")}>사용자 UI</button></div>
            <fieldset><legend>테마 브라우저</legend><div className="theme-grid">{themeNames.map((theme) => { const item = themeRegistry[theme]; const world = profile.worldEngine && activePreference.theme === theme ? profile.worldEngine : resolveThemeProfile({ ...activePreference, theme }).worldEngine; return <button key={theme} type="button" className={activePreference.theme === theme ? "is-selected" : ""} onClick={() => selectTheme(theme)}><span className={`theme-preview ${theme} world-preview-${world.layout}`} style={{ backgroundImage: `${world.background}, url(${world.assetSource || "/ultra-brain-world.png"})`, backgroundSize: "cover", backgroundPosition: "center", filter: `${item.worldFilter} contrast(${profile.adjustments.contrast}) saturate(${profile.adjustments.saturation})` }} /><strong>{item.label}</strong><small>{world.label} · {world.motion === "still" ? "정적" : "움직임"}</small></button>; })}</div></fieldset>
            <fieldset><legend>강조 색상</legend><div className="accent-row">{ACCENT_SWATCHES.map((accent) => <button key={accent} type="button" className={activePreference.accent.toLowerCase() === accent ? "is-selected" : ""} style={{ "--swatch": accent } as CSSProperties} onClick={() => updateDraft({ accent })} aria-label={`강조 색상 ${accent} 사용`} />)}<label className="accent-picker" aria-label="사용자 색상 선택"><input type="color" value={activePreference.accent} onChange={(event) => updateDraft({ accent: event.target.value })} /><span>직접 선택</span></label></div></fieldset>
            <fieldset><legend>사용자 테마</legend><label className="file-drop"><input type="file" accept="image/*" onChange={importBackground} /><span>가져오기</span><small>내 이미지를 세계 배경으로 사용합니다.</small></label>{customBackground && <button className="text-action" type="button" onClick={() => { setCustomBackground(null); setToast("가져온 배경을 제거했습니다"); }}>가져온 배경 제거</button>}</fieldset>
            <fieldset><legend>테마 프리셋</legend><div className="preset-row">{Object.values(themePresets).map((preset: { id: string; label: string; description: string }) => <button key={preset.id} type="button" className={activePreference.themePreset === preset.id ? "is-selected" : ""} onClick={() => selectThemePreset(preset.id)}><strong>{preset.label}</strong><small>{preset.description}</small></button>)}</div></fieldset>
            <small className="field-hint">테마를 고르면 해당 세계의 컨셉아트·배치·광원·질감·버튼 모양이 함께 바뀝니다. 세부 조정은 ‘기본 조정’에서 합니다.</small>
            <fieldset><legend>테마 패키지</legend><div className="theme-package-card"><div><span className="detail-swatch" style={{ background: profile.accent }} /><strong>{profile.package.name} · {profile.package.version}</strong></div><p>{profile.package.worldStyle}<br />상세 조정 {profile.package.adjustmentKeys.length}개 · 가져오기 준비 · 내보내기 준비</p></div><div className="package-actions"><label className="package-import"><input type="file" accept="application/json,.json" onChange={importThemePackage} /><span>패키지 가져오기</span></label><button className="text-action" type="button" onClick={exportThemePackage}>패키지 내보내기</button></div></fieldset>
            <div className="theme-detail-card"><div><span className="detail-swatch" style={{ background: profile.accent }} /><strong>{themeRegistry[activePreference.theme].label} · 이미지 월드</strong></div><div className={`theme-world-preview world-preview-${profile.worldEngine.layout}`} style={{ backgroundImage: `linear-gradient(145deg, ${profile.worldEngine.background}, transparent), url(${profile.worldEngine.assetSource || "/ultra-brain-world.png"})`, backgroundSize: "cover", backgroundPosition: "center" }}><span>{profile.worldEngine.assetLabel}</span></div><p>세계관 · {profile.worldEngine.label}<br />배치 · {profile.worldEngine.layout} · 움직임 · {profile.worldEngine.motion}<br />글꼴 · {profile.font.split(",")[0]} · 모서리 · {profile.radius}<br />{themePresets[activePreference.themePreset]?.label || "사용자 지정"} 기본 조정</p></div>
          </div>}

          {studioTab === "layout" && <div className="studio-pane">
            <fieldset><legend>배치 편집기</legend><div className="layout-stage"><div className="layout-stage-world" aria-hidden="true" />{(Object.keys(LAYOUT_LABELS) as LayoutKey[]).map((key) => <button key={key} type="button" draggable={!locks.layout && !draftLayout[key].pinned} className={`layout-node ${layoutSelection === key ? "is-selected" : ""} ${draftLayout[key].visible ? "" : "is-hidden"} layout-${key}`} style={{ transform: `translate(${draftLayout[key].x}px, ${draftLayout[key].y}px) scale(${draftLayout[key].scale})` }} onClick={() => setLayoutSelection(key)} onPointerDown={(event) => onLayoutPointerDown(key, event)} onPointerMove={onLayoutPointerMove} onPointerUp={onLayoutPointerUp} onPointerCancel={onLayoutPointerUp}>{LAYOUT_LABELS[key]}</button>)}</div><small className="field-hint">노드를 드래그해 위치를 바꾸고, 아래에서 크기·표시·고정을 조정합니다.</small></fieldset>
            <fieldset><legend>{LAYOUT_LABELS[layoutSelection]} 설정</legend><div className="range-row"><label>X <input type="range" min="-80" max="80" disabled={locks.layout || draftLayout[layoutSelection].pinned} value={draftLayout[layoutSelection].x} onChange={(event) => updateLayout(layoutSelection, { x: Number(event.target.value) })} /><output>{draftLayout[layoutSelection].x}px</output></label><label>Y <input type="range" min="-60" max="60" disabled={locks.layout || draftLayout[layoutSelection].pinned} value={draftLayout[layoutSelection].y} onChange={(event) => updateLayout(layoutSelection, { y: Number(event.target.value) })} /><output>{draftLayout[layoutSelection].y}px</output></label><label>크기 <input type="range" min="0.72" max="1.32" step="0.01" disabled={locks.layout || locks.component} value={draftLayout[layoutSelection].scale} onChange={(event) => updateLayout(layoutSelection, { scale: Number(event.target.value) })} /><output>{Math.round(draftLayout[layoutSelection].scale * 100)}%</output></label></div></fieldset>
            <div className="layout-control-grid"><button type="button" className={draftLayout[layoutSelection].visible ? "is-selected" : ""} onClick={() => updateLayout(layoutSelection, { visible: !draftLayout[layoutSelection].visible })}>표시 {draftLayout[layoutSelection].visible ? "켜짐" : "꺼짐"}</button><button type="button" className={draftLayout[layoutSelection].pinned ? "is-selected" : ""} onClick={() => updateLayout(layoutSelection, { pinned: !draftLayout[layoutSelection].pinned })}>고정 {draftLayout[layoutSelection].pinned ? "켜짐" : "꺼짐"}</button><select aria-label="컴포넌트 그룹" disabled={locks.layout || locks.component} value={draftLayout[layoutSelection].group} onChange={(event) => updateLayout(layoutSelection, { group: event.target.value as LayoutItem["group"] })}><option value="core">핵심</option><option value="navigation">이동</option><option value="ecosystem">OS Ecosystem</option></select></div>
            <div className="layout-align-row"><span>정렬</span><button type="button" onClick={() => alignSelected("x")}>가로 중앙</button><button type="button" onClick={() => alignSelected("y")}>세로 중앙</button></div>
            <fieldset><legend>배치 잠금</legend><div className="lock-grid">{UI_LOCK_KEYS.map((key) => <button key={key} type="button" className={draftPreference.uiLocks[key] ? "is-selected" : ""} aria-pressed={draftPreference.uiLocks[key]} onClick={() => toggleUiLock(key)}>{UI_LOCK_LABELS[key]} <span>{draftPreference.uiLocks[key] ? "해제" : "잠금"}</span></button>)}</div></fieldset>
            <button className="text-action" type="button" onClick={resetLayout}>배치 초기화</button>
          </div>}

          {studioTab === "custom" && <CanvasEditor baseTheme={themeRegistry[draftPreference.theme].label} onUseTheme={applyUserCustomTheme} onToast={setToast} />}

          {studioTab === "propagation" && <div className="studio-pane">
            <div className="propagation-banner"><span className={profile.propagation.status === "locked" ? "lock-state" : "health-dot"} /><div><strong>{profile.propagation.status === "locked" ? "전달 잠금" : profile.propagation.status === "override" ? "예외 적용 중" : "계층 자동 적용"}</strong><small>{profile.propagation.contract} · 연결 규격 {profile.propagation.interfaceVersion} · 변경 번호 {propagation.revision}</small></div></div>
            <div className="hierarchy-note"><strong>하나의 UI 기준</strong><span>Ultra Brain UI Studio가 모든 계층을 관리합니다. 잠금되지 않은 하위 항목에는 저장된 UI가 자동 적용됩니다.</span></div>
            <div className="propagation-hierarchy" aria-label="UI propagation hierarchy">
              {propagation.hierarchy.map((node: { id: string; label: string; kind: string; status: string; automatic: boolean; appliedTargets: string[]; lockedTargets: string[]; overriddenTargets: string[] }, index: number) => {
                const statusLabel = node.status === "source" ? "기준" : node.status === "locked" ? "잠금" : node.status === "override" ? "예외" : "자동 적용";
                return <button key={node.id} type="button" className={`hierarchy-node ${propagationSelection === node.id ? "is-selected" : ""}`} onClick={() => setPropagationSelection(node.id)}>
                  <span className={`hierarchy-index status-${node.status}`}>{index + 1}</span>
                  <span className="hierarchy-copy"><strong>{node.label}</strong><small>{node.kind === "source" ? "UI Studio 기준" : node.kind === "registered-child" ? "연결된 하위 시스템" : "하위 적용 대상"}</small></span>
                  <em className={`propagation-status status-${node.status}`}>{statusLabel}</em>
                  {index < propagation.hierarchy.length - 1 && <i aria-hidden="true">↓</i>}
                </button>;
              })}
            </div>
            <div className="propagation-editor-card">
              <div className="editor-card-heading"><div><small>선택한 계층</small><strong>{selectedPropagationNode?.label}</strong></div><span className="auto-apply-badge">{selectedPropagationNode?.kind === "source" ? "여기서 편집" : "하위 편집 잠금"}</span></div>
              <p className="field-hint">{selectedPropagationNode?.kind === "source" ? "여기서 기준 UI를 편집합니다. 저장한 설정은 잠금되지 않은 하위 계층에 전달됩니다." : "Ultra Brain UI Studio에서 관리합니다. 이 계층에서는 직접 UI를 편집할 수 없습니다."}</p>
              {selectedPropagationNode?.kind !== "source" && <div className="target-grid" aria-label={`Propagation targets for ${selectedPropagationNode?.label}`}>
                {PROPAGATION_TARGETS.map((target: string) => {
                  const locked = (draftPreference.propagationLocks[selectedPropagationNode?.id || ""] || []).includes(target);
                  const overridden = (draftPreference.propagationOverrides[selectedPropagationNode?.id || ""] || []).includes(target);
                  return <div key={target} className={`propagation-target ${locked ? "is-locked" : ""} ${overridden ? "is-overridden" : ""}`}>
                    <span>{PROPAGATION_TARGET_LABELS[target]}</span>
                    <button type="button" className={`target-toggle ${locked ? "is-on" : ""}`} onClick={() => togglePropagationTarget(selectedPropagationNode?.id || "os-ecosystem", "lock", target)} aria-pressed={locked}>{locked ? "잠금 해제" : "잠금"}</button>
                    <button type="button" className={`target-toggle ${overridden ? "is-on" : ""}`} onClick={() => togglePropagationTarget(selectedPropagationNode?.id || "os-ecosystem", "override", target)} aria-pressed={overridden}>{overridden ? "예외 해제" : "예외"}</button>
                  </div>;
                })}
              </div>}
              {selectedPropagationNode?.kind === "source" && <div className="source-target-summary"><span className="health-dot" /><strong>{PROPAGATION_TARGETS.length}개 대상이 여기서 시작됩니다</strong><small>테마, 화면 보정, 배치, 요소 크기, 표시 여부와 움직임을 전달합니다.</small></div>}
            </div>
            <div className="setting-row"><div><strong>OS Ecosystem 잠금</strong><small>저장한 UI가 연결된 하위 시스템으로 전달되지 않도록 유지합니다.</small></div><button className={`switch ${draftPreference.osEcosystemLocked ? "is-on" : ""}`} type="button" role="switch" aria-checked={draftPreference.osEcosystemLocked} onClick={toggleEcosystemLock}><span /></button></div>
            <div className="setting-row"><div><strong>OS Ecosystem 예외 적용</strong><small>하위 시스템의 독립 소유권은 유지한 채 전달 규칙을 미리 확인합니다.</small></div><button className={`switch ${draftPreference.propagationOverride ? "is-on" : ""}`} type="button" role="switch" aria-checked={draftPreference.propagationOverride} onClick={toggleEcosystemOverride}><span /></button></div>
            <div className="propagation-payload"><div><small>전달 미리보기</small><strong>{themeRegistry[draftPreference.theme].label} · 변경 번호 {draftPreference.revision}</strong></div><span>{selectedPropagationNode?.appliedTargets?.length || 0}개 자동 적용 · {selectedPropagationNode?.lockedTargets?.length || 0}개 잠금 · {selectedPropagationNode?.overriddenTargets?.length || 0}개 예외</span></div>
          </div>}

          <div className="drawer-actions"><button className="secondary-action" type="button" onClick={closePanel}>취소</button><button className="primary-action" type="button" onClick={saveStudio}>UI 저장</button></div>
        </aside>
      </>}

      {toast && <div className="toast" role="status"><span className="health-dot" />{toast}</div>}
    </main>
  );
}
