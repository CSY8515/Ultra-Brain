"use client";

import type { ChangeEvent, PointerEvent as ReactPointerEvent } from "react";
import { useCallback, useEffect, useRef, useState } from "react";

const CANVAS_WIDTH = 1200;
const CANVAS_HEIGHT = 760;
const CUSTOM_REGISTRY_KEY = "ultra-brain.user-custom/v1";

type Tool = "select" | "pen" | "brush" | "eraser" | "line" | "rectangle" | "circle" | "triangle" | "text" | "fill" | "gradient";
type BuilderTool = "select" | "frame" | "container" | "text" | "button" | "card" | "panel" | "widget" | "navigation" | "image" | "icon" | "shape" | "drawing";
type Point = { x: number; y: number };
type CanvasNode = {
  id: string; name: string; kind: "stroke" | "shape" | "text" | "image" | "component";
  tool?: Tool; points?: Point[]; start?: Point; end?: Point; text?: string; component?: string; src?: string;
  x?: number; y?: number; width?: number; height?: number; rotation?: number; group?: string;
  color: string; size: number; opacity: number; visible: boolean; locked: boolean;
};
type UserCustomTheme = { id: string; name: string; baseTheme: string; preview: string; createdAt: string; status: "draft" | "active" | "archived" };
type AssetRecord = { id: string; name: string; type: "image" | "drawing" | "official"; src?: string; tags: string[]; favorite: boolean; createdAt: string };
type RevisionRecord = { id: string; label: string; createdAt: string; nodes: CanvasNode[]; background: string; source: "draft" | "manual" | "applied" | "rollback"; validation: "통과" | "검토 필요" };

type CanvasEditorProps = { baseTheme: string; onUseTheme: (preview: string, name: string) => void; onToast: (message: string) => void };

function makeId(prefix: string) { return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`; }

function getPoint(event: ReactPointerEvent<HTMLCanvasElement>): Point {
  const rect = event.currentTarget.getBoundingClientRect();
  return { x: Math.max(0, Math.min(CANVAS_WIDTH, ((event.clientX - rect.left) / rect.width) * CANVAS_WIDTH)), y: Math.max(0, Math.min(CANVAS_HEIGHT, ((event.clientY - rect.top) / rect.height) * CANVAS_HEIGHT)) };
}

const COMPONENTS: { id: BuilderTool; label: string }[] = [
  { id: "frame", label: "Frame" }, { id: "container", label: "Container" }, { id: "text", label: "텍스트" }, { id: "button", label: "버튼" },
  { id: "card", label: "카드" }, { id: "panel", label: "패널" }, { id: "widget", label: "위젯" }, { id: "navigation", label: "탐색" },
  { id: "icon", label: "아이콘" }, { id: "shape", label: "도형" },
];
const COMPONENT_STATES = ["Default", "Hover", "Focus", "Active", "Selected", "Disabled", "Loading", "Error", "Success"];

export function CanvasEditor({ baseTheme, onUseTheme, onToast }: CanvasEditorProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const nodesRef = useRef<CanvasNode[]>([]);
  const activeRef = useRef<{ tool: Tool; start: Point; points: Point[] } | null>(null);
  const dragRef = useRef<{ id: string; start: Point; origin: Point } | null>(null);
  const copyRef = useRef<CanvasNode[]>([]);
  const [nodes, setNodes] = useState<CanvasNode[]>([]);
  const [history, setHistory] = useState<CanvasNode[][]>([]);
  const [redoStack, setRedoStack] = useState<CanvasNode[][]>([]);
  const [builderMode, setBuilderMode] = useState<"builder" | "drawing">("builder");
  const [builderTool, setBuilderTool] = useState<BuilderTool>("select");
  const [tool, setTool] = useState<Tool>("pen");
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [color, setColor] = useState("#c8a55d");
  const [size, setSize] = useState(8);
  const [opacity, setOpacity] = useState(1);
  const [background, setBackground] = useState("#061011");
  const [grid, setGrid] = useState(true);
  const [snap, setSnap] = useState(false);
  const [safeArea, setSafeArea] = useState(true);
  const [zoom, setZoom] = useState(1);
  const [previewMode, setPreviewMode] = useState<"desktop" | "tablet" | "mobile" | "full">("desktop");
  const [textValue, setTextValue] = useState("Ultra Brain");
  const [assetName, setAssetName] = useState("가져온 이미지");
  const [customName, setCustomName] = useState("My Custom World");
  const [customThemes, setCustomThemes] = useState<UserCustomTheme[]>([]);
  const [assets, setAssets] = useState<AssetRecord[]>([]);
  const [assetSearch, setAssetSearch] = useState("");
  const [componentState, setComponentState] = useState("Default");
  const [revisions, setRevisions] = useState<RevisionRecord[]>([]);
  const [revisionLabel, setRevisionLabel] = useState("UI 변경");
  const [draftSavedAt, setDraftSavedAt] = useState<string | null>(null);

  useEffect(() => {
    try {
      const custom = JSON.parse(window.localStorage.getItem(CUSTOM_REGISTRY_KEY) || "[]");
      const storedAssets = JSON.parse(window.localStorage.getItem(`${CUSTOM_REGISTRY_KEY}/assets`) || "[]");
      const storedRevisions = JSON.parse(window.localStorage.getItem(`${CUSTOM_REGISTRY_KEY}/revisions`) || "[]");
      if (Array.isArray(custom)) setCustomThemes(custom);
      if (Array.isArray(storedAssets)) setAssets(storedAssets);
      if (Array.isArray(storedRevisions)) setRevisions(storedRevisions);
    } catch { /* local workspace data is optional */ }
  }, []);

  const drawScene = useCallback((nextNodes = nodesRef.current, draft?: CanvasNode) => {
    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d");
    if (!canvas || !context) return;
    context.clearRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
    if (background.startsWith("linear-gradient")) {
      const gradient = context.createLinearGradient(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
      gradient.addColorStop(0, color); gradient.addColorStop(1, "#050909"); context.fillStyle = gradient;
    } else context.fillStyle = background;
    context.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
    for (const node of [...nextNodes, ...(draft ? [draft] : [])]) {
      if (!node.visible) continue;
      context.save(); context.globalAlpha = node.opacity;
      const x = node.x || node.start?.x || node.points?.[0]?.x || 0;
      const y = node.y || node.start?.y || node.points?.[0]?.y || 0;
      const width = node.width || Math.max(34, Math.abs((node.end?.x || x) - x));
      const height = node.height || Math.max(34, Math.abs((node.end?.y || y) - y));
      if (node.kind === "image" && node.src) {
        const image = new Image(); image.onload = () => { context.save(); context.globalAlpha = node.opacity; context.translate(x + width / 2, y + height / 2); context.rotate(((node.rotation || 0) * Math.PI) / 180); context.drawImage(image, -width / 2, -height / 2, width, height); context.restore(); }; image.src = node.src;
      } else if (node.kind === "text") {
        context.fillStyle = node.color; context.font = `600 ${Math.max(12, node.size * 4)}px Georgia, serif`; context.fillText(node.text || "텍스트", x, y);
      } else if (node.kind === "component") {
        context.translate(x + width / 2, y + height / 2); context.rotate(((node.rotation || 0) * Math.PI) / 180); context.translate(-(x + width / 2), -(y + height / 2));
        const active = componentState === "Hover" || componentState === "Active" || componentState === "Selected";
        context.fillStyle = active ? "rgba(200,165,93,.22)" : "rgba(6,18,18,.86)"; context.strokeStyle = node.color; context.lineWidth = Math.max(1, node.size / 2);
        context.beginPath(); context.roundRect(x, y, width, height, 12); context.fill(); context.stroke();
        context.fillStyle = node.color; context.font = `600 ${Math.max(14, node.size * 2)}px Pretendard, sans-serif`; context.fillText(node.component || node.name, x + 18, y + height / 2 + 6);
      } else if (node.kind === "shape") {
        const start = node.start || { x, y }; const end = node.end || { x: x + width, y: y + height }; context.strokeStyle = node.color; context.lineWidth = node.size; context.lineCap = "round"; context.beginPath();
        if (node.tool === "line") { context.moveTo(start.x, start.y); context.lineTo(end.x, end.y); }
        else if (node.tool === "rectangle") context.rect(start.x, start.y, end.x - start.x, end.y - start.y);
        else if (node.tool === "circle") context.arc(start.x, start.y, Math.hypot(end.x - start.x, end.y - start.y), 0, Math.PI * 2);
        else { context.moveTo(start.x, end.y); context.lineTo((start.x + end.x) / 2, start.y); context.lineTo(end.x, end.y); context.closePath(); }
        context.stroke();
      } else if (node.kind === "stroke" && node.points?.length) {
        context.globalCompositeOperation = node.tool === "eraser" ? "destination-out" : "source-over"; context.strokeStyle = node.color; context.lineWidth = node.tool === "brush" ? node.size * 2.2 : node.size; context.lineCap = "round"; context.lineJoin = "round"; context.beginPath();
        node.points.forEach((point, index) => index ? context.lineTo(point.x, point.y) : context.moveTo(point.x, point.y)); context.stroke();
      }
      context.restore();
    }
    context.save();
    if (grid) { context.strokeStyle = "rgba(200,165,93,.12)"; context.lineWidth = 1; for (let x = 0; x <= CANVAS_WIDTH; x += 40) { context.beginPath(); context.moveTo(x, 0); context.lineTo(x, CANVAS_HEIGHT); context.stroke(); } for (let y = 0; y <= CANVAS_HEIGHT; y += 40) { context.beginPath(); context.moveTo(0, y); context.lineTo(CANVAS_WIDTH, y); context.stroke(); } }
    if (safeArea) { context.setLineDash([10, 8]); context.strokeStyle = "rgba(240,213,138,.64)"; context.strokeRect(64, 52, CANVAS_WIDTH - 128, CANVAS_HEIGHT - 104); context.setLineDash([]); }
    context.restore();
  }, [background, color, componentState, grid, safeArea]);

  useEffect(() => { nodesRef.current = nodes; drawScene(nodes); }, [nodes, drawScene]);

  function commitNodes(next: CanvasNode[]) { setHistory((current) => [...current, nodesRef.current].slice(-40)); setRedoStack([]); nodesRef.current = next; setNodes(next); drawScene(next); }
  function undo() { const previous = history.at(-1); if (!previous) return; setRedoStack((current) => [...current, nodesRef.current]); setHistory((current) => current.slice(0, -1)); nodesRef.current = previous; setNodes(previous); }
  function redo() { const next = redoStack.at(-1); if (!next) return; setHistory((current) => [...current, nodesRef.current]); setRedoStack((current) => current.slice(0, -1)); nodesRef.current = next; setNodes(next); }
  function selectedNodes() { return nodesRef.current.filter((node) => selectedIds.includes(node.id)); }

  function addBuilderNode(kind: BuilderTool, point: Point = { x: 120 + (nodesRef.current.length % 3) * 280, y: 100 + (nodesRef.current.length % 4) * 120 }) {
    if (["select", "drawing", "image"].includes(kind)) return;
    const labels: Record<string, string> = { frame: "Frame", container: "Container", text: textValue || "텍스트", button: "버튼", card: "카드", panel: "패널", widget: "위젯", navigation: "탐색 버튼", icon: "아이콘", shape: "도형" };
    const width = kind === "frame" || kind === "container" ? 430 : kind === "card" || kind === "panel" ? 300 : 240;
    const height = kind === "frame" || kind === "container" ? 220 : kind === "card" || kind === "panel" ? 150 : 66;
    const node: CanvasNode = { id: makeId(kind), name: labels[kind] || kind, kind: kind === "text" ? "text" : kind === "shape" ? "shape" : "component", tool: kind === "shape" ? "rectangle" : undefined, text: kind === "text" ? textValue || "텍스트" : undefined, component: kind === "text" ? undefined : labels[kind], x: point.x, y: point.y, width, height, color, size: 8, opacity, visible: true, locked: false };
    commitNodes([...nodesRef.current, node]); setSelectedIds([node.id]);
  }

  function hitNode(point: Point) {
    return [...nodesRef.current].reverse().find((node) => { const x = node.x || node.start?.x || node.points?.[0]?.x || 0; const y = node.y || node.start?.y || node.points?.[0]?.y || 0; const width = node.width || Math.max(34, Math.abs((node.end?.x || x) - x)); const height = node.height || Math.max(34, Math.abs((node.end?.y || y) - y)); return point.x >= x - 20 && point.x <= x + width + 20 && point.y >= y - 20 && point.y <= y + height + 20; });
  }

  function handlePointerDown(event: ReactPointerEvent<HTMLCanvasElement>) {
    event.currentTarget.setPointerCapture(event.pointerId); const point = getPoint(event);
    if (builderMode === "builder") {
      if (builderTool !== "select") { addBuilderNode(builderTool, point); return; }
      const hit = hitNode(point); const additive = event.shiftKey || event.metaKey || event.ctrlKey;
      if (!hit) { if (!additive) setSelectedIds([]); return; }
      setSelectedIds((current) => additive ? (current.includes(hit.id) ? current.filter((id) => id !== hit.id) : [...current, hit.id]) : [hit.id]);
      if (!hit.locked) dragRef.current = { id: hit.id, start: point, origin: { x: hit.x || hit.start?.x || 0, y: hit.y || hit.start?.y || 0 } }; return;
    }
    if (tool === "select") { const hit = hitNode(point); setSelectedIds(hit ? [hit.id] : []); if (hit && !hit.locked) dragRef.current = { id: hit.id, start: point, origin: { x: hit.x || hit.start?.x || 0, y: hit.y || hit.start?.y || 0 } }; return; }
    if (tool === "fill") { setBackground(color); onToast("배경을 채웠습니다"); return; }
    if (tool === "gradient") { setBackground(`linear-gradient(135deg, ${color}, #050909 72%)`); onToast("그라디언트를 적용했습니다"); return; }
    if (tool === "text") { commitNodes([...nodesRef.current, { id: makeId("text"), name: textValue || "텍스트", kind: "text", text: textValue || "텍스트", x: point.x, y: point.y, color, size, opacity, visible: true, locked: false }]); return; }
    activeRef.current = { tool, start: point, points: [point] };
  }

  function handlePointerMove(event: ReactPointerEvent<HTMLCanvasElement>) {
    if (dragRef.current) { const point = getPoint(event); const dx = point.x - dragRef.current.start.x; const dy = point.y - dragRef.current.start.y; const next = nodesRef.current.map((node) => node.id === dragRef.current?.id && !node.locked ? { ...node, x: dragRef.current.origin.x + dx, y: dragRef.current.origin.y + dy } : node); nodesRef.current = next; setNodes(next); return; }
    const active = activeRef.current; if (!active) return; const point = getPoint(event); active.points.push(snap ? { x: Math.round(point.x / 10) * 10, y: Math.round(point.y / 10) * 10 } : point); const draft: CanvasNode = ["pen", "brush", "eraser"].includes(active.tool) ? { id: "draft", name: "draft", kind: "stroke", tool: active.tool, points: active.points, color, size, opacity, visible: true, locked: false } : { id: "draft", name: "draft", kind: "shape", tool: active.tool, start: active.start, end: point, color, size, opacity, visible: true, locked: false }; drawScene(nodesRef.current, draft);
  }

  function finishPointer(event: ReactPointerEvent<HTMLCanvasElement>) {
    dragRef.current = null; const active = activeRef.current; if (!active) return; const end = getPoint(event); const points = [...active.points, end]; const node: CanvasNode = ["pen", "brush", "eraser"].includes(active.tool) ? { id: makeId("stroke"), name: active.tool, kind: "stroke", tool: active.tool, points, color, size, opacity, visible: true, locked: false } : { id: makeId("shape"), name: active.tool, kind: "shape", tool: active.tool, start: active.start, end, color, size, opacity, visible: true, locked: false }; activeRef.current = null; commitNodes([...nodesRef.current, node]);
  }

  function updateNode(id: string, patch: Partial<CanvasNode>) { const next = nodesRef.current.map((node) => node.id === id && !node.locked ? { ...node, ...patch } : node); nodesRef.current = next; setNodes(next); }
  function deleteSelected() { if (!selectedIds.length) return; commitNodes(nodesRef.current.filter((node) => !selectedIds.includes(node.id))); setSelectedIds([]); }
  function duplicateSelected() { const copies = selectedNodes().map((node) => ({ ...node, id: makeId("copy"), name: `${node.name} 복사본`, x: (node.x || 0) + 24, y: (node.y || 0) + 24, locked: false })); if (!copies.length) return; commitNodes([...nodesRef.current, ...copies]); setSelectedIds(copies.map((node) => node.id)); }
  function groupSelected() { if (selectedIds.length < 2) return; const group = makeId("group"); commitNodes(nodesRef.current.map((node) => selectedIds.includes(node.id) ? { ...node, group } : node)); onToast("선택한 요소를 그룹화했습니다"); }
  function ungroupSelected() { if (!selectedIds.length) return; commitNodes(nodesRef.current.map((node) => selectedIds.includes(node.id) ? { ...node, group: undefined } : node)); onToast("그룹을 해제했습니다"); }
  function reorderSelected(direction: -1 | 1) { const next = [...nodesRef.current]; const index = next.findIndex((node) => selectedIds.includes(node.id)); const target = index + direction; if (index < 0 || target < 0 || target >= next.length) return; [next[index], next[target]] = [next[target], next[index]]; commitNodes(next); }

  function importAsset(event: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files || []); if (!files.length) return; let remaining = files.length; const added: AssetRecord[] = [];
    files.forEach((file, index) => { const reader = new FileReader(); reader.onload = () => { const src = String(reader.result); const asset: AssetRecord = { id: makeId("asset"), name: index === 0 && assetName ? assetName : file.name, type: "image", src, tags: ["사용자", "가져온 이미지"], favorite: false, createdAt: new Date().toISOString() }; added.push(asset); const node: CanvasNode = { id: makeId("image"), name: asset.name, kind: "image", src, x: 110 + index * 30, y: 110 + index * 24, width: 520, height: 330, rotation: 0, color, size, opacity, visible: true, locked: false }; commitNodes([...nodesRef.current, node]); remaining -= 1; if (!remaining) { const next = [...added, ...assets].slice(0, 80); setAssets(next); window.localStorage.setItem(`${CUSTOM_REGISTRY_KEY}/assets`, JSON.stringify(next)); onToast(`${files.length}개 에셋을 가져왔습니다`); } }; reader.readAsDataURL(file); }); event.target.value = "";
  }

  function saveDraft() { const savedAt = new Date().toISOString(); setDraftSavedAt(savedAt); window.localStorage.setItem(`${CUSTOM_REGISTRY_KEY}/draft`, JSON.stringify({ nodes: nodesRef.current, background, savedAt })); onToast("초안이 저장되었습니다"); }
  function saveRevision(source: RevisionRecord["source"] = "manual") { const revision: RevisionRecord = { id: makeId("revision"), label: revisionLabel || "UI 변경", createdAt: new Date().toISOString(), nodes: nodesRef.current, background, source, validation: "통과" }; const next = [revision, ...revisions].slice(0, 24); setRevisions(next); window.localStorage.setItem(`${CUSTOM_REGISTRY_KEY}/revisions`, JSON.stringify(next)); setDraftSavedAt(revision.createdAt); onToast(`리비전 ${next.length}이 생성되었습니다`); }
  function rollbackRevision(revision: RevisionRecord) { commitNodes(revision.nodes); setBackground(revision.background); saveRevision("rollback"); onToast("선택한 리비전을 복원했습니다"); }
  function emergencyRestore() { const production = revisions.find((revision) => revision.source === "applied" || revision.source === "manual"); if (production) rollbackRevision(production); else onToast("복원할 정상 리비전이 없습니다"); }
  function applyTemplate(template: "main" | "dashboard" | "workspace" | "minimal") { const title: Record<string, string> = { main: "Ultra Brain 메인", dashboard: "대시보드", workspace: "Workspace", minimal: "Minimal" }; const templateNodes: CanvasNode[] = [{ id: makeId("template"), name: "제목", kind: "text", text: title[template], x: 420, y: 150, color, size: 10, opacity: 1, visible: true, locked: false }, { id: makeId("template"), name: "주요 카드", kind: "component", component: template === "workspace" ? "Workspace Entry" : "Card", x: 320, y: 260, width: 320, height: 110, color, size: 8, opacity: 1, visible: true, locked: false }, { id: makeId("template"), name: "탐색 버튼", kind: "component", component: "Navigation Button", x: 700, y: 260, width: 220, height: 64, color, size: 8, opacity: 1, visible: true, locked: false }]; commitNodes(templateNodes); setSelectedIds(templateNodes.map((node) => node.id)); onToast(`${title[template]} 템플릿을 적용했습니다`); }
  function createCustomTheme() { const canvas = canvasRef.current; if (!canvas) return; const preview = canvas.toDataURL("image/png"); const item: UserCustomTheme = { id: makeId("custom"), name: customName || "My Custom World", baseTheme, preview, createdAt: new Date().toISOString(), status: "draft" }; const next = [item, ...customThemes].slice(0, 12); setCustomThemes(next); window.localStorage.setItem(CUSTOM_REGISTRY_KEY, JSON.stringify(next)); const drawingAsset: AssetRecord = { id: makeId("drawing"), name: item.name, type: "drawing", src: preview, tags: ["사용자", "드로잉", "배경"], favorite: false, createdAt: item.createdAt }; const nextAssets = [drawingAsset, ...assets].slice(0, 80); setAssets(nextAssets); window.localStorage.setItem(`${CUSTOM_REGISTRY_KEY}/assets`, JSON.stringify(nextAssets)); onUseTheme(preview, item.name); onToast("사용자 UI와 드로잉 에셋을 저장했습니다"); }

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) { const command = event.ctrlKey || event.metaKey; if (!command) return; if (event.key.toLowerCase() === "z") { event.preventDefault(); event.shiftKey ? redo() : undo(); } if (event.key.toLowerCase() === "y") { event.preventDefault(); redo(); } if (event.key.toLowerCase() === "c") copyRef.current = selectedNodes(); if (event.key.toLowerCase() === "v" && copyRef.current.length) { event.preventDefault(); const copies = copyRef.current.map((node) => ({ ...node, id: makeId("paste"), x: (node.x || 0) + 24, y: (node.y || 0) + 24, locked: false })); commitNodes([...nodesRef.current, ...copies]); setSelectedIds(copies.map((node) => node.id)); } if (event.key === "Delete" || event.key === "Backspace") { if (selectedIds.length) { event.preventDefault(); deleteSelected(); } } }
    window.addEventListener("keydown", onKeyDown); return () => window.removeEventListener("keydown", onKeyDown);
  }, [selectedIds, history, redoStack]);

  const selectedNode = nodes.find((node) => selectedIds.includes(node.id));
  const filteredAssets = assets.filter((asset) => `${asset.name} ${asset.tags.join(" ")}`.toLowerCase().includes(assetSearch.toLowerCase()));
  const tools: { id: Tool; label: string }[] = [{ id: "select", label: "선택" }, { id: "pen", label: "펜" }, { id: "brush", label: "브러시" }, { id: "eraser", label: "지우개" }, { id: "line", label: "직선" }, { id: "rectangle", label: "사각형" }, { id: "circle", label: "원" }, { id: "triangle", label: "삼각형" }, { id: "text", label: "텍스트" }, { id: "fill", label: "채우기" }, { id: "gradient", label: "그라디언트" }];
  const shellStyle = { "--canvas-zoom": zoom } as React.CSSProperties;

  return <div className={`canvas-editor preview-${previewMode} builder-${builderMode}`} style={shellStyle}>
    <div className="canvas-editor-header"><div><small>UI BUILDER · {draftSavedAt ? `저장 ${new Date(draftSavedAt).toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" })}` : "초안 없음"}</small><h3>UI Builder</h3><p>실제 화면을 만들고, 구성 요소와 에셋을 재사용하며, 저장 전 미리 확인할 수 있습니다.</p></div><div className="canvas-header-actions"><div className="canvas-mode-row"><button type="button" className={builderMode === "builder" ? "is-selected" : ""} onClick={() => setBuilderMode("builder")}>Builder</button><button type="button" className={builderMode === "drawing" ? "is-selected" : ""} onClick={() => setBuilderMode("drawing")}>Drawing 보조</button>{(["desktop", "tablet", "mobile", "full"] as const).map((mode) => <button key={mode} type="button" className={previewMode === mode ? "is-selected" : ""} onClick={() => setPreviewMode(mode)}>{mode === "desktop" ? "데스크톱" : mode === "tablet" ? "태블릿" : mode === "mobile" ? "모바일" : "전체 화면"}</button>)}</div><div className="canvas-value-row"><button type="button" onClick={undo} disabled={!history.length}>실행 취소</button><button type="button" onClick={redo} disabled={!redoStack.length}>다시 실행</button><button type="button" onClick={saveDraft}>초안 저장</button><button type="button" className="canvas-primary-action" onClick={() => saveRevision("applied")}>적용 리비전 저장</button></div></div></div>
    <div className="builder-workspace">
      <aside className="builder-tool-panel"><section><div className="canvas-section-heading"><strong>도구</strong><span>{builderMode === "builder" ? "UI 제작" : "Asset 제작"}</span></div><button type="button" className={builderTool === "select" ? "is-selected" : ""} onClick={() => setBuilderTool("select")}>선택 / 이동</button>{COMPONENTS.map((item) => <button key={item.id} type="button" className={builderTool === item.id ? "is-selected" : ""} onClick={() => { setBuilderMode("builder"); setBuilderTool(item.id); }}>{item.label}</button>)}<button type="button" onClick={() => { setBuilderMode("drawing"); setTool("pen"); }}>Drawing</button></section><section><div className="canvas-section-heading"><strong>템플릿</strong><span>복제 후 수정</span></div>{(["main", "dashboard", "workspace", "minimal"] as const).map((template) => <button key={template} type="button" onClick={() => applyTemplate(template)}>{template === "main" ? "Ultra Brain 메인" : template === "dashboard" ? "대시보드" : template === "workspace" ? "Workspace" : "Minimal"}</button>)}</section><section><div className="canvas-section-heading"><strong>그룹</strong><span>{selectedIds.length}개 선택</span></div><button type="button" onClick={groupSelected} disabled={selectedIds.length < 2}>그룹화</button><button type="button" onClick={ungroupSelected} disabled={!selectedIds.length}>그룹 해제</button><button type="button" onClick={duplicateSelected} disabled={!selectedIds.length}>복제</button><button type="button" onClick={deleteSelected} disabled={!selectedIds.length}>삭제</button></section></aside>
      <div className="builder-canvas-column"><div className="canvas-toolbar">{builderMode === "drawing" && <div className="canvas-tool-row">{tools.map((item) => <button key={item.id} type="button" className={tool === item.id ? "is-selected" : ""} onClick={() => setTool(item.id)}>{item.label}</button>)}</div>}<div className="canvas-value-row"><label>색상 <input type="color" value={color} onChange={(event) => setColor(event.target.value)} /></label><label>크기 <input type="range" min="1" max="60" value={size} onChange={(event) => setSize(Number(event.target.value))} /><output>{size}</output></label><label>투명도 <input type="range" min="0.1" max="1" step="0.05" value={opacity} onChange={(event) => setOpacity(Number(event.target.value))} /><output>{Math.round(opacity * 100)}%</output></label><label>배경 <input type="color" value={background.startsWith("#") ? background : "#061011"} onChange={(event) => setBackground(event.target.value)} /></label><button type="button" className={grid ? "is-selected" : ""} onClick={() => setGrid((current) => !current)}>그리드</button><button type="button" className={snap ? "is-selected" : ""} onClick={() => setSnap((current) => !current)}>스냅</button><button type="button" className={safeArea ? "is-selected" : ""} onClick={() => setSafeArea((current) => !current)}>안전 영역</button><label className="zoom-control">확대 <input type="range" min="0.5" max="1.4" step="0.1" value={zoom} onChange={(event) => setZoom(Number(event.target.value))} /><output>{Math.round(zoom * 100)}%</output></label></div></div><div className="canvas-stage"><canvas ref={canvasRef} width={CANVAS_WIDTH} height={CANVAS_HEIGHT} style={{ transform: `scale(${zoom})` }} onPointerDown={handlePointerDown} onPointerMove={handlePointerMove} onPointerUp={finishPointer} onPointerCancel={() => { activeRef.current = null; dragRef.current = null; }} aria-label="UI Builder Canvas" /></div></div>
      <aside className="builder-property-panel"><section><div className="canvas-section-heading"><strong>속성</strong><span>{selectedIds.length ? `${selectedIds.length}개 선택` : "선택 없음"}</span></div>{selectedNode ? <><label>이름<input className="canvas-text-input" value={selectedNode.name} onChange={(event) => updateNode(selectedNode.id, { name: event.target.value })} /></label><div className="property-grid"><label>X<input type="number" value={Math.round(selectedNode.x || 0)} onChange={(event) => updateNode(selectedNode.id, { x: Number(event.target.value) })} /></label><label>Y<input type="number" value={Math.round(selectedNode.y || 0)} onChange={(event) => updateNode(selectedNode.id, { y: Number(event.target.value) })} /></label><label>너비<input type="number" value={Math.round(selectedNode.width || 240)} onChange={(event) => updateNode(selectedNode.id, { width: Number(event.target.value) })} /></label><label>높이<input type="number" value={Math.round(selectedNode.height || 66)} onChange={(event) => updateNode(selectedNode.id, { height: Number(event.target.value) })} /></label></div><label>회전<input type="range" min="-180" max="180" value={Math.round(selectedNode.rotation || 0)} onChange={(event) => updateNode(selectedNode.id, { rotation: Number(event.target.value) })} /></label><label>투명도<input type="range" min="0.1" max="1" step="0.05" value={selectedNode.opacity} onChange={(event) => updateNode(selectedNode.id, { opacity: Number(event.target.value) })} /></label><button type="button" className={selectedNode.locked ? "is-selected" : ""} onClick={() => updateNode(selectedNode.id, { locked: !selectedNode.locked })}>{selectedNode.locked ? "잠금 해제" : "잠금"}</button></> : <p className="field-hint">Canvas에서 요소를 선택하면 위치·크기·스타일을 편집할 수 있습니다.</p>}</section><section><div className="canvas-section-heading"><strong>Component 상태</strong><span>실시간 미리보기</span></div><div className="canvas-option-row">{COMPONENT_STATES.map((state) => <button key={state} type="button" className={componentState === state ? "is-selected" : ""} onClick={() => setComponentState(state)}>{state}</button>)}</div></section><section><div className="canvas-section-heading"><strong>Asset Library</strong><label className="canvas-import"><input type="file" multiple accept="image/png,image/jpeg,image/webp,image/svg+xml,image/gif" onChange={importAsset} /><span>가져오기</span></label></div><input className="canvas-text-input" value={assetSearch} onChange={(event) => setAssetSearch(event.target.value)} placeholder="에셋 검색" aria-label="에셋 검색" /><div className="asset-library-list">{filteredAssets.slice(0, 12).map((asset) => <button key={asset.id} type="button" onClick={() => asset.src && commitNodes([...nodesRef.current, { id: makeId("asset-node"), name: asset.name, kind: "image", src: asset.src, x: 180, y: 150, width: 420, height: 260, color, size, opacity, visible: true, locked: false }])}>{asset.src && <img src={asset.src} alt="" />}<span>{asset.name}</span><small>{asset.tags.join(" · ")}</small></button>)}</div></section></aside>
    </div>
    <div className="builder-bottom-panels"><section><div className="canvas-section-heading"><strong>Layer / Component Tree</strong><span>{nodes.length}개</span></div><div className="canvas-layer-list">{nodes.slice().reverse().map((node) => <div key={node.id} className={`canvas-layer ${selectedIds.includes(node.id) ? "is-selected" : ""}`}><button type="button" onClick={() => setSelectedIds([node.id])}>{node.name}</button><button type="button" onClick={() => updateNode(node.id, { visible: !node.visible })}>{node.visible ? "표시" : "숨김"}</button><button type="button" onClick={() => updateNode(node.id, { locked: !node.locked })}>{node.locked ? "잠금" : "해제"}</button></div>)}</div><div className="canvas-layer-actions"><button type="button" onClick={() => reorderSelected(1)}>뒤로</button><button type="button" onClick={() => reorderSelected(-1)}>앞으로</button></div></section><section><div className="canvas-section-heading"><strong>Revision History</strong><span>{revisions.length}개</span></div><input className="canvas-text-input" value={revisionLabel} onChange={(event) => setRevisionLabel(event.target.value)} aria-label="리비전 이름" placeholder="리비전 이름" /><div className="revision-list">{revisions.slice(0, 8).map((revision) => <button key={revision.id} type="button" onClick={() => rollbackRevision(revision)}><strong>{revision.label}</strong><small>{new Date(revision.createdAt).toLocaleString("ko-KR")} · {revision.source} · 검증 {revision.validation}</small></button>)}</div><button type="button" onClick={emergencyRestore} disabled={!revisions.length}>마지막 정상 리비전 복원</button></section><section><div className="canvas-section-heading"><strong>사용자 UI</strong><span>{baseTheme}</span></div><input className="canvas-text-input" value={customName} onChange={(event) => setCustomName(event.target.value)} aria-label="사용자 UI 이름" /><button className="canvas-primary-action" type="button" onClick={createCustomTheme}>사용자 UI 저장</button><div className="custom-theme-list">{customThemes.map((item) => <button type="button" key={item.id} onClick={() => onUseTheme(item.preview, item.name)}><img src={item.preview} alt="" /><span>{item.name}</span><small>{item.baseTheme}</small></button>)}</div></section></div>
  </div>;
}
