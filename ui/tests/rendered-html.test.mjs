import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";
import test from "node:test";

const templateRoot = new URL("../", import.meta.url);
const previewRoot = new URL("../app/_sites-preview/", import.meta.url);

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);
  return worker.fetch(
    new Request("http://localhost/", { headers: { accept: "text/html" } }),
    { ASSETS: { fetch: async () => new Response("Not found", { status: 404 }) } },
    { waitUntil() {}, passThroughOnException() {} },
  );
}

test("server renders the Ultra Brain v0.984 UI Studio world UI", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);
  const html = await response.text();
  assert.match(html, /<title>Ultra Brain v0\.984 .* Ultra Brain<\/title>/i);
  assert.match(html, /Ultra Brain/);
  assert.doesNotMatch(html, /Your site is taking shape|Building your site|codex-preview|react-loading-skeleton/i);
});

test("the production entry has no disposable starter surface", async () => {
  const [page, layout, packageJson, shell, canvas, styles] = await Promise.all([
    readFile(new URL("../app/page.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/layout.tsx", import.meta.url), "utf8"),
    readFile(new URL("../package.json", import.meta.url), "utf8"),
    readFile(new URL("../app/ultra-brain-shell.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/canvas-editor-v983.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/globals.css", import.meta.url), "utf8"),
  ]);
  assert.match(page, /<UltraBrainShell \/>/);
  assert.match(shell, /ultra-brain-world\.png/);
  assert.match(shell, /UI 스튜디오 열기/);
  assert.match(shell, /worldEngine/);
  assert.match(shell, /CanvasEditor/);
  assert.match(shell, /PROPAGATION_TARGET_LABELS/);
  assert.match(shell, /THEME_ADJUSTMENT_LABELS/);
  assert.match(shell, /UI_LOCK_KEYS/);
  assert.match(shell, /type StudioTab = "adjustments" \| "themes" \| "custom" \| "ui-lock"/);
  assert.match(shell, /type Panel = null \| "studio" \| "notifications"/);
  assert.match(shell, /\["adjustments", "themes", "custom", "ui-lock"\] as StudioTab\[\]/);
  assert.equal((shell.match(/studioTab === "ui-lock" &&/g) || []).length, 1);
  assert.match(shell, /"기본 조정"[\s\S]*"테마"[\s\S]*"사용자 지정 UI"[\s\S]*"UI 잠금"/);
  assert.doesNotMatch(shell, /\["adjustments", "themes", "custom", "layout", "propagation"\]/);
  for (const key of ["theme", "world", "revision", "accent", "density", "motion", "themePreset", "scope", "layout", "uiLocks", "propagationTargets", "propagationLocks", "propagationOverrides", "osEcosystemLocked", "propagationOverride", "contract", "interface", "target", "propagation", "os_locked", "os_override", "applied_targets", "locked_targets", "overridden_targets"]) {
    assert.match(shell, new RegExp(`params\\.set\\("${key}"`), `missing OS Ecosystem contract field: ${key}`);
  }
  assert.match(shell, /params\.set\("contract", "ultra-brain\.ui\/v1"\)/);
  assert.match(shell, /params\.set\("interface", "1\.0"\)/);
  assert.match(shell, /params\.set\("target", "os-ecosystem"\)/);
  assert.match(shell, /const propagationStatus = osLocked && osOverride \? "locked-override" : osLocked \? "locked" : osOverride \? "override" : "automatic"/);
  assert.match(shell, /const osLocked = preference\.osEcosystemLocked/);
  assert.match(shell, /const osOverride = preference\.propagationOverride/);
  assert.match(shell, /resolvePropagation\(preference\)\.hierarchy\.find/);
  assert.match(shell, /params\.set\("applied_targets", appliedTargets\.join\(","\)\)/);
  assert.match(shell, /params\.set\("locked_targets", lockedTargets\.join\(","\)\)/);
  assert.match(shell, /params\.set\("overridden_targets", overriddenTargets\.join\(","\)\)/);
  assert.match(shell, /for \(const key of THEME_ADJUSTMENT_KEYS\) params\.set\(key, String\(preference\.themeAdjustments\[key\]\)\)/);
  assert.match(shell, /buildEcosystemUrl\(preference, resolveThemeProfile\(preference\)\.worldEngine\.id, layout\), \[preference, layout\]/);
  assert.match(shell, /function toCompactJson/);
  assert.match(shell, /setDraftCustomBackground\(customBackground\)/);
  assert.match(shell, /const nextBackground = draftCustomBackground/);
  assert.match(shell, /setCustomBackground\(nextBackground\)/);
  assert.match(canvas, /UI\/UX 도구함/);
  assert.match(canvas, /그리기용 도구함/);
  assert.equal((canvas.match(/toolbox-section v983-toolbox/g) || []).length, 2);
  assert.match(canvas, /aria-expanded=\{uiOpen\}/);
  assert.match(canvas, /aria-expanded=\{drawingOpen\}/);
  assert.match(canvas, /UiTool \| null/);
  assert.match(canvas, /DrawTool \| null/);
  assert.match(canvas, /current === next \? null : next/);
  assert.doesNotMatch(canvas, /canvas-header-actions|canvas-toolbar|builder-property-panel|v983-quick-settings/);
  assert.match(canvas, /pointerType === "pen"/);
  assert.match(canvas, /getCoalescedEvents/);
  assert.match(canvas, /pressure: normalPressure/);
  assert.match(canvas, /tiltX: nativeEvent\.tiltX/);
  assert.match(canvas, /globalCompositeOperation = node\.tool === "eraser" \? "destination-out"/);
  assert.match(canvas, /createRadialGradient/);
  assert.match(canvas, /floodFill/);
  assert.match(canvas, /removeImageBackground/);
  assert.match(canvas, /가로 자르기/);
  assert.match(canvas, /합성 방식/);
  assert.match(canvas, /캔버스 이동/);
  assert.match(canvas, /renderContent\(canvas, nodesRef\.current, backgroundRef\.current, null, false\)/);
  assert.match(canvas, /contentRef/);
  assert.match(canvas, /overlayRef/);
  assert.match(shell, /studioTab !== "custom"/);
  assert.match(canvas, /되돌리기/);
  assert.match(canvas, /그림 가져오기/);
  assert.doesNotMatch(styles, /ecosystem-seed:hover ~ \.world-focus-art/);
  assert.match(styles, /\.world-ambient \{[^}]*background: none;[^}]*opacity: 0 !important;[^}]*animation: none !important;/);
  assert.match(canvas, /사용자 UI로 적용/);
  assert.match(canvas, /변경 기록/);
  assert.match(canvas, /rollback/);
  assert.match(layout, /Ultra Brain v0\.984/);
  assert.doesNotMatch(layout, /codex-preview|_sites-preview|Starter Project/);
  assert.doesNotMatch(packageJson, /react-loading-skeleton/);
  await assert.rejects(access(new URL("public/_sites-preview", templateRoot)));
  await assert.rejects(access(previewRoot));
});

test("every official world uses a full-screen widescreen image", async () => {
  const assets = [
    "ultra-brain-world.png", "world-light.png", "world-dark.png",
    "world-universe.png", "world-galaxy.png", "world-ecosystem.png",
    "world-ocean.png", "world-grassland.png", "world-lava.png",
    "world-minimal.png", "world-paper.png", "world-archive.png", "world-calm.png",
  ];
  for (const name of assets) {
    const png = await readFile(new URL(`../public/${name}`, import.meta.url));
    assert.equal(png.toString("ascii", 1, 4), "PNG", `${name} must be a PNG`);
    const width = png.readUInt32BE(16);
    const height = png.readUInt32BE(20);
    assert.ok(width >= 1671, `${name} is too narrow for the production stage`);
    assert.equal(height, 941, `${name} must share the production stage height`);
  }
});
