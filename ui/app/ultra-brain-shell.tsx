"use client";

import type { ChangeEvent, CSSProperties, PointerEvent as ReactPointerEvent } from "react";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  THEME_STORAGE_KEY,
  THEME_ADJUSTMENT_KEYS,
  THEME_ADJUSTMENT_RANGES,
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
const ACCENT_SWATCHES = ["#c8a55d", "#83aa8c", "#56b8cf", "#9d91e8", "#df86b8", "#e87943", "#d2d7d0"];
const LAYOUT_LABELS = { topbar: "Topbar", center: "World identity", seed: "OS Entry", rail: "Navigation rail", status: "Status dock" } as const;
const PROPAGATION_TARGET_LABELS: Record<string, string> = {
  theme: "Theme",
  background: "Background",
  color: "Color",
  brightness: "Brightness",
  contrast: "Contrast",
  saturation: "Saturation",
  hue: "Hue",
  texture: "Texture",
  lighting: "Lighting",
  shadow: "Shadow",
  glow: "Glow",
  transparency: "Transparency",
  blur: "Blur",
  layout: "Layout",
  componentPosition: "Component position",
  componentSize: "Component size",
  visibility: "Visibility",
  animation: "Animation",
};

type Panel = null | "studio" | "notifications";
type StudioTab = "themes" | "layout" | "propagation" | "preview";
type LayoutKey = keyof typeof LAYOUT_LABELS;
type LayoutOffsets = Record<LayoutKey, { x: number; y: number }>;
type Preference = ReturnType<typeof validatePreference>;
type RollbackPoint = ReturnType<typeof createRollbackPoint>;
type ThemeAdjustmentKey = "brightness" | "contrast" | "saturation" | "hue" | "lighting" | "shadow" | "glow" | "texture" | "blur" | "transparency";

const DEFAULT_LAYOUT: LayoutOffsets = {
  topbar: { x: 0, y: 0 },
  center: { x: 0, y: 0 },
  seed: { x: 0, y: 0 },
  rail: { x: 0, y: 0 },
  status: { x: 0, y: 0 },
};

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function hexFromRgb(r: number, g: number, b: number) {
  return `#${[r, g, b].map((value) => Math.round(value).toString(16).padStart(2, "0")).join("")}`;
}

export function UltraBrainShell() {
  const [loaded, setLoaded] = useState(false);
  const [hydrated, setHydrated] = useState(false);
  const [panel, setPanel] = useState<Panel>(null);
  const [studioTab, setStudioTab] = useState<StudioTab>("themes");
  const [preference, setPreference] = useState<Preference>(defaultPreference);
  const [draftPreference, setDraftPreference] = useState<Preference>(defaultPreference);
  const [layout, setLayout] = useState<LayoutOffsets>(DEFAULT_LAYOUT);
  const [draftLayout, setDraftLayout] = useState<LayoutOffsets>(DEFAULT_LAYOUT);
  const [rollbackStack, setRollbackStack] = useState<RollbackPoint[]>([]);
  const [customBackground, setCustomBackground] = useState<string | null>(null);
  const [toast, setToast] = useState("");
  const [layoutSelection, setLayoutSelection] = useState<LayoutKey>("topbar");
  const [propagationSelection, setPropagationSelection] = useState("os-ecosystem");
  const dragRef = useRef<{ key: LayoutKey; startX: number; startY: number; originX: number; originY: number } | null>(null);

  useEffect(() => {
    try {
      const stored = JSON.parse(window.localStorage.getItem(THEME_STORAGE_KEY) || "null");
      if (stored?.preference) setPreference(validatePreference(stored.preference));
      if (stored?.layout) setLayout({ ...DEFAULT_LAYOUT, ...stored.layout });
      if (stored?.rollbackStack) setRollbackStack(stored.rollbackStack);
    } catch {
      // Local preferences are optional; the official profile remains safe.
    }
    setHydrated(true);
  }, []);

  const activePreference = panel === "studio" ? draftPreference : preference;
  const profile = useMemo(() => resolveThemeProfile(activePreference), [activePreference]);
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
  }, [activePreference, profile]);

  useEffect(() => {
    if (!toast) return undefined;
    const timeout = window.setTimeout(() => setToast(""), 3200);
    return () => window.clearTimeout(timeout);
  }, [toast]);

  function openStudio(tab: StudioTab = "themes") {
    setDraftPreference(preference);
    setDraftLayout(layout);
    setStudioTab(tab);
    if (tab === "propagation") setPropagationSelection("os-ecosystem");
    setPanel("studio");
  }

  function closePanel() {
    setDraftPreference(preference);
    setDraftLayout(layout);
    setPanel(null);
  }

  function updateDraft(partial: Partial<Preference>) {
    setDraftPreference((current) => validatePreference({ ...current, ...partial }));
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
    updateDraft({ theme: theme as Preference["theme"], accent: themeRegistry[theme].accent, themePreset: "balanced", themeAdjustments: themePresets.balanced.adjustments });
    setToast(`${themeRegistry[theme].label} preview`);
  }

  function updateThemeAdjustment(key: ThemeAdjustmentKey, value: number) {
    updateDraft({ themePreset: "custom", themeAdjustments: { ...draftPreference.themeAdjustments, [key]: value } });
  }

  function selectThemePreset(preset: string) {
    setDraftPreference((current) => applyThemePreset(current, preset));
    setToast(`${themePresets[preset].label} preset preview`);
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
    setToast("Theme package exported");
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
        setToast("Theme package imported for preview");
      } catch {
        setToast("Theme package could not be read");
      }
    };
    reader.readAsText(file);
    event.target.value = "";
  }

  function persist(nextPreference: Preference, nextLayout: LayoutOffsets, nextRollbacks: RollbackPoint[]) {
    window.localStorage.setItem(THEME_STORAGE_KEY, JSON.stringify({ preference: nextPreference, layout: nextLayout, rollbackStack: nextRollbacks }));
  }

  function saveStudio() {
    const result = applyPreference(preference, draftPreference);
    setPreference(result.next);
    setLayout(draftLayout);
    const nextRollbacks = [result.rollback, ...rollbackStack].slice(0, 6);
    setRollbackStack(nextRollbacks);
    persist(result.next, draftLayout, nextRollbacks);
    setPanel(null);
    setToast(`UI saved · revision ${result.next.revision}`);
  }

  function rollbackLast() {
    const [point, ...rest] = rollbackStack;
    if (!point) {
      setToast("No rollback point available");
      return;
    }
    const next = validatePreference(point.preference);
    setPreference(next);
    setDraftPreference(next);
    setRollbackStack(rest);
    persist(next, layout, rest);
    setToast("Previous UI state restored");
  }

  function resetLayout() {
    setDraftLayout(DEFAULT_LAYOUT);
    setToast("Layout reset for preview");
  }

  function updateLayout(key: LayoutKey, patch: Partial<LayoutOffsets[LayoutKey]>) {
    setDraftLayout((current) => ({ ...current, [key]: { ...current[key], ...patch } }));
  }

  function onLayoutPointerDown(key: LayoutKey, event: ReactPointerEvent<HTMLButtonElement>) {
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
        setToast("Image imported · accent sampled");
      };
      image.src = source;
    };
    reader.readAsDataURL(file);
  }

  const shellStyle = { "--ui-contrast": profile.adjustments.contrast } as CSSProperties;
  const topbarStyle = { translate: `${layout.topbar.x}px ${layout.topbar.y}px` } as CSSProperties;
  const centerStyle = { translate: `calc(-50% + ${layout.center.x}px) calc(-50% + ${layout.center.y}px)` } as CSSProperties;
  const seedStyle = { left: `calc(50% + ${layout.seed.x}px)`, bottom: `calc(12.5% + ${layout.seed.y}px)` } as CSSProperties;
  const railStyle = { right: `calc(25px - ${layout.rail.x}px)`, top: `calc(50% + ${layout.rail.y}px)` } as CSSProperties;
  const statusStyle = { left: `calc(22px + ${layout.status.x}px)`, bottom: `calc(18px - ${layout.status.y}px)` } as CSSProperties;

  if (!hydrated) return <div className="world-loading" aria-label="Loading Ultra Brain"><div className="loading-mark" /><p>Opening Ultra Brain</p><span className="loading-line" /></div>;

  return (
    <main className="world-shell" aria-label="Ultra Brain" style={shellStyle}>
      <img className={`world-art ${loaded ? "is-loaded" : ""}`} src="/ultra-brain-world.png" alt="World tree with a central sun sphere and OS Ecosystem seed" onLoad={() => setLoaded(true)} />
      {customBackground && <div className="custom-world-art" style={{ backgroundImage: `url(${customBackground})` }} aria-hidden="true" />}
      <div className="world-vignette" aria-hidden="true" />
      <div className="world-texture" aria-hidden="true" />

      <header className="orientation-bar" style={topbarStyle}>
        <div className="topbar-left">
          <a className="brand" href="#ultra-brain" aria-label="Ultra Brain home">
            <span className="brand-sigil" aria-hidden="true">✦</span>
            <span><strong>Ultra Brain</strong><small>v0.92 · Official UI</small></span>
          </a>
          <button className="studio-launch" type="button" onClick={() => openStudio("themes")} aria-label="Open UI Studio">
            <span aria-hidden="true">⌘</span><span><strong>UI Studio</strong><small>Change UI</small></span>
          </button>
        </div>
        <nav className="world-path" aria-label="Current location"><span>Ultra Brain</span><i>/</i><span aria-current="page">OS Ecosystem</span></nav>
        <div className="top-actions">
          <button className="icon-button" type="button" onClick={() => setPanel("notifications")} aria-label="Open notifications">◌<span className="notice-dot" /></button>
          <button className="icon-button" type="button" onClick={() => openStudio("preview")} aria-label="Open UI preview">◈</button>
        </div>
      </header>

      <section id="ultra-brain" className="world-center" style={centerStyle} aria-labelledby="ultra-brain-title">
        <p className="eyebrow">OFFICIAL WORLD · REVISION {activePreference.revision}</p>
        <span className="title-rule title-rule-top" aria-hidden="true" />
        <h1 id="ultra-brain-title">Ultra Brain</h1>
        <span className="title-rule" aria-hidden="true" />
        <p className="world-status"><span className="health-dot" />Healthy <b>·</b> Official UI</p>
      </section>

      <a className="ecosystem-seed" style={seedStyle} href={OS_ECOSYSTEM_URL} target="_blank" rel="noreferrer" aria-label="Open OS Ecosystem in a new tab">
        <span className="seed-aura" aria-hidden="true" />
        <span className="seed-copy"><small>REGISTERED SYSTEM</small><strong>OS Ecosystem</strong><em>v0.74 · Healthy</em><span className="seed-action">Enter <b>↗</b></span></span>
      </a>
      <img className="world-focus-art" src="/ultra-brain-world.png" alt="" aria-hidden="true" />

      <nav className="world-rail" style={railStyle} aria-label="System navigation">
        <a className="rail-item is-current" href={OS_ECOSYSTEM_URL} target="_blank" rel="noreferrer" aria-label="Open OS Ecosystem"><b>⌂</b><span>OS Ecosystem</span></a>
        <span className="rail-line" aria-hidden="true" />
        <button className="rail-item rail-studio" type="button" onClick={() => openStudio("propagation")} aria-label="Open propagation controls"><b>↯</b><span>Propagation</span></button>
      </nav>

      <aside className="status-dock" style={statusStyle} aria-label="System status">
        <div><span className="health-dot" /> <strong>Healthy</strong></div><i /><span>OS Ecosystem connected</span><i /><span>v0.92</span><button type="button" onClick={() => openStudio("preview")}>Preview</button>
      </aside>

      {panel === "notifications" && <section className="notice-panel floating-panel" aria-label="Notifications">
        <div className="panel-heading"><div><small>SYSTEM NOTICES</small><h2>All clear</h2></div><button type="button" onClick={closePanel} aria-label="Close notifications">×</button></div>
        <div className="notice-card"><span className="health-dot" /><div><strong>OS Ecosystem is healthy</strong><p>The registered child system is connected and ready to enter.</p></div></div>
        <p className="empty-note">No unresolved UI or propagation alerts.</p>
      </section>}

      {panel === "studio" && <>
        <div className="drawer-scrim" onClick={closePanel} aria-hidden="true" />
        <aside className="settings-drawer is-open" aria-label="UI Studio">
          <div className="drawer-topline"><span className="eyebrow">OFFICIAL UI STUDIO</span><button type="button" onClick={closePanel} aria-label="Close UI Studio">×</button></div>
          <h2>Shape the world</h2>
          <p className="drawer-intro">Preview visual changes in place, then save a governed UI revision. Changes stay inside Ultra Brain until you confirm.</p>
          <div className="studio-tabs" role="tablist" aria-label="UI Studio sections">
            {(["themes", "layout", "propagation", "preview"] as StudioTab[]).map((tab) => <button key={tab} type="button" role="tab" aria-selected={studioTab === tab} className={studioTab === tab ? "is-selected" : ""} onClick={() => setStudioTab(tab)}>{tab === "themes" ? "Theme" : tab === "layout" ? "Layout" : tab === "propagation" ? "Propagation" : "Preview"}</button>)}
          </div>

          {studioTab === "themes" && <div className="studio-pane">
            <fieldset><legend>Theme profile</legend><div className="theme-grid">{themeNames.map((theme) => { const item = themeRegistry[theme]; return <button key={theme} type="button" className={activePreference.theme === theme ? "is-selected" : ""} onClick={() => selectTheme(theme)}><span className={`theme-preview ${theme}`} /><strong>{item.label}</strong><small>{item.description}</small></button>; })}</div></fieldset>
            <fieldset><legend>Accent</legend><div className="accent-row">{ACCENT_SWATCHES.map((accent) => <button key={accent} type="button" className={activePreference.accent.toLowerCase() === accent ? "is-selected" : ""} style={{ "--swatch": accent } as CSSProperties} onClick={() => updateDraft({ accent })} aria-label={`Use accent ${accent}`} />)}<label className="accent-picker" aria-label="Choose custom accent"><input type="color" value={activePreference.accent} onChange={(event) => updateDraft({ accent: event.target.value })} /><span>Custom</span></label></div></fieldset>
            <fieldset><legend>User custom theme</legend><label className="file-drop"><input type="file" accept="image/*" onChange={importBackground} /><span>Import image</span><small>Use your own background and sample its first accent automatically.</small></label>{customBackground && <button className="text-action" type="button" onClick={() => { setCustomBackground(null); setToast("Custom background removed"); }}>Remove imported background</button>}</fieldset>
            <fieldset><legend>Theme preset</legend><div className="preset-row">{Object.values(themePresets).map((preset: { id: string; label: string; description: string }) => <button key={preset.id} type="button" className={activePreference.themePreset === preset.id ? "is-selected" : ""} onClick={() => selectThemePreset(preset.id)}><strong>{preset.label}</strong><small>{preset.description}</small></button>)}</div></fieldset>
            <fieldset><legend>Theme detail adjustments</legend><div className="adjustment-grid">{THEME_ADJUSTMENT_KEYS.map((key: ThemeAdjustmentKey) => { const range = THEME_ADJUSTMENT_RANGES[key]; const value = activePreference.themeAdjustments[key]; return <label key={key}><span>{key === "componentPosition" ? "Component position" : key.charAt(0).toUpperCase() + key.slice(1)}</span><input type="range" min={range.min} max={range.max} step={range.step} value={value} onChange={(event) => updateThemeAdjustment(key, Number(event.target.value))} aria-label={`Adjust ${key}`} /><output>{Number(value).toFixed(range.step < 1 ? 2 : 0)}{range.unit === "x" ? "×" : range.unit}</output></label>; })}</div><small className="field-hint">Adjust presentation tokens without changing the selected world's concept art or illustration style.</small></fieldset>
            <fieldset><legend>Theme package</legend><div className="theme-package-card"><div><span className="detail-swatch" style={{ background: profile.accent }} /><strong>{profile.package.name} · {profile.package.version}</strong></div><p>{profile.package.worldStyle}<br />{profile.package.adjustmentKeys.length} detail controls · import ready · export ready</p></div><div className="package-actions"><label className="package-import"><input type="file" accept="application/json,.json" onChange={importThemePackage} /><span>Import package</span></label><button className="text-action" type="button" onClick={exportThemePackage}>Export package</button></div></fieldset>
            <div className="theme-detail-card"><div><span className="detail-swatch" style={{ background: profile.accent }} /><strong>{themeRegistry[activePreference.theme].label} system</strong></div><p>Background · {profile.mode}<br />Layout · world-first<br />Font · {profile.font.split(",")[0]}<br />Radius · {profile.radius} · {themePresets[activePreference.themePreset]?.label || "Custom"} detail</p></div>
          </div>}

          {studioTab === "layout" && <div className="studio-pane">
            <fieldset><legend>Drag &amp; drop layout editor</legend><div className="layout-stage"><div className="layout-stage-world" aria-hidden="true" />{(Object.keys(LAYOUT_LABELS) as LayoutKey[]).map((key) => <button key={key} type="button" draggable className={`layout-node ${layoutSelection === key ? "is-selected" : ""} layout-${key}`} style={{ transform: `translate(${draftLayout[key].x}px, ${draftLayout[key].y}px)` }} onClick={() => setLayoutSelection(key)} onPointerDown={(event) => onLayoutPointerDown(key, event)} onPointerMove={onLayoutPointerMove} onPointerUp={onLayoutPointerUp} onPointerCancel={onLayoutPointerUp}>{LAYOUT_LABELS[key]}</button>)}</div><small className="field-hint">Drag a node to preview its position. Keyboard sliders below provide precise control.</small></fieldset>
            <fieldset><legend>{LAYOUT_LABELS[layoutSelection]} position</legend><div className="range-row"><label>X <input type="range" min="-80" max="80" value={draftLayout[layoutSelection].x} onChange={(event) => updateLayout(layoutSelection, { x: Number(event.target.value) })} /><output>{draftLayout[layoutSelection].x}px</output></label><label>Y <input type="range" min="-60" max="60" value={draftLayout[layoutSelection].y} onChange={(event) => updateLayout(layoutSelection, { y: Number(event.target.value) })} /><output>{draftLayout[layoutSelection].y}px</output></label></div></fieldset>
            <button className="text-action" type="button" onClick={resetLayout}>Reset all positions</button>
          </div>}

          {studioTab === "propagation" && <div className="studio-pane">
            <div className="propagation-banner"><span className={profile.propagation.status === "locked" ? "lock-state" : "health-dot"} /><div><strong>{profile.propagation.status === "locked" ? "Propagation locked" : profile.propagation.status === "override" ? "Override active" : "Automatic hierarchy propagation"}</strong><small>{profile.propagation.contract} · interface {profile.propagation.interfaceVersion} · revision {propagation.revision}</small></div></div>
            <div className="hierarchy-note"><strong>One source of truth</strong><span>Ultra Brain UI Studio governs every level. Unlocked descendants automatically receive the saved UI payload.</span></div>
            <div className="propagation-hierarchy" aria-label="UI propagation hierarchy">
              {propagation.hierarchy.map((node: { id: string; label: string; kind: string; status: string; automatic: boolean; appliedTargets: string[]; lockedTargets: string[]; overriddenTargets: string[] }, index: number) => {
                const statusLabel = node.status === "source" ? "Source" : node.status === "locked" ? "Locked" : node.status === "override" ? "Override" : "Auto applied";
                return <button key={node.id} type="button" className={`hierarchy-node ${propagationSelection === node.id ? "is-selected" : ""}`} onClick={() => setPropagationSelection(node.id)}>
                  <span className={`hierarchy-index status-${node.status}`}>{index + 1}</span>
                  <span className="hierarchy-copy"><strong>{node.label}</strong><small>{node.kind === "source" ? "UI Studio source" : node.kind === "registered-child" ? "Registered child" : "Downstream target"}</small></span>
                  <em className={`propagation-status status-${node.status}`}>{statusLabel}</em>
                  {index < propagation.hierarchy.length - 1 && <i aria-hidden="true">↓</i>}
                </button>;
              })}
            </div>
            <div className="propagation-editor-card">
              <div className="editor-card-heading"><div><small>SELECTED LEVEL</small><strong>{selectedPropagationNode?.label}</strong></div><span className="auto-apply-badge">{selectedPropagationNode?.kind === "source" ? "Editable source" : "Child editor disabled"}</span></div>
              <p className="field-hint">{selectedPropagationNode?.kind === "source" ? "Edit the source UI here. The saved payload is then offered to every unlocked descendant." : "Managed from Ultra Brain UI Studio. This level cannot edit its own UI."}</p>
              {selectedPropagationNode?.kind !== "source" && <div className="target-grid" aria-label={`Propagation targets for ${selectedPropagationNode?.label}`}>
                {PROPAGATION_TARGETS.map((target: string) => {
                  const locked = (draftPreference.propagationLocks[selectedPropagationNode?.id || ""] || []).includes(target);
                  const overridden = (draftPreference.propagationOverrides[selectedPropagationNode?.id || ""] || []).includes(target);
                  return <div key={target} className={`propagation-target ${locked ? "is-locked" : ""} ${overridden ? "is-overridden" : ""}`}>
                    <span>{PROPAGATION_TARGET_LABELS[target]}</span>
                    <button type="button" className={`target-toggle ${locked ? "is-on" : ""}`} onClick={() => togglePropagationTarget(selectedPropagationNode?.id || "os-ecosystem", "lock", target)} aria-pressed={locked}>Lock</button>
                    <button type="button" className={`target-toggle ${overridden ? "is-on" : ""}`} onClick={() => togglePropagationTarget(selectedPropagationNode?.id || "os-ecosystem", "override", target)} aria-pressed={overridden}>Override</button>
                  </div>;
                })}
              </div>}
              {selectedPropagationNode?.kind === "source" && <div className="source-target-summary"><span className="health-dot" /><strong>All {PROPAGATION_TARGETS.length} targets originate here</strong><small>Theme, visual tokens, layout, component geometry, visibility and motion.</small></div>}
            </div>
            <div className="setting-row"><div><strong>OS Ecosystem lock</strong><small>Keep the selected global UI payload from reaching the registered child.</small></div><button className={`switch ${draftPreference.osEcosystemLocked ? "is-on" : ""}`} type="button" role="switch" aria-checked={draftPreference.osEcosystemLocked} onClick={toggleEcosystemLock}><span /></button></div>
            <div className="setting-row"><div><strong>OS Ecosystem override</strong><small>Preview a governed exception while keeping child ownership independent.</small></div><button className={`switch ${draftPreference.propagationOverride ? "is-on" : ""}`} type="button" role="switch" aria-checked={draftPreference.propagationOverride} onClick={toggleEcosystemOverride}><span /></button></div>
            <div className="propagation-payload"><div><small>PROPAGATION PREVIEW PAYLOAD</small><strong>{themeRegistry[draftPreference.theme].label} · revision {draftPreference.revision}</strong></div><span>{selectedPropagationNode?.appliedTargets?.length || 0} auto applied · {selectedPropagationNode?.lockedTargets?.length || 0} locked · {selectedPropagationNode?.overriddenTargets?.length || 0} override</span></div>
          </div>}

          {studioTab === "preview" && <div className="studio-pane">
            <div className="preview-mode"><div><strong>Live preview</strong><small>Draft changes are visible behind this studio.</small></div><span className="preview-pill">ON</span></div>
            <div className="compare-grid"><div className="compare-card"><small>SAVED</small><strong>Revision {preference.revision}</strong><span>{themeRegistry[preference.theme].label}</span><i style={{ background: preference.accent }} /></div><div className="compare-arrow">→</div><div className="compare-card is-draft"><small>PREVIEW</small><strong>Revision {preference.revision + 1}</strong><span>{themeRegistry[draftPreference.theme].label}</span><i style={{ background: draftPreference.accent }} /></div></div>
            <div className="impact-card"><div><span className="health-dot" /><strong>Compatibility check</strong></div><p>Ultra Brain <b>→</b> OS Ecosystem</p><small>Only UI tokens and governed presentation preferences are affected. Runtime ownership remains independent.</small></div>
            <button className="rollback-action" type="button" onClick={rollbackLast} disabled={!rollbackStack.length}>Rollback last saved revision {rollbackStack.length ? `(${rollbackStack.length})` : ""}</button>
          </div>}

          <div className="drawer-actions"><button className="secondary-action" type="button" onClick={closePanel}>Discard</button><button className="primary-action" type="button" onClick={saveStudio}>Save UI revision</button></div>
        </aside>
      </>}

      {toast && <div className="toast" role="status"><span className="health-dot" />{toast}</div>}
    </main>
  );
}
