"use client";

import type { ChangeEvent, CSSProperties, PointerEvent as ReactPointerEvent } from "react";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  THEME_STORAGE_KEY,
  applyPreference,
  createRollbackPoint,
  defaultPreference,
  resolveThemeProfile,
  themeNames,
  themeRegistry,
  validatePreference,
} from "../lib/theme-engine";

const OS_ECOSYSTEM_URL = "https://8javbq85jtappi6tkdhkt7g.streamlit.app/";
const ACCENT_SWATCHES = ["#c8a55d", "#83aa8c", "#56b8cf", "#9d91e8", "#df86b8", "#e87943", "#d2d7d0"];
const PROPAGATION_CHAIN = ["Ultra Brain", "OS Ecosystem", "Living OS", "Universal Learning Engine", "Future Projects"];
const LAYOUT_LABELS = { topbar: "Topbar", center: "World identity", seed: "OS Entry", rail: "Navigation rail", status: "Status dock" } as const;

type Panel = null | "studio" | "notifications";
type StudioTab = "themes" | "layout" | "propagation" | "preview";
type LayoutKey = keyof typeof LAYOUT_LABELS;
type LayoutOffsets = Record<LayoutKey, { x: number; y: number }>;
type Preference = ReturnType<typeof validatePreference>;
type RollbackPoint = ReturnType<typeof createRollbackPoint>;

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

  function selectTheme(theme: string) {
    updateDraft({ theme: theme as Preference["theme"], accent: themeRegistry[theme].accent });
    setToast(`${themeRegistry[theme].label} preview`);
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

  const shellStyle = { "--ui-contrast": profile.contrast } as CSSProperties;
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
            <span><strong>Ultra Brain</strong><small>v0.9 · Official UI</small></span>
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
        <div><span className="health-dot" /> <strong>Healthy</strong></div><i /><span>OS Ecosystem connected</span><i /><span>v0.9</span><button type="button" onClick={() => openStudio("preview")}>Preview</button>
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
            <div className="theme-detail-card"><div><span className="detail-swatch" style={{ background: profile.accent }} /><strong>{themeRegistry[activePreference.theme].label} system</strong></div><p>Background · {profile.mode}<br />Layout · world-first<br />Font · {profile.font.split(",")[0]}<br />Radius · {profile.radius} · Lighting tuned</p></div>
          </div>}

          {studioTab === "layout" && <div className="studio-pane">
            <fieldset><legend>Drag &amp; drop layout editor</legend><div className="layout-stage"><div className="layout-stage-world" aria-hidden="true" />{(Object.keys(LAYOUT_LABELS) as LayoutKey[]).map((key) => <button key={key} type="button" draggable className={`layout-node ${layoutSelection === key ? "is-selected" : ""} layout-${key}`} style={{ transform: `translate(${draftLayout[key].x}px, ${draftLayout[key].y}px)` }} onClick={() => setLayoutSelection(key)} onPointerDown={(event) => onLayoutPointerDown(key, event)} onPointerMove={onLayoutPointerMove} onPointerUp={onLayoutPointerUp} onPointerCancel={onLayoutPointerUp}>{LAYOUT_LABELS[key]}</button>)}</div><small className="field-hint">Drag a node to preview its position. Keyboard sliders below provide precise control.</small></fieldset>
            <fieldset><legend>{LAYOUT_LABELS[layoutSelection]} position</legend><div className="range-row"><label>X <input type="range" min="-80" max="80" value={draftLayout[layoutSelection].x} onChange={(event) => updateLayout(layoutSelection, { x: Number(event.target.value) })} /><output>{draftLayout[layoutSelection].x}px</output></label><label>Y <input type="range" min="-60" max="60" value={draftLayout[layoutSelection].y} onChange={(event) => updateLayout(layoutSelection, { y: Number(event.target.value) })} /><output>{draftLayout[layoutSelection].y}px</output></label></div></fieldset>
            <button className="text-action" type="button" onClick={resetLayout}>Reset all positions</button>
          </div>}

          {studioTab === "propagation" && <div className="studio-pane">
            <div className="propagation-banner"><span className={profile.propagation.status === "locked" ? "lock-state" : "health-dot"} /><div><strong>{profile.propagation.status === "locked" ? "Propagation locked" : profile.propagation.status === "override" ? "Override active" : "Compatible propagation"}</strong><small>{profile.propagation.contract} · interface {profile.propagation.interfaceVersion}</small></div></div>
            <div className="propagation-chain">{PROPAGATION_CHAIN.map((node, index) => <div key={node} className="chain-node"><span className={index < 2 ? "is-active" : ""}>{index + 1}</span><div><strong>{node}</strong><small>{index === 0 ? "Source" : index === 1 ? "Registered child" : "Future target"}</small></div>{index < PROPAGATION_CHAIN.length - 1 && <i aria-hidden="true">↓</i>}</div>)}</div>
            <div className="setting-row"><div><strong>Propagation lock</strong><small>Keep global UI changes from reaching OS Ecosystem.</small></div><button className={`switch ${draftPreference.osEcosystemLocked ? "is-on" : ""}`} type="button" role="switch" aria-checked={draftPreference.osEcosystemLocked} onClick={() => updateDraft({ osEcosystemLocked: !draftPreference.osEcosystemLocked })}><span /></button></div>
            <div className="setting-row"><div><strong>Override lock</strong><small>Explicitly preview a governed exception without changing child ownership.</small></div><button className={`switch ${draftPreference.propagationOverride ? "is-on" : ""}`} type="button" role="switch" aria-checked={draftPreference.propagationOverride} onClick={() => updateDraft({ propagationOverride: !draftPreference.propagationOverride })}><span /></button></div>
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
