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

test("server renders the Ultra Brain v0.97 Professional UI Studio world UI", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);
  const html = await response.text();
  assert.match(html, /<title>Ultra Brain v0\.97 .* Ultra Brain<\/title>/i);
  assert.match(html, /Ultra Brain/);
  assert.doesNotMatch(html, /Your site is taking shape|Building your site|codex-preview|react-loading-skeleton/i);
});

test("the production entry has no disposable starter surface", async () => {
  const [page, layout, packageJson, shell, canvas, styles] = await Promise.all([
    readFile(new URL("../app/page.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/layout.tsx", import.meta.url), "utf8"),
    readFile(new URL("../package.json", import.meta.url), "utf8"),
    readFile(new URL("../app/ultra-brain-shell.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/canvas-editor.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/globals.css", import.meta.url), "utf8"),
  ]);
  assert.match(page, /<UltraBrainShell \/>/);
  assert.match(shell, /ultra-brain-world\.png/);
  assert.match(shell, /Open UI Studio/);
  assert.match(shell, /worldEngine/);
  assert.match(shell, /CanvasEditor/);
  assert.match(shell, /PROPAGATION_TARGET_LABELS/);
  assert.match(shell, /THEME_ADJUSTMENT_LABELS/);
  assert.match(shell, /UI_LOCK_KEYS/);
  assert.match(canvas, /UI Builder/);
  assert.match(canvas, /초보자용 UI 제작/);
  assert.match(canvas, /터치펜 도구함/);
  assert.match(canvas, /마우스 도구함/);
  assert.match(canvas, /AI 이미지 가져오기/);
  assert.doesNotMatch(styles, /ecosystem-seed:hover ~ \.world-focus-art/);
  assert.match(canvas, /Asset Library/);
  assert.match(canvas, /Revision History/);
  assert.match(canvas, /rollbackRevision/);
  assert.match(layout, /Ultra Brain v0\.97/);
  assert.doesNotMatch(layout, /codex-preview|_sites-preview|Starter Project/);
  assert.doesNotMatch(packageJson, /react-loading-skeleton/);
  await assert.rejects(access(new URL("public/_sites-preview", templateRoot)));
  await assert.rejects(access(previewRoot));
});
